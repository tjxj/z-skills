#!/usr/bin/env python3
import hashlib
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image
import yaml

from book_common import ManuscriptError, file_sha256
from markdown_inline import plain_inline

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$")
IMAGE = re.compile(r"^!\[([^\]]*)\]\((\S+?)(?:\s+['\"].*['\"])?\)$")
TABLE_SEPARATOR = re.compile(r"^:?-{3,}:?$")


def json_safe(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value


def front_matter(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    metadata = {}
    start = 0
    if lines and lines[0].strip() == "---":
        end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
        if end is None:
            raise ManuscriptError("YAML front matter 未闭合")
        metadata = json_safe(yaml.safe_load("\n".join(lines[1:end])) or {})
        if not isinstance(metadata, dict):
            raise ManuscriptError("YAML front matter 必须是对象")
        start = end + 1
    while start < len(lines) and not lines[start].strip():
        start += 1
    return metadata, [(index + 1, line) for index, line in enumerate(lines) if index >= start]


def table_cells(line):
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    if r"\|" in value:
        raise ManuscriptError("暂不支持表格单元格中的转义竖线")
    return [cell.strip() for cell in value.split("|")]


def is_table_separator(line):
    cells = table_cells(line)
    return bool(cells) and all(TABLE_SEPARATOR.fullmatch(cell.replace(" ", "")) for cell in cells)


def plain_blocks(blocks):
    paragraphs = []
    for block in blocks:
        kind = block["type"]
        if kind in {"paragraph", "heading", "quote"}:
            paragraphs.append(plain_inline(block["text"]))
        elif kind == "list":
            paragraphs.extend(plain_inline(item) for item in block["items"])
        elif kind == "image":
            paragraphs.append(block["caption"])
        elif kind == "code":
            paragraphs.extend(block["text"].splitlines() or [""])
        elif kind == "table":
            paragraphs.extend(block["headers"])
            paragraphs.extend(cell for row in block["rows"] for cell in row)
    return [x for x in paragraphs if x.strip()]


def parse_markdown(path):
    metadata, lines = front_matter(path)
    if not lines:
        raise ManuscriptError("Markdown 正文为空")
    works = []
    current = {"title": "开篇", "type": "导语", "line_start": lines[0][0], "blocks": []}

    def finish(line_end):
        if not current["blocks"]:
            return
        current["line_end"] = line_end
        current["paragraphs"] = plain_blocks(current["blocks"])
        if not current["paragraphs"]:
            raise ManuscriptError(f"章节 {current['title']} 没有可排版的文字")
        works.append(current)

    index = 0
    while index < len(lines):
        line_number, line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code_lines = []
            start = line_number
            index += 1
            while index < len(lines) and not lines[index][1].strip().startswith("```"):
                code_lines.append(lines[index][1])
                index += 1
            if index >= len(lines):
                raise ManuscriptError(f"第 {start} 行代码块未闭合")
            if any(x.strip() == r"\end{PoetryCode}" for x in code_lines):
                raise ManuscriptError(f"第 {start} 行代码块包含保留环境控制行")
            current["blocks"].append({"type": "code", "language": language, "text": "\n".join(code_lines), "line_start": start, "line_end": lines[index][0]})
            index += 1
            continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            title = plain_inline(heading.group(2))
            if level <= 3:
                finish(line_number - 1)
                current = {"title": title, "type": "技术文章", "line_start": line_number, "blocks": []}
            else:
                current["blocks"].append({"type": "heading", "level": level, "text": title, "line_start": line_number, "line_end": line_number})
            index += 1
            continue
        image = IMAGE.match(stripped)
        if image:
            alt, url = image.groups()
            current["blocks"].append({"type": "image", "url": url, "alt": alt, "caption": alt or f"图 {sum(x['type'] == 'image' for w in works + [current] for x in w['blocks']) + 1}　原文配图", "line_start": line_number, "line_end": line_number})
            index += 1
            continue
        item = LIST_ITEM.match(line)
        if item:
            if item.group(1):
                raise ManuscriptError(f"第 {line_number} 行：暂不支持嵌套列表")
            ordered = item.group(2)[0].isdigit()
            items = []
            start = line_number
            while index < len(lines):
                match = LIST_ITEM.match(lines[index][1])
                if not match or match.group(1) or match.group(2)[0].isdigit() != ordered:
                    break
                items.append(match.group(3))
                index += 1
            current["blocks"].append({"type": "list", "ordered": ordered, "items": items, "line_start": start, "line_end": lines[index - 1][0]})
            continue
        if "|" in line and index + 1 < len(lines) and is_table_separator(lines[index + 1][1]):
            headers = table_cells(line)
            separator = table_cells(lines[index + 1][1])
            if len(headers) != len(separator) or not headers:
                raise ManuscriptError(f"第 {line_number} 行表格表头无效")
            start = line_number
            index += 2
            rows = []
            while index < len(lines) and lines[index][1].strip() and "|" in lines[index][1]:
                row = table_cells(lines[index][1])
                if len(row) != len(headers):
                    raise ManuscriptError(f"第 {lines[index][0]} 行表格列数不一致")
                rows.append(row)
                index += 1
            current["blocks"].append({"type": "table", "headers": headers, "rows": rows, "line_start": start, "line_end": lines[index - 1][0]})
            continue
        if stripped.startswith(">"):
            start = line_number
            quoted = []
            while index < len(lines) and lines[index][1].strip().startswith(">"):
                quoted.append(lines[index][1].strip()[1:].lstrip())
                index += 1
            current["blocks"].append({"type": "quote", "text": " ".join(quoted), "line_start": start, "line_end": lines[index - 1][0]})
            continue
        if stripped.startswith("<") or stripped.startswith("$$"):
            raise ManuscriptError(f"第 {line_number} 行包含暂不支持的 HTML 或数学公式")
        if re.fullmatch(r"[-*_]\s*[-*_]\s*[-*_][-*_\s]*", stripped):
            current["blocks"].append({"type": "rule", "line_start": line_number, "line_end": line_number})
        else:
            current["blocks"].append({"type": "paragraph", "text": line, "line_start": line_number, "line_end": line_number})
        index += 1
    finish(lines[-1][0])
    if not works:
        raise ManuscriptError("没有可排版的文章内容")
    for position, work in enumerate(works):
        work["id"] = f"A{position + 1:03d}"
        if position and work["line_start"] < works[position - 1]["line_end"]:
            raise ManuscriptError("文章行号覆盖异常")
    return metadata, works


def inspect_image(path):
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.format not in {"PNG", "JPEG"} or min(image.size) < 1:
            raise ManuscriptError(f"不支持的图片格式：{path}")
        return image.format, image.size


def materialize_images(source, works, assets_dir, offline=False):
    assets_dir = Path(assets_dir).resolve()
    images_dir = assets_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = assets_dir / "source-manifest.json"
    previous = {}
    if manifest_path.is_file():
        import json
        previous = {x["url"]: x for x in json.loads(manifest_path.read_text(encoding="utf-8")).get("images", [])}
    records = []
    for work in works:
        for block in work["blocks"]:
            if block["type"] != "image":
                continue
            url = block["url"]
            number = len(records) + 1
            cached = previous.get(url)
            target = images_dir / Path(cached["path"]).name if cached else None
            if target and target.is_file():
                if file_sha256(target) != cached["sha256"]:
                    raise ManuscriptError(f"缓存图片校验失败：{target}")
            else:
                if offline:
                    raise ManuscriptError(f"离线模式缺少图片：{url}")
                if urlparse(url).scheme == "https":
                    request = Request(url, headers={"User-Agent": "PoetryBook/1.1 local-document-typesetting"})
                    with urlopen(request, timeout=30) as response:
                        if urlparse(response.geturl()).scheme != "https":
                            raise ManuscriptError("图片重定向到了非 HTTPS 地址")
                        data = response.read(25 * 1024 * 1024 + 1)
                    if len(data) > 25 * 1024 * 1024:
                        raise ManuscriptError(f"图片超过 25MB：{url}")
                elif urlparse(url).scheme in {"http", "https"}:
                    raise ManuscriptError("网络图片只允许 HTTPS 地址")
                else:
                    local = (Path(source).resolve().parent / url).resolve()
                    if not local.is_file():
                        raise ManuscriptError(f"本地图片不存在：{local}")
                    data = local.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                target = images_dir / f"image-{number:02d}-{digest[:12]}.tmp"
                target.write_bytes(data)
            try:
                image_format, size = inspect_image(target)
            except Exception as exc:
                target.unlink(missing_ok=True)
                raise ManuscriptError(f"图片校验失败 {url}：{exc}") from exc
            if target.suffix == ".tmp":
                final = target.with_suffix(".png" if image_format == "PNG" else ".jpg")
                target.replace(final)
                target = final
            record = {
                "url": url,
                "path": f"images/{target.name}",
                "sha256": file_sha256(target),
                "bytes": target.stat().st_size,
                "width": size[0],
                "height": size[1],
                "format": image_format,
            }
            block.update({"path": record["path"], "source_path": str(target), "source": url if url.startswith("https://") else ""})
            records.append(record)
    return records


def article_links(works):
    pattern = re.compile(r"(?<!!)\[[^\]]+\]\((https?://[^)]+)\)")
    links = []
    for work in works:
        for block in work["blocks"]:
            values = []
            if block["type"] in {"paragraph", "heading", "quote"}:
                values = [block["text"]]
            elif block["type"] == "list":
                values = block["items"]
            elif block["type"] == "table":
                values = block["headers"] + [cell for row in block["rows"] for cell in row]
            for value in values:
                links.extend(pattern.findall(value))
    return links
