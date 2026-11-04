#!/usr/bin/env python3
"""导出 PNG / 总览图 / PDF（macOS、Windows、Linux 通用，需要 Chrome 或 Edge）。

用法：
  python render.py index.html                 # png/01.png… + contact-sheet.png
  python render.py index.html --pdf           # 另外导出 deck.pdf
  python render.py index.html --slides 1,3-5 --scale 2
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _chrome import file_url, find_chrome, png_size, run_chrome  # noqa: E402


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    bad = [p for p in pages if p < 1 or p > total]
    if bad:
        raise SystemExit(f"页码超出范围 1-{total}：{bad}")
    return sorted(pages)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path, help="build.py 生成的 index.html")
    ap.add_argument("--out", type=Path, help="PNG 输出目录，默认 <html 所在目录>/png")
    ap.add_argument("--slides", help="只导出部分页，例如 1,3-5")
    ap.add_argument("--scale", type=float, default=1, help="像素倍率，2 = 3840x2160")
    ap.add_argument("--jobs", type=int, default=min(6, os.cpu_count() or 2))
    ap.add_argument("--no-sheet", action="store_true", help="不生成 contact-sheet.png")
    ap.add_argument("--pdf", action="store_true", help="同时导出 deck.pdf")
    ap.add_argument("--chrome", help="Chrome / Edge 路径")
    args = ap.parse_args()

    html = args.html.expanduser().resolve()
    if not html.is_file():
        raise SystemExit(f"找不到 {html}")
    text = html.read_text(encoding="utf-8")
    if 'id="wh-runtime"' not in text:
        raise SystemExit("这是源稿，请先运行 build.py 生成 index.html 再导出")
    total = len(re.findall(r"<section\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bslide\b", text, re.I))
    chrome = find_chrome(args.chrome)
    if not chrome:
        raise SystemExit("找不到 Chrome / Edge；用 --chrome 或环境变量 WH_CHROME 指定路径")
    out = (args.out or html.parent / "png").expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    pages = parse_pages(args.slides, total)
    width = round(1920 * args.scale)
    height = round(1080 * args.scale)
    digits = max(2, len(str(total)))

    def shoot(n: int) -> tuple[int, str | None]:
        target = out / f"{n:0{digits}d}.png"
        target.unlink(missing_ok=True)
        proc = run_chrome(chrome, file_url(html, "export", f"/{n}"), [f"--screenshot={target}"], scale=args.scale)
        size = png_size(target)
        if size != (width, height):
            err = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] if proc.stderr else []
            return n, f"尺寸 {size}，应为 {width}x{height} {' '.join(err)}"
        return n, None

    failures = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for n, err in pool.map(shoot, pages):
            if err:
                failures.append(f"第 {n} 页：{err}")
    print(f"PNG：{len(pages) - len(failures)}/{len(pages)} 页 → {out}")

    if not args.no_sheet:
        rows = math.ceil(total / 4)
        sw, sh = 4 * 480 + 5 * 24, rows * 270 + (rows + 1) * 24
        sheet = html.parent / "contact-sheet.png"
        sheet.unlink(missing_ok=True)
        run_chrome(chrome, file_url(html, "sheet"), [f"--screenshot={sheet}"], width=sw, height=sh)
        if png_size(sheet):
            print(f"总览图：{sheet}")
        else:
            failures.append("总览图导出失败")

    if args.pdf:
        pdf = html.parent / "deck.pdf"
        pdf.unlink(missing_ok=True)
        run_chrome(chrome, file_url(html, "export"), [f"--print-to-pdf={pdf}", "--no-pdf-header-footer"], budget_ms=20000, timeout=240)
        if pdf.is_file() and pdf.stat().st_size > 1000:
            print(f"PDF：{pdf}")
        else:
            failures.append("PDF 导出失败")

    for f in failures:
        print(f"error: {f}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
