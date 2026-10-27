#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

from book_common import (
    ManuscriptError,
    SKILL_HOME,
    TeXCodec,
    file_sha256,
    iter_works,
    load_json,
    normalized_metadata,
    safe_filename,
    validate_manuscript,
)
from build_style import build_style
from article_render import article_expectations, prepare_images, render_blocks

BOOK_TEX = r"""\expandafter\def\csname ltj@stdmcfont\endcsname{name:LXGWWenKai-Regular}
\expandafter\def\csname ltj@stdgtfont\endcsname{name:LXGWWenKai-Regular}
\documentclass[11pt,openany]{ltjsbook}
\input{style.tex}
\begin{document}
\CoverPage
\input{frontmatter-content.tex}
\tableofcontents
\clearpage
\input{contents.tex}
\end{document}
"""


def check_environment():
    missing = [command for command in ["latexmk", "lualatex", "gs"] if not shutil.which(command)]
    missing.extend(name for name in ["fontTools", "fitz", "PIL"] if importlib.util.find_spec(name) is None)
    if missing:
        raise ManuscriptError("缺少运行依赖：" + ", ".join(missing) + "。请先安装并授权所需依赖。")


def render_work(work, codec, article=False):
    date = work["date"]
    start_macro = "\\ArticleWorkStart" if article else "\\WorkStart"
    lines = [
        f"{start_macro}{{{work['id']}}}{{{codec.tex(work['title'])}}}{{{codec.tex(date['label'] + '　' + work['type'] + '　' + work['id'])}}}"
    ]
    if work.get("blocks"):
        lines.extend(render_blocks(work["blocks"], codec))
    else:
        for paragraph in work["paragraphs"]:
            lines.append(f"\\WorkLine{{{codec.tex(paragraph)}}}")
    if work.get("intro"):
        lines.append(f"\\WorkGloss{{题解　{codec.tex(work['intro'])}}}")
    if work.get("gloss"):
        lines.append(f"\\WorkGloss{{{codec.tex('；'.join(work['gloss']))}}}")
    if work.get("comment"):
        lines.append(f"\\WorkNote{{{codec.tex(work['comment'])}}}")
    if article:
        source = f"原文：{'；'.join(work['sources'])}。"
    else:
        source = f"系年依据：{date['evidence']}。底本：{'；'.join(work['sources'])}。"
    lines.append(f"\\WorkSource{{{codec.tex(source)}}}")
    lines.append("\\WorkEnd")
    return "\n".join(lines)


def render_group(group, codec, article=False):
    output = [f"\\BookChapter{{{codec.tex(group['title'])}}}{{{codec.tex(group.get('years', ''))}}}{{{codec.tex(group.get('intro', ''))}}}"]
    previous_label = object()
    for work in group["works"]:
        if not article and work["date"]["label"] != previous_label:
            output.append(f"\\YearHeading{{{codec.tex(work['date']['label'])}}}")
            previous_label = work["date"]["label"]
        output.append(render_work(work, codec, article))
    return output


def render_manuscript(payload, codec):
    output = []
    article = payload.get("document_type") == "article"
    for chapter in payload.get("chapters", []):
        output.extend(render_group(chapter, codec, article))
    if payload.get("appendix"):
        output.extend(render_group(payload["appendix"], codec, article))
    for section in payload.get("backmatter", []):
        output.append(f"\\FrontHeading{{{codec.tex(section['heading'])}}}")
        output.extend(codec.tex(paragraph) + "\\par" for paragraph in section["paragraphs"])
    if payload.get("index", True):
        output.append("\\FrontHeading{篇名索引}")
        for work in sorted(iter_works(payload), key=lambda x: (x.get("index_title", x["title"]), x["id"])):
            output.append(f"\\IndexEntry{{{codec.tex(work.get('index_title', work['title']))}}}{{{work['id']}}}")
    return "\n".join(output) + "\n"


def validation_expectations(payload, metadata):
    works = list(iter_works(payload))
    golden = {}
    for work in works[:7]:
        golden[work["id"]] = work["paragraphs"][0][:32]
    return {
        "pdf_title": metadata["pdf_title"],
        "golden": golden,
        "chapter_titles": [x["title"] for x in payload.get("chapters", [])] + ([payload["appendix"]["title"]] if payload.get("appendix") else []),
        "longest_title_id": max(works, key=lambda x: len(x["title"]))["id"],
        "longest_text_id": max(works, key=lambda x: sum(len(x) for x in x["paragraphs"]))["id"],
        **article_expectations(payload),
    }


