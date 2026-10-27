#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from fontTools.ttLib import TTCollection, TTFont

SKILL_HOME = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
METADATA_DEFAULTS = {
    "subtitle": "",
    "series": "编年诗传",
    "edition": "编年笺注本",
    "seal": "诗",
    "subject": "诗词编年",
    "keywords": "诗词,编年,横排",
}


class ManuscriptError(ValueError):
    pass


def text_field(value, label, allow_empty=False):
    if not isinstance(value, str) or "\x00" in value or (not allow_empty and not value.strip()):
        raise ManuscriptError(f"{label} 必须是非空文本" if not allow_empty else f"{label} 必须是文本")
    return value


def list_field(value, label):
    if not isinstance(value, list):
        raise ManuscriptError(f"{label} 必须是数组")
    return value


def normalized_metadata(payload):
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ManuscriptError("缺少 metadata 对象")
    result = dict(METADATA_DEFAULTS)
    result.update(metadata)
    for key in ["title", "author", "subtitle", "series", "edition", "seal", "subject"]:
        text_field(result.get(key), f"metadata.{key}", allow_empty=key == "subtitle")
    keywords = result["keywords"]
    if isinstance(keywords, list):
        keywords = ",".join(text_field(x, "metadata.keywords 项") for x in keywords)
    result["keywords"] = text_field(keywords, "metadata.keywords")
    result["pdf_title"] = result["title"] + ("——" + result["subtitle"] if result["subtitle"] else "")
    return result


def normalized_sections(payload, key):
    sections = list_field(payload.get(key, []), key)
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ManuscriptError(f"{key}[{section_index}] 必须是对象")
        text_field(section.get("heading"), f"{key}[{section_index}].heading")
        paragraphs = list_field(section.get("paragraphs"), f"{key}[{section_index}].paragraphs")
        if not paragraphs:
            raise ManuscriptError(f"{key}[{section_index}].paragraphs 不能为空")
        for index, paragraph in enumerate(paragraphs):
            text_field(paragraph, f"{key}[{section_index}].paragraphs[{index}]")
    return sections


def iter_works(payload):
    for chapter in payload.get("chapters", []):
        yield from chapter["works"]
    appendix = payload.get("appendix")
    if appendix:
        yield from appendix["works"]


def validate_blocks(work, where):
    if "blocks" not in work:
        return
    blocks = list_field(work["blocks"], f"{where}.blocks")
    if not blocks:
        raise ManuscriptError(f"{where}.blocks 不能为空")
    for index, block in enumerate(blocks):
        label = f"{where}.blocks[{index}]"
        if not isinstance(block, dict) or not isinstance(block.get("type"), str):
            raise ManuscriptError(f"{label} 必须包含块类型")
        kind = block["type"]
        if kind in {"paragraph", "quote"}:
            text_field(block.get("text"), f"{label}.text")
        elif kind == "heading":
            text_field(block.get("text"), f"{label}.text")
            if isinstance(block.get("level"), bool) or not isinstance(block.get("level"), int) or not 1 <= block["level"] <= 6:
                raise ManuscriptError(f"{label}.level 必须在 1–6 之间")
        elif kind == "list":
            if not isinstance(block.get("ordered"), bool):
                raise ManuscriptError(f"{label}.ordered 必须是布尔值")
            items = list_field(block.get("items"), f"{label}.items")
            if not items:
                raise ManuscriptError(f"{label}.items 不能为空")
            for item_index, item in enumerate(items):
                text_field(item, f"{label}.items[{item_index}]")
        elif kind == "image":
            text_field(block.get("caption"), f"{label}.caption")
            text_field(block.get("path"), f"{label}.path")
            text_field(block.get("source", ""), f"{label}.source", allow_empty=True)
            path = Path(block["path"])
            if path.is_absolute() or ".." in path.parts or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                raise ManuscriptError(f"{label}.path 不是安全的图片相对路径")
            text_field(block.get("source_path", ""), f"{label}.source_path", allow_empty=True)
        elif kind == "code":
            text_field(block.get("text"), f"{label}.text", allow_empty=True)
            text_field(block.get("language", ""), f"{label}.language", allow_empty=True)
            if any(line.strip() == r"\end{PoetryCode}" for line in block["text"].splitlines()):
                raise ManuscriptError(f"{label}.text 包含保留环境控制行")
        elif kind == "table":
            headers = list_field(block.get("headers"), f"{label}.headers")
            rows = list_field(block.get("rows"), f"{label}.rows")
            if not headers:
                raise ManuscriptError(f"{label}.headers 不能为空")
            for cell_index, cell in enumerate(headers):
                text_field(cell, f"{label}.headers[{cell_index}]")
            for row_index, row in enumerate(rows):
                cells = list_field(row, f"{label}.rows[{row_index}]")
                if len(cells) != len(headers):
                    raise ManuscriptError(f"{label}.rows[{row_index}] 列数不一致")
                for cell_index, cell in enumerate(cells):
                    text_field(cell, f"{label}.rows[{row_index}][{cell_index}]", allow_empty=True)
        elif kind != "rule":
            raise ManuscriptError(f"{label}.type 暂不支持：{kind}")


