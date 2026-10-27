#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import shutil

from book_common import ManuscriptError, file_sha256, validate_manuscript
from markdown_article import article_links, materialize_images, parse_markdown
from render_book import render


def default_title(source, metadata):
    candidate = metadata.get("title")
    if isinstance(candidate, str) and candidate.strip() and candidate.strip() != ".md":
        return candidate.strip()
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", Path(source).stem)


def default_author(metadata):
    author = metadata.get("author", "佚名")
    if isinstance(author, list):
        return str(author[0]) if author else "佚名"
    return str(author)


def prepare(args):
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        raise ManuscriptError(f"Markdown 不存在：{source}")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ManuscriptError(f"输出目录必须为空或不存在：{output}")
    original_metadata, works = parse_markdown(source)
    metadata = {
        "title": args.title or default_title(source, original_metadata),
        "subtitle": args.subtitle,
        "author": args.author or default_author(original_metadata),
        "series": args.series,
        "edition": args.edition,
        "seal": args.seal,
        "subject": args.subject or "技术文章专题排版",
        "keywords": ["技术文章", "图文排版", "横排"],
    }
    date_label = args.date or str(original_metadata.get("date") or "发布日期未详")
    match = re.match(r"^(\d{4})", date_label)
    year = int(match.group(1)) if match else None
    for work in works:
        work["date"] = {
            "start": year,
            "end": year,
            "label": date_label,
            "evidence": "原稿 YAML 或命令行提供的发布日期；不等同于独立事实核验",
        }
        work["sources"] = [f"{metadata['author']}原稿，{date_label}，第{work['line_start']}–{work['line_end']}行"]
    assets_dir = Path(args.assets_dir).expanduser().resolve() if args.assets_dir else output.parent / f"{output.name}-assets"
    images = materialize_images(source, works, assets_dir, offline=args.offline)
    payload = {
        "document_type": "article",
        "metadata": metadata,
        "frontmatter": [
            {"heading": "排版说明", "paragraphs": [
                f"本册为{metadata['author']}原文的技术图文排版样张，保留原有论述顺序、标题、列表、链接与配图。",
                "原始稿件和图片另存来源清单。技术数据、性能比较与趋势判断均以原文为准，本次工作不冒充独立事实核验。",
            ]}
        ],
        "chapters": [{
            "id": "article",
            "title": metadata["title"],
            "years": metadata["subtitle"],
            "intro": f"{metadata['author']}原文 · 技术图文排版",
            "works": works,
        }],
        "backmatter": [
            {"heading": "原文与图片出处", "paragraphs": [
                "原稿、原始图片地址、文件尺寸与 SHA-256 校验值见随附 source-manifest.json。",
                "本册仅进行结构解析与版式转换；复杂 Markdown 扩展和原文未提供的补充资料不在本次收录范围内。",
            ]}
        ],
        "links": article_links(works),
        "validation": {"required_phrases": args.require},
        "index": False,
    }
    validate_manuscript(payload)
    saved_source = assets_dir / "source.md"
    if saved_source.resolve() != source:
        shutil.copyfile(source, saved_source)
    if file_sha256(saved_source) != file_sha256(source):
        raise ManuscriptError("保存的原稿与输入文件校验值不一致")
    manifest = {
        "original_markdown": str(source),
        "source_sha256": file_sha256(source),
        "original_metadata": original_metadata,
        "effective_metadata": metadata,
        "date_label": date_label,
        "images": images,
    }
    (assets_dir / "book.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (assets_dir / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return assets_dir / "book.json", len(images)


def main():
    parser = argparse.ArgumentParser(description="将 Markdown 技术文章制作成图文 PDF")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--assets-dir")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--theme", default="song-mist")
    parser.add_argument("--title")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--author")
    parser.add_argument("--series", default="技术专题")
    parser.add_argument("--edition", default="技术文章·图文笺注本")
    parser.add_argument("--seal", default="阅")
    parser.add_argument("--subject")
    parser.add_argument("--date")
    parser.add_argument("--require", action="append", default=[])
    args = parser.parse_args()
    try:
        book_json, images = prepare(args)
        result = render(argparse.Namespace(input=str(book_json), output=args.output, theme=args.theme))
        result["images"] = images
        result["assets"] = str(Path(args.assets_dir).expanduser().resolve()) if args.assets_dir else str(Path(args.output).expanduser().resolve().parent / f"{Path(args.output).name}-assets")
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ManuscriptError) as exc:
        parser.exit(1, f"技术文章构建失败：{exc}\n")


if __name__ == "__main__":
    main()