def compile_pdf(build_dir):
    result = subprocess.run(
        ["latexmk", "-lualatex", "-interaction=nonstopmode", "-halt-on-error", "book.tex"],
        cwd=build_dir,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if result.returncode:
        detail = (result.stdout + "\n" + result.stderr)[-6000:]
        raise ManuscriptError(f"LuaLaTeX 编译失败；完整日志见 {build_dir / 'book.log'}\n{detail}")


def render(args):
    check_environment()
    source = Path(args.input).expanduser().resolve()
    if not source.is_file():
        raise ManuscriptError(f"书稿不存在：{source}")
    output = Path(args.output).expanduser().resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ManuscriptError(f"输出目录必须为空或不存在，以免覆盖资料：{output}")
    payload = load_json(source)
    quality = validate_manuscript(payload)
    metadata = normalized_metadata(payload)
    output.mkdir(parents=True, exist_ok=True)
    build_dir = output / "build"
    build_dir.mkdir()
    prepare_images(payload, source.parent, build_dir)
    codec = TeXCodec()
    frontmatter = []
    for section in payload.get("frontmatter", []):
        frontmatter.append(f"\\FrontHeading{{{codec.tex(section['heading'])}}}")
        frontmatter.extend(codec.tex(paragraph) + "\\par" for paragraph in section["paragraphs"])
    (build_dir / "frontmatter-content.tex").write_text("\n".join(frontmatter) + "\n", encoding="utf-8")
    (build_dir / "contents.tex").write_text(render_manuscript(payload, codec), encoding="utf-8")
    (build_dir / "book.tex").write_text(BOOK_TEX, encoding="utf-8")
    works = list(iter_works(payload))
    manifest = {
        "sample": False,
        "theme": args.theme,
        "input_sha256": file_sha256(source),
        "works": [{"id": x["id"], "title": x["title"], "sha256": hashlib.sha256("\n".join(x["paragraphs"]).encode("utf-8")).hexdigest()} for x in works],
        "selected_ids": sorted(x["id"] for x in works),
        "validation": validation_expectations(payload, metadata),
        "quality": quality,
    }
    (build_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (build_dir / "font-usage.json").write_text(json.dumps(codec.usage_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    style_args = argparse.Namespace(
        config=str(SKILL_HOME / "assets" / "themes.json"),
        assets=str(SKILL_HOME / "assets"),
        font_dir=str(SKILL_HOME / "assets" / "fonts"),
        theme=args.theme,
        output=str(build_dir / "style.tex"),
        **{key: metadata[key] for key in ["title", "subtitle", "author", "series", "edition", "seal", "subject", "keywords"]},
    )
    build_style(style_args)
    compile_pdf(build_dir)
    filename = safe_filename(metadata["pdf_title"]) + ".pdf"
    pdf_path = output / filename
    shutil.copyfile(build_dir / "book.pdf", pdf_path)
    shutil.copyfile(build_dir / "book.works", output / "book.works")
    shutil.copyfile(build_dir / "manifest.json", output / "manifest.json")
    shutil.copyfile(build_dir / "font-usage.json", output / "font-usage.json")
    validator = Path(__file__).resolve().with_name("validate_pdf.py")
    result = subprocess.run(
        [sys.executable, str(validator), str(pdf_path), "--build-dir", str(build_dir), "--report", str(output / "validation-report.json"), "--render-dir", str(output / "preview")],
        cwd=output.parent,
    )
    if result.returncode:
        raise ManuscriptError(f"PDF 已生成但未通过验收：{output / 'validation-report.json'}")
    report = json.loads((output / "validation-report.json").read_text(encoding="utf-8"))
    return {
        "passed": True,
        "theme": args.theme,
        "pdf": str(pdf_path),
        "pages": report["pages"],
        "works": report["works"],
        "checks": len(report["checks"]),
        "report": str(output / "validation-report.json"),
        "warnings": quality["warnings"],
    }


def main():
    parser = argparse.ArgumentParser(description="从规范化 JSON 生成 Poetry Book PDF 并完整验收")
    parser.add_argument("--input", required=True, help="规范化书稿 JSON")
    parser.add_argument("--theme", default="song-mist")
    parser.add_argument("--output", required=True, help="新的或空的输出目录")
    args = parser.parse_args()
    try:
        print(json.dumps(render(args), ensure_ascii=False))
    except (OSError, ManuscriptError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Poetry Book 构建失败：{exc}\n")


if __name__ == "__main__":
    main()
