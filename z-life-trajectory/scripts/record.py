#!/usr/bin/env python3
"""把 lifeline 长图录成 3:4 竖屏视频（默认 1080x1440、30fps）。屏与屏之间缓动切换，切屏落在音乐的小节线上。

    python3 record.py spec.json -o life.mp4                       # 现场合成配乐（bgm.py，warm）
    python3 record.py spec.json -o life.mp4 --mood bright         # 换配乐情绪：warm / bright / calm
    python3 record.py spec.json -o life.mp4 --bgm song.mp3        # 用自己的音乐，librosa 自动找拍点
    python3 record.py spec.json -o life.mp4 --bgm song.mp3 --bpm 128 --t0 0.42   # 手动给拍点
    python3 record.py spec.json -o life.mp4 --bgm none            # 无声
    python3 record.py spec.json --plan                            # 只打印每屏的到达时刻和停留时长
    python3 record.py spec.json -o life.mp4 --test 2,9.5,40       # 只截这几个时刻的画面，存到 life_test/

每屏静止多久按文字量和插画块估算。想手动指定，在那一屏写 "hold": 秒数（封面写在 cover 里）。
依赖：playwright、ffmpeg；自带配乐要 numpy；给自己的音乐找拍点要 librosa（可选，没装就不对拍）。
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


# ---------------------------------------------------------------- 拍点
# 切屏只落在「强拍」上：4/4 拍里的第 1 拍和第 3 拍，也就是每两拍一个点。
def grid_from_bpm(bpm, t0=0.0, upto=900.0):
    step = 120.0 / bpm
    k = -int(t0 // step)
    out = []
    while True:
        t = t0 + k * step
        if t > upto:
            return out
        if t >= -1e-6:
            out.append(max(0.0, t))
        k += 1


def detect_grid(path, start=0.0, upto=900.0):
    """给自带音乐找强拍：先用 librosa 估速度，再在 ±3% 里扫一遍「速度 × 相位」，
    挑起音（低频加权，底鼓和贝斯更可信）最集中的那一组，整首歌按这个匀速网格走。
    最后挑低频最重的那一拍当第 1 拍。返回 (强拍时刻表, bpm, 第一个第 1 拍的时刻)。"""
    import numpy as np
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True, offset=start)
    hop = 256
    fps = sr / hop
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = librosa.onset.onset_strength(S=librosa.power_to_db(S[freqs < 160]), sr=sr, hop_length=hop)
    n = min(len(oenv), len(low))
    oenv, low = oenv[:n], low[:n]
    env = oenv / (oenv.mean() + 1e-9) + 2 * low / (low.mean() + 1e-9)
    tempo_fn = getattr(librosa.feature, 'tempo', None) or librosa.beat.tempo
    bpm0 = float(np.atleast_1d(tempo_fn(onset_envelope=oenv, sr=sr, hop_length=hop))[0])
    while bpm0 > 150:
        bpm0 /= 2
    while bpm0 < 70:
        bpm0 *= 2
    t = np.arange(n) / fps
    nb = 64
    best = None
    for per in np.linspace(60 / bpm0 * 0.97, 60 / bpm0 * 1.03, 601):
        prof = np.bincount(((t % per) / per * nb).astype(int) % nb, weights=env, minlength=nb)
        prof = prof + 0.5 * (np.roll(prof, 1) + np.roll(prof, -1))
        k = int(np.argmax(prof))
        if best is None or prof[k] > best[0]:
            best = (prof[k], per, (k + 0.5) / nb * per)
    peak, per, phase = best
    phase = (phase - 0.02) % per  # 起音曲线的峰值比真正的起拍晚一点点
    if peak / (2 * env.sum()) < 2.5 / nb:
        raise RuntimeError('节拍不明显')

    def lowsum(t0, step):
        idx = np.round(np.arange(t0, n / fps, step) * fps).astype(int)
        idx = idx[idx < n]
        return float(np.mean([low[max(0, i - 2):i + 3].max() for i in idx])) if len(idx) else 0.0

    q = int(np.argmax([lowsum(phase + j * per, 4 * per) for j in range(4)]))
    first = phase + q * per
    step = 2 * per
    t0 = first - step * int(first // step)
    out, x = [], t0
    while x <= upto:
        out.append(float(x))
        x += step
    return out, 60 / per, float(first)


# ---------------------------------------------------------------- 时间表
def plan(holds, grid=None, glide=1.5):
    """grid 是强拍时刻表。返回 arrive[i]（第 i 屏停稳）、leave[i]（开始滑向下一屏）、glides[i]、总时长。

    滑动时长取一个强拍间隔（太短就取两个），每屏都在强拍上停稳。"""
    n = len(holds)
    arrive, leave, glides = [0.0], [], []
    if not grid:
        t = 0.0
        for i in range(n - 1):
            t += holds[i]
            leave.append(t)
            t += glide
            arrive.append(t)
            glides.append(glide)
        return arrive, leave, glides, t + holds[-1]
    D = grid
    k = 0
    for i in range(n - 1):
        want = arrive[i] + holds[i]
        floor_ = arrive[i] + max(3.0, 0.75 * holds[i])
        best = None
        for j in range(k + 1, len(D)):
            h = D[j] - D[j - 1]
            g = h if h >= 0.9 or j < 2 else D[j] - D[j - 2]
            lv = D[j] - g
            if lv < floor_:
                continue
            if best is None or abs(lv - want) < abs(best[1] - want):
                best = (j, lv, g)
            if lv >= want:
                break
        if best is None:
            raise RuntimeError('音乐拍点不够长')
        k = best[0]
        leave.append(best[1])
        arrive.append(D[k])
        glides.append(best[2])
    end_want = arrive[-1] + holds[-1]
    j = next((j for j in range(k + 1, len(D)) if D[j] >= end_want - 0.6), None)
    return arrive, leave, glides, (D[j] if j is not None else end_want)


def ease(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ypos(t, arrive, leave, glides):
    for i, lv in enumerate(leave):
        if t < lv:
            return 1000.0 * i
        if t < arrive[i + 1]:
            return 1000.0 * (i + ease((t - lv) / glides[i]))
    return 1000.0 * (len(arrive) - 1)


def print_plan(holds, arrive, leave, total, note):
    print(f'时间表（{note}）：总长 {total:.2f}s，{len(arrive)} 屏')
    for i in range(len(arrive)):
        end = leave[i] if i < len(leave) else total
        print(f'  {i:02d}  到达 {arrive[i]:6.2f}s  静止 {end - arrive[i]:5.2f}s（估 {holds[i]:.1f}s）')


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
    ap.add_argument('--bgm', default='auto', help='auto（现场合成）/ none / 音乐文件路径')
    ap.add_argument('--mood', default='warm', help='auto 配乐的情绪：warm / bright / calm')
    ap.add_argument('--seed', type=int, default=7, help='auto 配乐的随机种子，换一个数换一种编排')
    ap.add_argument('--bpm', type=float, help='手动给速度（auto 时改配乐速度；自带音乐时跳过自动找拍）')
    ap.add_argument('--t0', type=float, default=0.0, help='自带音乐第一个强拍在第几秒（配合 --bpm）')
    ap.add_argument('--bgm-start', type=float, default=0.0, help='自带音乐从第几秒开始用')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--width', type=int, default=1080, help='视频宽度，高度按 3:4 自动算')
    ap.add_argument('--crf', type=int, default=17)
    ap.add_argument('--small', action='store_true', help='另存一份 crf 23 的小文件（-small.mp4）')
    ap.add_argument('--plan', action='store_true', help='只打印时间表')
    ap.add_argument('--test', help='逗号分隔的秒数：只截这几个时刻')
    a = ap.parse_args()

    spec_path = os.path.abspath(a.spec)
    spec = json.load(open(spec_path, encoding='utf-8'))
    base = os.path.dirname(spec_path)
    out = os.path.abspath(a.out or os.path.splitext(spec_path)[0] + '.mp4')
    W, H = a.width, a.width * 4 // 3
    theme = dict(lifeline.THEMES.get(spec.get('theme', 'terra'), lifeline.THEMES['terra']))
    theme.update(spec.get('colors', {}))
    paper = theme['PAPER']

    holds = screen_holds(spec)
    music, grid, note = None, None, '不对拍'
    if a.bgm == 'auto':
        import bgm as BGM
        bpm = a.bpm or BGM.MOODS[a.mood]['bpm']
        grid, note = grid_from_bpm(bpm), f'现场合成配乐 {a.mood} {bpm:g} BPM'
    elif a.bgm != 'none':
        music = os.path.abspath(a.bgm)
        if a.bpm:
            grid, note = grid_from_bpm(a.bpm, a.t0 - a.bgm_start), f'手动拍点 {a.bpm:g} BPM'
        else:
            try:
                grid, bpm, first = detect_grid(music, a.bgm_start)
                note = f'librosa 找拍 {bpm:.1f} BPM，第一个重拍 {first:.2f}s'
            except ImportError:
                note = '没装 librosa，不对拍（pip install librosa 或用 --bpm/--t0）'
            except Exception as e:  # noqa: BLE001
                note = f'找拍失败（{e}），不对拍'
    elif a.bpm:
        grid, note = grid_from_bpm(a.bpm, a.t0), f'无声，按 {a.bpm:g} BPM 切屏'
    arrive, leave, glides, total = plan(holds, grid)
    print_plan(holds, arrive, leave, total, note)
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
                pg.evaluate(frame_js(ypos(tt, arrive, leave, glides), tt))
                path = os.path.join(d, f't{tt:06.2f}.jpg')
                open(path, 'wb').write(pg.screenshot(type='jpeg', quality=92))
                print('  ', path)
            br.close()
        return

    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        sys.exit('找不到 ffmpeg')
    tmp = tempfile.mkdtemp(prefix='lifeline_')
    silent = os.path.join(tmp, 'silent.mp4')
    nframes = int(round(total * a.fps))
    fade = min(1.2, total / 4)
    ff = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(a.fps), '-c:v', 'mjpeg',
                           '-i', '-', '-vf', f'fade=t=out:st={total - fade:.3f}:d={fade:.3f}:color=0x{paper.lstrip("#")},format=yuv420p',
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-r', str(a.fps), '-movflags', '+faststart',
                           silent], stdin=subprocess.PIPE)
    t_start = time.time()
    with sync_playwright() as p:
        br, pg = open_page(p, html, W, H)
        for f in range(nframes):
            tt = f / a.fps
            pg.evaluate(frame_js(ypos(tt, arrive, leave, glides), tt))
            ff.stdin.write(pg.screenshot(type='jpeg', quality=95))
            if f % 300 == 0:
                print(f'  帧 {f}/{nframes}  已用 {time.time() - t_start:.0f}s', flush=True)
        br.close()
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit('ffmpeg 编码失败')

    if a.bgm == 'auto':
        import bgm as BGM
        music = os.path.join(tmp, 'bgm.wav')
        x, _ = BGM.generate(total, a.bpm or BGM.MOODS[a.mood]['bpm'], a.mood, a.seed)
        BGM.write_wav(music, x)
    if music:
        af = (f'atrim=0:{total:.3f},afade=t=in:st=0:d=0.3,afade=t=out:st={max(0, total - 2.5):.3f}:d=2.5,'
              'loudnorm=I=-16:TP=-1.5:LRA=11')
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-i', silent]
        if a.bgm_start and a.bgm != 'auto':
            cmd += ['-ss', f'{a.bgm_start:.3f}']
        cmd += ['-stream_loop', '-1', '-i', music, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', af,
                '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
        subprocess.run(cmd, check=True)
    else:
        shutil.move(silent, out)
    mb = os.path.getsize(out) / 1048576
    print(f'written {out}  {total:.2f}s  {W}x{H}  {mb:.1f}MB  录制用了 {time.time() - t_start:.0f}s')
    if a.small:
        small = os.path.splitext(out)[0] + '-small.mp4'
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', out, '-c:v', 'libx264', '-preset', 'slow', '-crf', '23',
                        '-c:a', 'copy', '-movflags', '+faststart', small], check=True)
        print(f'written {small}  {os.path.getsize(small) / 1048576:.1f}MB')
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
