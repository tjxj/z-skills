#!/usr/bin/env python3
"""版式体检：静态检查 + 真实浏览器排版检查。

用法：python check_deck.py <index.html 或 slides.html> [--no-browser] [--strict] [--json]

浏览器检查会在 1920x1080 画布上逐页测量：文字/图片越界、贴边、字号过小、
内容溢出、文字与标注重叠、标注压图、页面中间空洞、末行孤字、单页字数、缺讲稿。
有错误时退出码为 1；--strict 时警告也算失败。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _chrome import file_url, find_chrome, run_chrome  # noqa: E402


def static_checks(text: str) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    # 内嵌的模板样式与运行时不参与作者内容检查
    text = re.sub(r"<(style|script)\b[^>]*\bid\s*=\s*[\"']wh-[^\"']*[\"'][^>]*>.*?</\1>", "", text, flags=re.S | re.I)
    slides = re.findall(r"<section\b([^>]*\bclass\s*=\s*[\"'][^\"']*\bslide\b[^>]*)>", text, re.I)
    if not slides:
        errors.append('没有找到 <section class="slide">')
    if not re.search(r"<main\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bdeck\b", text, re.I):
        errors.append('没有找到 <main class="deck">')
    notes = len(re.findall(r"<(?:aside|div)\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bnotes\b", text, re.I))
    if slides and notes < len(slides):
        warnings.append(f"{len(slides)} 页只有 {notes} 段讲稿")
    for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", text):
        if float(m.group(1)) < 20:
            warnings.append(f"样式里出现 {m.group(1)}px 字号，投影上看不清")
            break
    if re.search(r"<(?:img|script|link)\b[^>]*(?:src|href)\s*=\s*[\"']https?://", text, re.I):
        warnings.append("仍有网络外链资源，离线或换电脑时可能缺图")
    return errors, warnings, len(slides)


def browser_audit(html: Path, chrome: str) -> dict:
    proc = run_chrome(chrome, file_url(html, "audit"), ["--dump-dom"], budget_ms=20000, timeout=180, capture=True)
    dom = proc.stdout.decode("utf-8", "replace")
    m = re.search(r'<script id="wh-audit" type="application/json">(.*?)</script>', dom, re.S)
    if not m:
        raise RuntimeError("浏览器检查没有返回结果（运行时未执行完）")
    return json.loads(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path)
    ap.add_argument("--no-browser", action="store_true", help="只做静态检查")
    ap.add_argument("--strict", action="store_true", help="警告也视为失败")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--chrome", help="Chrome / Edge 可执行文件路径")
    args = ap.parse_args()

    path = args.html.expanduser().resolve()
    if not path.is_file():
        print(f"error: 找不到 {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    errors, warnings, count = static_checks(text)
    report: dict = {"file": str(path), "slides": count, "errors": errors, "warnings": warnings, "pages": []}

    if not errors and not args.no_browser:
        chrome = find_chrome(args.chrome)
        if not chrome:
            warnings.append("未找到 Chrome / Edge，跳过浏览器排版检查（可用 --chrome 或环境变量 WH_CHROME 指定）")
        else:
            target = path
            tmp = None
            if 'id="wh-runtime"' not in text:
                from build import build  # 源稿：先构建到临时目录再检查
                tmp = tempfile.TemporaryDirectory(prefix="wh-check-")
                target = build(path, Path(tmp.name), timeline=False, quiet=True)[0]
            try:
                audit = browser_audit(target, chrome)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"浏览器检查失败：{exc}")
                audit = None
            finally:
                if tmp:
                    tmp.cleanup()
            if audit:
                if not audit.get("font", {}).get("whHand"):
                    warnings.append("手写字体没有加载，画面会退回楷体（请用 build.py 重新构建）")
                if audit.get("font", {}).get("missing"):
                    warnings.append(f"手写字体缺字（已用楷体补位）：{audit['font']['missing'][:40]}")
                report["pages"] = audit["slides"]

    page_err = sum(len(p["errors"]) for p in report["pages"])
    page_warn = sum(len(p["warnings"]) for p in report["pages"])
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print(f"error: {e}")
        for w in warnings:
            print(f"warn:  {w}")
        for p in report["pages"]:
            for e in p["errors"]:
                print(f"error: 第 {p['index']} 页「{p['title'][:16]}」{e}")
            for w in p["warnings"]:
                print(f"warn:  第 {p['index']} 页「{p['title'][:16]}」{w}")
        total_e = len(errors) + page_err
        total_w = len(warnings) + page_warn
        verdict = "ok" if total_e == 0 and not (args.strict and total_w) else "fail"
        print(f"{verdict}: {count} 页，{total_e} 个错误，{total_w} 个警告")
    failed = errors or page_err or (args.strict and (warnings or page_warn))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
