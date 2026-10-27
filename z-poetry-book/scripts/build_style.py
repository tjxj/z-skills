#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys

from book_common import ManuscriptError, SKILL_HOME, TeXCodec, load_json

THEME_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_themes(config_path):
    path = Path(config_path).resolve()
    payload = load_json(path)
    themes = payload.get("themes")
    if not isinstance(themes, list) or not themes:
        raise ManuscriptError("主题配置必须包含非空 themes 数组")
    seen = set()
    for theme in themes:
        theme_id = theme.get("id") if isinstance(theme, dict) else None
        if not isinstance(theme_id, str) or not THEME_ID.fullmatch(theme_id) or theme_id in seen:
            raise ManuscriptError(f"无效或重复的主题 ID：{theme_id}")
        for field in ["name", "description", "file"]:
            if not isinstance(theme.get(field), str) or not theme[field]:
                raise ManuscriptError(f"主题 {theme_id} 缺少 {field}")
        relative = Path(theme["file"])
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".tex":
            raise ManuscriptError(f"主题 {theme_id} 的文件路径不安全")
        seen.add(theme_id)
    if payload.get("default") not in seen:
        raise ManuscriptError("默认主题不在 themes 数组中")
    return payload, path.parent


def build_style(args):
    payload, config_dir = load_themes(args.config)
    assets = Path(args.assets).resolve()
    theme_id = args.theme or payload["default"]
    theme = next((x for x in payload["themes"] if x["id"] == theme_id), None)
    if theme is None:
        raise ManuscriptError(f"未知主题 {theme_id}；可用：{', '.join(x['id'] for x in payload['themes'])}")
    base_path = assets / "style-base.tex"
    theme_path = assets / theme["file"]
    for path in [base_path, theme_path]:
        if not path.is_file():
            raise ManuscriptError(f"主题资源不存在：{path}")
    font_dir = Path(args.font_dir).expanduser().resolve()
    if any(char in str(font_dir) for char in "\n\r{}%#"):
        raise ManuscriptError("字体路径包含 LaTeX 不支持的字符")
    codec = TeXCodec(font_dir)
    metadata = {
        "title": args.title,
        "subtitle": args.subtitle,
        "author": args.author,
        "series": args.series,
        "edition": args.edition,
        "seal": args.seal,
    }
    for key, value in metadata.items():
        if not isinstance(value, str) or "\x00" in value:
            raise ManuscriptError(f"元数据 {key} 无效")
    pdf_title = args.title + ("——" + args.subtitle if args.subtitle else "")
    replacements = {
        "%FONT_DIR%": "{" + font_dir.as_posix().rstrip("/") + "/}",
        "%THEME_DEFINITIONS%": theme_path.read_text(encoding="utf-8"),
        "%PDF_TITLE%": codec.tex(pdf_title),
        "%PDF_AUTHOR%": codec.tex(args.author + " 著；" + args.edition),
        "%PDF_SUBJECT%": codec.tex(args.subject),
        "%PDF_KEYWORDS%": codec.tex(args.keywords),
        "%BOOK_TITLE%": codec.tex(args.title),
        "%BOOK_SUBTITLE%": codec.tex(args.subtitle),
        "%BOOK_AUTHOR%": codec.tex(args.author),
        "%BOOK_SERIES%": codec.tex(args.series),
        "%BOOK_EDITION%": codec.tex(args.edition),
        "%BOOK_SEAL%": codec.tex(args.seal),
    }
    style = base_path.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        if marker not in style:
            raise ManuscriptError(f"共享样式缺少占位符 {marker}")
        style = style.replace(marker, value)
    if re.search(r"%[A-Z_]+%", style):
        raise ManuscriptError("共享样式仍有未替换的占位符")
    output = Path(args.output).expanduser().resolve()
    if output.is_dir():
        raise ManuscriptError(f"输出路径是目录：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(style, encoding="utf-8")
    return {"theme": theme_id, "name": theme["name"], "output": str(output), "font_dir": str(font_dir), "config_dir": str(config_dir)}


def main():
    parser = argparse.ArgumentParser(description="生成 Poetry Book 主题 LaTeX 样式")
    parser.add_argument("--config", default=str(SKILL_HOME / "assets" / "themes.json"))
    parser.add_argument("--assets", default=str(SKILL_HOME / "assets"))
    parser.add_argument("--font-dir", default=str(SKILL_HOME / "assets" / "fonts"))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--theme")
    parser.add_argument("--output", default="style.tex")
    parser.add_argument("--title", default="未命名诗传")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--author", default="佚名")
    parser.add_argument("--series", default="编年诗传")
    parser.add_argument("--edition", default="编年笺注本")
    parser.add_argument("--seal", default="诗")
    parser.add_argument("--subject", default="诗词编年")
    parser.add_argument("--keywords", default="诗词,编年,横排")
    args = parser.parse_args()
    try:
        if args.list:
            payload, _ = load_themes(args.config)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        print(json.dumps(build_style(args), ensure_ascii=False))
    except (OSError, ManuscriptError) as exc:
        parser.exit(1, f"Poetry Book 样式生成失败：{exc}\n")


if __name__ == "__main__":
    main()
