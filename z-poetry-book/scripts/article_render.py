#!/usr/bin/env python3
from pathlib import Path
import shutil
import unicodedata
from urllib.parse import urlparse

from PIL import Image

from book_common import ManuscriptError, iter_works
from markdown_inline import tex_inline, tex_url


def article_expectations(payload):
    if payload.get("document_type") != "article":
        return {}
    result = {"markdown_artifacts": True}
    images = sum(1 for work in iter_works(payload) for block in work.get("blocks", []) if block["type"] == "image")
    if images:
        result["expected_images"] = images
    if payload.get("links"):
        result["expected_links"] = len(payload["links"])
    required = payload.get("validation", {}).get("required_phrases", [])
    if required:
        result["required_phrases"] = required
    return result


def prepare_images(payload, source_dir, build_dir):
    for work in iter_works(payload):
        for block in work.get("blocks", []):
            if block["type"] != "image":
                continue
            source = Path(block.get("source_path") or source_dir / block["path"]).expanduser().resolve()
            if not source.is_file():
                raise ManuscriptError(f"图片不存在：{source}")
            try:
                with Image.open(source) as image:
                    image.verify()
            except Exception as exc:
                raise ManuscriptError(f"图片无法读取：{source}：{exc}") from exc
            relative = Path(block["path"])
            target = (build_dir / relative).resolve()
            if build_dir.resolve() not in target.parents:
                raise ManuscriptError(f"图片输出路径越界：{relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


def wrap_code(text, width=88):
    wrapped = []
    for original in text.expandtabs(4).splitlines():
        line = ""
        size = 0
        for char in original:
            char_width = 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
            if line and size + char_width > width:
                wrapped.append(line)
                line = "  " + char
                size = 2 + char_width
            else:
                line += char
                size += char_width
        wrapped.append(line)
    return "\n".join(wrapped)


def render_blocks(blocks, codec):
    output = []
    for block in blocks:
        kind = block["type"]
        if kind == "paragraph":
            output.append(f"\\WorkLine{{{tex_inline(codec, block['text'])}}}")
        elif kind == "heading":
            output.append(f"\\ArticleHeading{{{block['level']}}}{{{tex_inline(codec, block['text'])}}}")
        elif kind == "list":
            environment = "enumerate" if block["ordered"] else "itemize"
            output.append("\\begin{" + environment + "}\\setlength{\\itemsep}{2pt}\\setlength{\\topsep}{3pt}")
            output.extend(f"\\item {tex_inline(codec, item)}" for item in block["items"])
            output.append("\\end{" + environment + "}")
        elif kind == "image":
            source = ""
            if urlparse(block.get("source", "")).scheme in {"http", "https"}:
                source = "{\\scriptsize\\color{faded}\\url{" + tex_url(block["source"]) + "}}"
            output.append(f"\\ArticleImage{{{codec.tex(block['path'])}}}{{{tex_inline(codec, block['caption'])}}}{{{source}}}")
        elif kind == "quote":
            output.append(f"\\ArticleQuote{{{tex_inline(codec, block['text'])}}}")
        elif kind == "code":
            if block.get("language"):
                output.append(f"\\CodeHeading{{{codec.tex(block['language'])}}}")
            output.append("\\begin{PoetryCode}\n" + wrap_code(block["text"]) + "\n\\end{PoetryCode}")
        elif kind == "table":
            headers = block["headers"]
            columns = "*{" + str(len(headers)) + "}{>{\\raggedright\\arraybackslash}X}"
            output.append("\\begin{center}\\scriptsize\\begin{tabularx}{\\linewidth}{@{}" + columns + "@{}}\\toprule")
            output.append(" & ".join(tex_inline(codec, cell) for cell in headers) + " \\\\ \\midrule")
            for row in block["rows"]:
                output.append(" & ".join(tex_inline(codec, cell) for cell in row) + " \\\\")
            output.append("\\bottomrule\\end{tabularx}\\end{center}")
        elif kind == "rule":
            output.append("\\ArticleRule")
    return output
