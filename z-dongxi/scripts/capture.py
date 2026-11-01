#!/usr/bin/env python3
"""把动态 SVG 定格成帧：看动画是否按剧本走，或导出 MP4 / GIF 发小红书、视频号。

用法：
  python3 capture.py rag.svg --sheet sheet.png          # 均匀取 8 帧拼成联系表
  python3 capture.py rag.svg --mp4 rag.mp4 --fps 30     # 录一个完整周期
  python3 capture.py rag.svg --gif rag.gif --fps 12
依赖：playwright（chromium）、Pillow、ffmpeg
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import tempfile

from playwright.sync_api import sync_playwright


def period(svg):
    m = re.search(r'dur="([\d.]+)s"[^>]*repeatCount="indefinite"', svg)
    durs = [float(x) for x in re.findall(r'dur="([\d.]+)s"', svg)]
    return max(durs) if durs else (float(m.group(1)) if m else 6.0)


def frames(svg_path, times, outdir, scale=1):
    svg = pathlib.Path(svg_path).read_text(encoding="utf-8")
    html = f"<html><body style='margin:0;background:#fff'>{svg.replace('width=\"100%\"', 'width=\"750\"')}</body></html>"
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 750, "height": 1000}, device_scale_factor=scale)
        pg.set_content(html)
        pg.evaluate("document.querySelector('svg').pauseAnimations()")
        for i, t in enumerate(times):
            pg.evaluate(f"document.querySelector('svg').setCurrentTime({t})")
            pg.wait_for_timeout(15)
            f = pathlib.Path(outdir) / f"f{i:05d}.png"
            pg.screenshot(path=str(f), clip={"x": 0, "y": 0, "width": 750, "height": 1000})
            out.append(f)
        b.close()
    return out


def sheet(fs, times, out, cols=4):
    from PIL import Image, ImageDraw
    w, h = 375, 500
    rows = (len(fs) + cols - 1) // cols
    img = Image.new("RGB", (cols * (w + 12) + 12, rows * (h + 40) + 12), "#DDDDDD")
    d = ImageDraw.Draw(img)
    for i, (f, t) in enumerate(zip(fs, times)):
        x, y = 12 + (i % cols) * (w + 12), 12 + (i // cols) * (h + 40)
        d.rectangle([x, y, x + w, y + 26], fill="#111111")
        d.text((x + 8, y + 7), f"t = {t:.1f}s", fill="#FFFFFF")
        img.paste(Image.open(f).convert("RGB").resize((w, h)), (x, y + 28))
    img.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--sheet")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--mp4")
    ap.add_argument("--gif")
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    T = period(pathlib.Path(a.svg).read_text(encoding="utf-8"))
    tmp = tempfile.mkdtemp()
    if a.sheet:
        times = [T * (i + .5) / a.n * .94 for i in range(a.n)]
        fs = frames(a.svg, times, tmp)
        sheet(fs, times, a.sheet)
        print(f"✓ {a.sheet}  周期 {T:.1f}s")
    if a.mp4 or a.gif:
        k = int(T * a.fps)
        frames(a.svg, [i / a.fps for i in range(k)], tmp, scale=2 if a.mp4 else 1)
        if a.mp4:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", f"{tmp}/f%05d.png",
                            "-vf", "scale=1080:1440:flags=lanczos", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", a.mp4], check=True)
            print(f"✓ {a.mp4}")
        if a.gif:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", f"{tmp}/f%05d.png",
                            "-vf", "scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer",
                            a.gif], check=True)
            print(f"✓ {a.gif}")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