def validate_manuscript(payload):
    if not isinstance(payload, dict):
        raise ManuscriptError("书稿根节点必须是 JSON 对象")
    if payload.get("document_type", "book") not in {"book", "article"}:
        raise ManuscriptError("document_type 只能是 book 或 article")
    normalized_metadata(payload)
    normalized_sections(payload, "frontmatter")
    normalized_sections(payload, "backmatter")
    if not isinstance(payload.get("index", True), bool):
        raise ManuscriptError("index 必须是布尔值")
    chapters = list_field(payload.get("chapters", []), "chapters")
    groups = list(chapters)
    appendix = payload.get("appendix")
    if appendix is not None:
        if not isinstance(appendix, dict):
            raise ManuscriptError("appendix 必须是对象")
        groups.append(appendix)
    if not groups:
        raise ManuscriptError("至少需要一个 chapters 章节或 appendix")
    seen_ids = set()
    seen_chapters = set()
    warnings = []
    seen_text = {}
    for group_index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ManuscriptError(f"章节 {group_index} 必须是对象")
        text_field(group.get("title"), f"章节 {group_index}.title")
        text_field(group.get("years", ""), f"章节 {group_index}.years", allow_empty=True)
        text_field(group.get("intro", ""), f"章节 {group_index}.intro", allow_empty=True)
        if group_index < len(chapters):
            chapter_id = group.get("id")
            if not isinstance(chapter_id, str) or not ID_PATTERN.fullmatch(chapter_id):
                raise ManuscriptError(f"章节 {group_index}.id 只能使用字母、数字、点、下划线或连字符")
            if chapter_id in seen_chapters:
                raise ManuscriptError(f"章节 ID 重复：{chapter_id}")
            seen_chapters.add(chapter_id)
        works = list_field(group.get("works"), f"章节 {group_index}.works")
        if not works:
            raise ManuscriptError(f"章节 {group_index}.works 不能为空")
        previous_start = None
        for work_index, work in enumerate(works):
            where = f"{group.get('id', 'appendix')}.works[{work_index}]"
            if not isinstance(work, dict):
                raise ManuscriptError(f"{where} 必须是对象")
            work_id = work.get("id")
            if not isinstance(work_id, str) or not ID_PATTERN.fullmatch(work_id):
                raise ManuscriptError(f"{where}.id 只能使用 1–64 位字母、数字、点、下划线或连字符")
            if work_id in seen_ids:
                raise ManuscriptError(f"作品 ID 重复：{work_id}")
            seen_ids.add(work_id)
            title = text_field(work.get("title"), f"{where}.title")
            text_field(work.get("type"), f"{where}.type")
            paragraphs = list_field(work.get("paragraphs"), f"{where}.paragraphs")
            if not paragraphs:
                raise ManuscriptError(f"{where}.paragraphs 不能为空")
            for paragraph_index, paragraph in enumerate(paragraphs):
                text_field(paragraph, f"{where}.paragraphs[{paragraph_index}]")
            validate_blocks(work, where)
            date = work.get("date")
            if not isinstance(date, dict):
                raise ManuscriptError(f"{where}.date 必须是对象")
            start, end = date.get("start"), date.get("end")
            for value, name in [(start, "start"), (end, "end")]:
                if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
                    raise ManuscriptError(f"{where}.date.{name} 必须是整数或 null")
            if (start is None) != (end is None):
                raise ManuscriptError(f"{where}.date.start 与 end 必须同时填写或同时为 null")
            if start is not None and start > end:
                raise ManuscriptError(f"{where}.date.start 不能晚于 end")
            if group_index < len(chapters) and payload.get("document_type") != "article":
                if start is None:
                    raise ManuscriptError(f"{where} 未提供系年；未系年作品请置于 appendix")
                if previous_start is not None and start < previous_start:
                    raise ManuscriptError(f"{where} 未按开始年份升序排列；未系年作品请置于 appendix")
                previous_start = start
            text_field(date.get("label"), f"{where}.date.label")
            text_field(date.get("evidence"), f"{where}.date.evidence")
            for key in ["intro", "comment"]:
                text_field(work.get(key, ""), f"{where}.{key}", allow_empty=True)
            gloss = list_field(work.get("gloss", []), f"{where}.gloss")
            for index, item in enumerate(gloss):
                text_field(item, f"{where}.gloss[{index}]")
            sources = list_field(work.get("sources", []), f"{where}.sources")
            if not sources:
                raise ManuscriptError(f"{where}.sources 至少需要一个可追溯来源")
            for index, source in enumerate(sources):
                text_field(source, f"{where}.sources[{index}]")
            fingerprint = "\n".join(paragraphs)
            if fingerprint in seen_text:
                warnings.append(f"正文重复，保留并复核：{seen_text[fingerprint]} / {work_id}")
            seen_text[fingerprint] = work_id
            if work.get("index_title") is not None:
                text_field(work["index_title"], f"{where}.index_title")
    return {"works": len(seen_ids), "warnings": warnings}


