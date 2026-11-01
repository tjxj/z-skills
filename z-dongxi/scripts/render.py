#!/usr/bin/env python3
"""渲染动态 SVG。

用法：
  python3 render.py --spec demo.json --out rag.svg [--style sketch] [--png rag.png]
  python3 render.py --spec demo.json --insert-to 文章.md --heading "### RAG 怎么跑"
  python3 render.py --list
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dongxi import LAYOUTS, STYLES, render  # noqa: E402


def insert_md(md_path, svg, heading=None):
    p = pathlib.Path(md_path)
    text = p.read_text(encoding="utf-8")
    block = "\n" + svg + "\n"
    if heading and heading in text:
        i = text.index(heading)
        j = text.find("\n\n", i + len(heading))
        j = text.find("\n\n", j + 2) if j != -1 else -1
        pos = j if j != -1 else len(text)
    else:
        m = re.search(r"\n\n", text)
        pos = m.end() - 1 if m else len(text)
    p.write_text(text[:pos] + "\n" + block + text[pos:], encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec")
    ap.add_argument("--spec-json")
    ap.add_argument("--style", help="风格名或 auto")
    ap.add_argument("--out")
    ap.add_argument("--png", help="同时导出静态终态 PNG")
    ap.add_argument("--insert-to")
    ap.add_argument("--heading")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("图型：", " ".join(LAYOUTS))
        for k, v in STYLES.items():
            print(f"  {k:<10}{v['cn']:<6} {v['note']}")
        return
    spec = json.loads(a.spec_json) if a.spec_json else json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    svg, name, T = render(spec, a.style)
    out = a.out or (pathlib.Path(a.spec).with_suffix(".svg") if a.spec else "dongxi.svg")
    pathlib.Path(out).write_text(svg, encoding="utf-8")
    print(f"✓ {out}  图型={spec['type']} 风格={name} 周期={T:.1f}s 大小={len(svg.encode()) / 1024:.1f}KB")
    if a.png:
        subprocess.run(["rsvg-convert", "-w", "750", "-o", a.png, str(out)], check=True)
        print(f"✓ {a.png}")
    if a.insert_to:
        insert_md(a.insert_to, svg, a.heading)
        print(f"✓ 已插入 {a.insert_to}")


if __name__ == "__main__":
    main()
