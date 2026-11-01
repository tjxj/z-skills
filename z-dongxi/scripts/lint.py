#!/usr/bin/env python3
"""公众号可用性 + 反模板检查。

Floor（硬门槛，不过就不能发）：
  viewBox 必须是五种画幅之一（3:4 750x1000 / 9:16 750x1334 / 1:1 900x900 / 4:3 1200x900 / 16:9 1280x720）；不能有 id= / <script> / <style> / @keyframes / foreignObject / url(# / href="#
  不能有空行和换行；不能出现全角句号 。；不能出现「老章工程手记」；字号不小于 13；体积不超过 120KB；至少一个动画
Reflex（提醒）：
  字号小于 15 的文字太多；动画周期超过 20 秒；同一张图超过 4 种强调色；文字跑出画布
用法：python3 lint.py a.svg [b.svg ...]   或   python3 lint.py 文章.md（检查其中所有内联 SVG）
"""
import pathlib
import re
import sys

SIZES = {(750, 1000), (750, 1334), (900, 900), (1200, 900), (1280, 720)}

FLOOR = [
    (r"\sid=", "出现 id 属性，公众号会剥掉"),
    (r"<script", "出现 <script>"),
    (r"<style", "出现 <style>"),
    (r"@keyframes", "出现 CSS 动画"),
    (r"foreignObject", "出现 foreignObject"),
    (r"url\(#", "引用了 url(#…)"),
    (r'href="#', "引用了 href=#"),
    (r"<defs", "出现 <defs>"),
    (r"。", "出现全角句号"),
    (r"老章工程手记", "出现「老章工程手记」"),
]


def check(svg, name):
    errs, warns = [], []
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    W, H = (int(vb.group(1)), int(vb.group(2))) if vb else (0, 0)
    if (W, H) not in SIZES:
        errs.append(f"viewBox {W}x{H} 不在支持的画幅里")
    if "\n" in svg.strip():
        errs.append("SVG 内有换行，粘到公众号会断")
    for pat, msg in FLOOR:
        if re.search(pat, svg):
            errs.append(msg)
    sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', svg)]
    if sizes and min(sizes) < 13:
        errs.append(f"最小字号 {min(sizes)} < 13，手机上看不清")
    small = sum(1 for x in sizes if x < 15)
    if small > 16:
        warns.append(f"{small} 处字号小于 15，信息可能塞太多")
    kb = len(svg.encode()) / 1024
    if kb > 120:
        errs.append(f"体积 {kb:.0f}KB > 120KB")
    elif kb > 80:
        warns.append(f"体积 {kb:.0f}KB，偏大")
    if not re.search(r"<animate|<set ", svg):
        errs.append("没有任何动画")
    durs = [float(x) for x in re.findall(r'dur="([\d.]+)s"', svg)]
    if durs and max(durs) > 20:
        warns.append(f"周期 {max(durs):.0f}s，读者等不到结尾")
    for x, y in re.findall(r'<text x="(-?[\d.]+)" y="(-?[\d.]+)"', svg):
        if not (0 <= float(x) <= W and 0 <= float(y) <= H):
            warns.append(f"文字锚点 ({x},{y}) 在画布外")
            break
    print(("✗ " if errs else "✓ ") + f"{name}  {kb:.1f}KB  周期 {max(durs) if durs else 0:.1f}s")
    for e in errs:
        print("   [Floor] " + e)
    for w in warns:
        print("   [Reflex] " + w)
    return not errs


def main():
    ok = True
    for f in sys.argv[1:]:
        text = pathlib.Path(f).read_text(encoding="utf-8")
        if f.endswith(".md"):
            for i, svg in enumerate(re.findall(r"<svg.*?</svg>", text, re.S)):
                ok &= check(svg, f"{f} #{i + 1}")
        else:
            ok &= check(text, f)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
