#!/usr/bin/env python3
"""把长 SVG 在指定时刻定格，切成一屏一张 PNG，再拼一张总览图，方便逐屏检查。

    python3 preview.py out.svg -o preview/            # 默认定格在第 4 秒
    python3 preview.py out.svg -o preview/ -t 1,4,8   # 多个时刻，各出一套
    python3 preview.py out.svg -o preview/ --screens 3,7 --scale 2

依赖 playwright（pip install playwright && python3 -m playwright install chromium）。
"""
import argparse
import os
import re

from playwright.sync_api import sync_playwright

PAGE = ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#fff}'
        'svg{display:block}</style></head><body>%s</body></html>')


def svg_size(svg):
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    return (float(m.group(1)), float(m.group(2))) if m else (750.0, 1000.0)


def render(svg_path, out_dir, times=(4.0,), screens=None, scale=1.0, sheet=True, screen_h=1000):
    svg = open(svg_path, encoding='utf-8').read()
    if svg_path.endswith('.md'):
        m = re.search(r'<svg.*?</svg>', svg, re.S)
        svg = m.group(0)
    vw, vh = svg_size(svg)
    css_w = 750
    css_h = vh * css_w / vw
    os.makedirs(out_dir, exist_ok=True)
    n = max(1, int(round(css_h / screen_h))) if abs(vw - 750) < 1 else 1
    outs = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={'width': css_w, 'height': 1000}, device_scale_factor=scale)
        pg.set_content(PAGE % svg, wait_until='load')
        pg.evaluate('document.fonts.ready.then(()=>1)')
        pg.evaluate('document.querySelector("svg").pauseAnimations()')
        for t in times:
            pg.evaluate(f'document.querySelector("svg").setCurrentTime({t})')
            tag = f't{t:g}'.replace('.', '_')
            shots = []
            idx = range(n) if not screens else [i for i in screens if i < n]
            for i in idx:
                h = screen_h if n > 1 else css_h
                path = os.path.join(out_dir, f'{tag}_s{i:02d}.png')
                pg.screenshot(path=path, clip={'x': 0, 'y': i * screen_h, 'width': css_w, 'height': h}, full_page=True)
                shots.append(path)
            outs += shots
            if sheet and len(shots) > 1:
                outs.append(contact_sheet(shots, os.path.join(out_dir, f'{tag}_sheet.jpg')))
        br.close()
    return outs


def contact_sheet(paths, out, cols=6, thumb_w=300):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert('RGB') for p in paths]
    tw = thumb_w
    th = int(ims[0].size[1] * tw / ims[0].size[0])
    rows = (len(ims) + cols - 1) // cols
    pad = 12
    sheet = Image.new('RGB', (cols * (tw + pad) + pad, rows * (th + pad) + pad), '#D9D4CA')
    d = ImageDraw.Draw(sheet)
    for k, im in enumerate(ims):
        c, r = k % cols, k // cols
        x, y = pad + c * (tw + pad), pad + r * (th + pad)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline='#B5AE9F')
    sheet.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('svg', help='.svg 文件，或含内联 SVG 的 .md（取第一张）')
    ap.add_argument('-o', '--out', default='preview')
    ap.add_argument('-t', '--times', default='4', help='逗号分隔的秒数')
    ap.add_argument('--screens', help='只出这几屏，逗号分隔（从 0 数，0 是封面）')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--no-sheet', action='store_true')
    a = ap.parse_args()
    times = [float(x) for x in a.times.split(',') if x]
    screens = [int(x) for x in a.screens.split(',')] if a.screens else None
    for p in render(a.svg, a.out, times, screens, a.scale, not a.no_sheet):
        print(p)


if __name__ == '__main__':
    main()
