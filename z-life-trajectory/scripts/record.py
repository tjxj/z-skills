#!/usr/bin/env python3
"""把 lifeline 长图录成 3:4 竖屏视频（默认 1080x1440、30fps，无声）。每屏停一会，再缓动滑到下一屏。

    python3 record.py spec.json -o life.mp4                       # 录视频
    python3 record.py spec.json --plan                            # 只打印每屏的到达时刻和停留时长
    python3 record.py spec.json -o life.mp4 --test 2,9.5,40       # 只截这几个时刻的画面，存到 life_test/
    python3 record.py spec.json -o life.mp4 --glide 1.2 --small   # 切屏快一点，再另存一份小文件

每屏静止多久按文字量和插画块估算。想手动指定，在那一屏写 "hold": 秒数（封面写在 cover 里）。
视频不带音轨，配乐、配音在剪辑软件里加。依赖：playwright、ffmpeg。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import lifeline  # noqa: E402

VISUAL_EXTRA = {'ring': 1.2, 'bars': 1.6, 'dots': 0.8, 'counter': 0.5, 'journey': 0.5, 'compare': 0.6,
                'exchange': 0.5, 'lifebar': 1.0, 'hbars': 0.8, 'bigstat': 0.4, 'team': 0.6, 'plaque': 0.4,
                'quote': 0.3, 'icons': 0.4, 'card': 0.3}
SKIP_KEYS = {'type', 'icon', 'kind', 'style', 'vehicle', 'scene', 'attach', 'marker', 'hold', 'dark'}


# ---------------------------------------------------------------- 每屏停多久
def text_weight(v):
    if isinstance(v, str):
        cjk = len(re.findall(r'[㐀-鿿]', v))
        words = len(re.findall(r'[A-Za-z0-9][A-Za-z0-9.,%$+\-]*', v))
        return cjk + 1.6 * words
    if isinstance(v, dict):
        return sum(text_weight(x) for k, x in v.items() if k not in SKIP_KEYS)
    if isinstance(v, list):
        return sum(text_weight(x) for x in v)
    return 0


def screen_holds(spec):
    """每屏希望静止的秒数（不含滑动）。"""
    cov = spec.get('cover', {})
    holds = [float(cov.get('hold', 5.0 + 0.04 * len(cov.get('stops', []))))]
    for scr in spec.get('screens', []):
        if 'hold' in scr:
            holds.append(float(scr['hold']))
            continue
        blocks = scr.get('blocks', [])
        w = text_weight({k: scr.get(k) for k in ('era', 'title', 'sub')}) + text_weight(blocks)
        extra = sum(VISUAL_EXTRA.get(b.get('type'), 0 if b.get('type') in lifeline.BLOCKS else 0.8) for b in blocks)
        holds.append(min(9.5, max(4.8, 2.4 + 0.02 * w + extra)))
    if len(holds) > 1 and 'hold' not in spec.get('screens', [{}])[-1]:
        holds[-1] += 1.8
    return holds


# ---------------------------------------------------------------- 时间表
def plan(holds, glide=1.5):
    """返回 arrive[i]（第 i 屏停稳的时刻）、leave[i]（第 i 屏开始滑向下一屏的时刻）、总时长。"""
    arrive, leave, t = [0.0], [], 0.0
    for h in holds[:-1]:
        t += h
        leave.append(t)
        t += glide
        arrive.append(t)
    return arrive, leave, t + holds[-1]


def ease(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ypos(t, arrive, leave):
    for i, lv in enumerate(leave):
        if t < lv:
            return 1000.0 * i
        if t < arrive[i + 1]:
            return 1000.0 * (i + ease((t - lv) / (arrive[i + 1] - lv)))
    return 1000.0 * (len(arrive) - 1)


def print_plan(arrive, leave, total, glide):
    print(f'时间表：总长 {total:.2f}s，{len(arrive)} 屏，每次切屏 {glide:g}s')
    for i in range(len(arrive)):
        end = leave[i] if i < len(leave) else total
        print(f'  {i:02d}  到达 {arrive[i]:6.2f}s  静止 {end - arrive[i]:5.2f}s')


# ---------------------------------------------------------------- 录制
def video_svg(svg, w, h):
    head_end = svg.index('>') + 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 1000" width="{w}" height="{h}" '
            f'preserveAspectRatio="xMidYMin slice" style="display:block;font-family:{lifeline.SERIF}">' + svg[head_end:])


def open_page(p, html, w, h):
    br = p.chromium.launch()
    pg = br.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
    pg.set_content(html, wait_until='load')
    pg.evaluate('document.fonts.ready.then(()=>1)')
    pg.evaluate('document.querySelector("svg").pauseAnimations()')
    return br, pg


def frame_js(y, t):
    return (f'(()=>{{const s=document.querySelector("svg");s.setAttribute("viewBox","0 {y:.2f} 750 1000");'
            f's.setCurrentTime({t:.4f});}})()')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec')
    ap.add_argument('-o', '--out', default=None, help='输出 mp4（默认和 spec 同名）')
    ap.add_argument('--glide', type=float, default=1.5, help='每次切屏滑多少秒，默认 1.5')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--width', type=int, default=1080, help='视频宽度，高度按 3:4 自动算')
    ap.add_argument('--crf', type=int, default=17)
    ap.add_argument('--small', action='store_true', help='另存一份 crf 23 的小文件（-small.mp4）')
    ap.add_argument('--plan', action='store_true', help='只打印时间表')
    ap.add_argument('--test', help='逗号分隔的秒数：只截这几个时刻')
    a = ap.parse_args()
    if a.glide <= 0:
        sys.exit('--glide 要大于 0')

    spec_path = os.path.abspath(a.spec)
    spec = json.load(open(spec_path, encoding='utf-8'))
    base = os.path.dirname(spec_path)
    out = os.path.abspath(a.out or os.path.splitext(spec_path)[0] + '.mp4')
    W, H = a.width, a.width * 4 // 3
    theme = dict(lifeline.THEMES.get(spec.get('theme', 'terra'), lifeline.THEMES['terra']))
    theme.update(spec.get('colors', {}))
    paper = theme['PAPER']

    holds = screen_holds(spec)
    arrive, leave, total = plan(holds, a.glide)
    print_plan(arrive, leave, total, a.glide)
    if a.plan:
        return

    offsets = [0.0] + [max(0.0, t - 0.2) for t in arrive[1:]]
    svg, errs, warns, ns = lifeline.build(spec, base, video_offsets=offsets)
    for e in errs:
        print('  [错误] ' + e)
    if ns != len(arrive):
        sys.exit('屏数和时间表对不上')
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;overflow:hidden;'
            f'background:{paper}}}</style></head><body>' + video_svg(svg, W, H) + '</body></html>')

    from playwright.sync_api import sync_playwright
    if a.test:
        d = os.path.splitext(out)[0] + '_test'
        os.makedirs(d, exist_ok=True)
        with sync_playwright() as p:
            br, pg = open_page(p, html, W, H)
            for tt in (float(x) for x in a.test.split(',') if x):
                pg.evaluate(frame_js(ypos(tt, arrive, leave), tt))
                path = os.path.join(d, f't{tt:06.2f}.jpg')
                open(path, 'wb').write(pg.screenshot(type='jpeg', quality=92))
                print('  ', path)
            br.close()
        return

    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        sys.exit('找不到 ffmpeg')
    tmp = tempfile.mkdtemp(prefix='lifeline_')
    video = os.path.join(tmp, 'video.mp4')
    nframes = int(round(total * a.fps))
    fade = min(1.2, total / 4)
    ff = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(a.fps), '-c:v', 'mjpeg',
                           '-i', '-', '-vf', f'fade=t=out:st={total - fade:.3f}:d={fade:.3f}:color=0x{paper.lstrip("#")},format=yuv420p',
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-r', str(a.fps), '-movflags', '+faststart',
                           video], stdin=subprocess.PIPE)
    t_start = time.time()
    with sync_playwright() as p:
        br, pg = open_page(p, html, W, H)
        for f in range(nframes):
            tt = f / a.fps
            pg.evaluate(frame_js(ypos(tt, arrive, leave), tt))
            ff.stdin.write(pg.screenshot(type='jpeg', quality=95))
            if f % 300 == 0:
                print(f'  帧 {f}/{nframes}  已用 {time.time() - t_start:.0f}s', flush=True)
        br.close()
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit('ffmpeg 编码失败')
    shutil.move(video, out)
    mb = os.path.getsize(out) / 1048576
    print(f'written {out}  {total:.2f}s  {W}x{H}  {mb:.1f}MB  录制用了 {time.time() - t_start:.0f}s')
    if a.small:
        small = os.path.splitext(out)[0] + '-small.mp4'
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', out, '-c:v', 'libx264', '-preset', 'slow', '-crf', '23',
                        '-movflags', '+faststart', small], check=True)
        print(f'written {small}  {os.path.getsize(small) / 1048576:.1f}MB')
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