def font_cmap(path):
    font_path = Path(path)
    fonts = TTCollection(str(font_path)).fonts if font_path.suffix.lower() == ".ttc" else [TTFont(str(font_path))]
    return {codepoint for font in fonts for table in font["cmap"].tables for codepoint in table.cmap}


def discover_main_font():
    configured = os.environ.get("POETRY_BOOK_MAIN_FONT")
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            raise ManuscriptError(f"POETRY_BOOK_MAIN_FONT 不存在：{path}")
        return path
    executable = shutil.which("fc-match")
    if not executable:
        raise ManuscriptError("缺少 fc-match；请设置 POETRY_BOOK_MAIN_FONT 为主中文字体文件")
    result = subprocess.run([executable, "-f", "%{file}", "Source Han Serif SC VF"], capture_output=True, text=True)
    path = Path(result.stdout.strip())
    if result.returncode or not path.is_file():
        raise ManuscriptError("找不到 Source Han Serif SC VF；请安装字体或设置 POETRY_BOOK_MAIN_FONT")
    return path


class TeXCodec:
    def __init__(self, font_dir=None, main_font=None):
        self.font_dir = Path(font_dir or SKILL_HOME / "assets" / "fonts").resolve()
        self.main_cmap = font_cmap(main_font or discover_main_font())
        self.fallbacks = {}
        for family, filename in [("babeljfont", "BabelStoneHan.ttf"), ("imingjfont", "I.Ming-8.10.ttf")]:
            path = self.font_dir / filename
            if not path.is_file():
                raise ManuscriptError(f"缺少生僻字字体：{path}")
            self.fallbacks[family] = font_cmap(path)
        self.usage = {family: set() for family in self.fallbacks}

    def tex(self, value):
        replacements = {
            "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
            "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        }
        output = []
        for char in str(value):
            escaped = replacements.get(char, char)
            codepoint = ord(char)
            if codepoint not in self.main_cmap:
                family = next((name for name, cmap in self.fallbacks.items() if codepoint in cmap), None)
                if family is None:
                    raise ManuscriptError(f"已配置字体均不覆盖 {char!r} U+{codepoint:04X}")
                self.usage[family].add(char)
                escaped = "{\\" + family + " " + escaped + "}"
            output.append(escaped)
        return "".join(output)

    def usage_payload(self):
        return {family: {"characters": sorted(chars), "count": len(chars)} for family, chars in self.usage.items()}


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManuscriptError(f"无法读取 JSON {path}：{exc}") from exc


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_filename(value):
    result = re.sub(r"[/\\\x00]", "_", value).strip().strip(".")
    if not result or result in {".", ".."}:
        raise ManuscriptError("书名无法转换为安全文件名")
    return result
