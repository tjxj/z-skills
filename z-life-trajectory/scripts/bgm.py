#!/usr/bin/env python3
"""现场合成一段配乐：电钢琴琶音 + 铺底 + 贝斯 + 轻鼓。没有版权顾虑，节拍网格精确已知。

    python3 bgm.py -o music.wav --seconds 128                  # 默认 warm，100 BPM
    python3 bgm.py -o music.wav --seconds 128 --mood bright --seed 3

mood：
    warm    小调，温和叙事（默认，100 BPM）
    bright  大调，明快（112 BPM）
    calm    慢，留白多，鼓很轻（84 BPM）

第一个强拍在 0 秒，每小节 4 拍。record.py --bgm auto 会自动调用它，让每次切屏都落在小节线上。
只依赖 numpy。
"""
import argparse
import wave

import numpy as np

SR = 44100

# 和弦：(铺底音, 贝斯根音)，MIDI 音高，60 = 中央 C
MOODS = {
    'warm': dict(bpm=100, arp='eighth', drums='soft', phrases=[
        [([57, 60, 64, 67], 45), ([53, 57, 60, 64], 41), ([55, 60, 64, 71], 48), ([55, 59, 62, 67], 43)],
        [([53, 57, 60, 64], 41), ([55, 59, 62, 67], 43), ([52, 55, 59, 62], 40), ([57, 60, 64, 67], 45)],
    ], tonic=([57, 60, 64, 69], 45)),
    'bright': dict(bpm=112, arp='eighth', drums='full', phrases=[
        [([55, 60, 64, 67], 48), ([55, 59, 62, 67], 47), ([57, 60, 64, 69], 45), ([57, 60, 65, 69], 41)],
        [([57, 60, 64, 69], 45), ([57, 60, 65, 69], 41), ([55, 60, 64, 67], 48), ([55, 59, 62, 67], 43)],
    ], tonic=([55, 60, 64, 72], 48)),
    'calm': dict(bpm=84, arp='quarter', drums='light', phrases=[
        [([57, 61, 64, 66], 50), ([57, 59, 62, 66], 47), ([55, 59, 62, 66], 43), ([57, 61, 64, 69], 45)],
        [([55, 59, 62, 66], 43), ([57, 61, 64, 69], 45), ([54, 57, 61, 64], 42), ([57, 59, 62, 66], 47)],
    ], tonic=([54, 57, 62, 66], 50)),
}

ARPS = [
    [0, 2, 4, 2, 5, 2, 4, 3],
    [0, 4, 2, 5, 3, 4, 1, 4],
    [0, None, 2, 4, None, 2, 5, 3],
    [1, 3, 5, 3, 4, 2, 3, 0],
]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


class Bus:
    def __init__(self, n):
        self.x = np.zeros((n, 2))

    def add(self, t, sig, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= len(self.x) or i < 0:
            return
        sig = sig[:len(self.x) - i]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.x[i:i + len(sig), 0] += sig * gain * l * 1.414
        self.x[i:i + len(sig), 1] += sig * gain * r * 1.414


def ep_note(f, dur, vel):
    """FM 电钢琴：起音亮，随后变暖。"""
    n = int((dur + 1.4) * SR)
    t = np.arange(n) / SR
    idx = (2.0 * np.exp(-t / 0.16) + 0.22) * (0.6 + 0.4 * vel)
    car = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    tine = 0.16 * np.sin(2 * np.pi * f * 7.0 * t) * np.exp(-t / 0.035) if f * 7 < 12000 else 0
    env = (1 - np.exp(-t / 0.004)) * np.exp(-t / 1.0)
    off = t > dur
    env[off] *= np.exp(-(t[off] - dur) / 0.28)
    return (car + tine) * env * vel


def pad_chord(notes, dur, rng, detune):
    n = int((dur + 1.3) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes:
        f = hz(m) * 2 ** (detune / 1200)
        ph = rng.uniform(0, 2 * np.pi)
        for h in range(1, 8):
            if f * h > 9000:
                break
            out += np.sin(2 * np.pi * f * h * t + ph * h) / h ** 1.6
    att = np.clip(t / 0.45, 0, 1) ** 2
    rel = np.clip((dur + 1.3 - t) / 1.3, 0, 1)
    swell = 1 + 0.07 * np.sin(2 * np.pi * 0.23 * t)
    return out * att * rel * swell / len(notes)


def bass_note(f, dur, vel):
    n = int((dur + 0.25) * SR)
    t = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.22 * np.sin(6 * np.pi * f * t)
    env = (1 - np.exp(-t / 0.006)) * np.exp(-t / 0.9)
    off = t > dur
    env[off] *= np.exp(-(t[off] - dur) / 0.07)
    return w * env * vel


def kick(rng):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 56 + 90 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)
    click = np.diff(rng.standard_normal(n + 1)) * np.exp(-t / 0.002) * 0.18
    return body + click


def snap(rng):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    nz = np.diff(rng.standard_normal(n + 1))
    env = np.exp(-t / 0.055) * (1 + 0.6 * np.exp(-((t - 0.012) / 0.004) ** 2))
    return nz * env * 0.5 + 0.35 * np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.035)


def hat(rng):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    nz = np.diff(np.diff(rng.standard_normal(n + 2)))
    return nz * np.exp(-t / 0.022) * 0.5


def master_eq(x):
    """零相位均衡：切掉 40Hz 以下，低频收 3dB，3kHz 以上提一点，手机外放更清楚。"""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    hp = (f / 40) ** 2 / (1 + (f / 40) ** 2)
    low = 1 - (1 - 10 ** (-3 / 20)) / (1 + (f / 120) ** 2)
    high = 1 + (10 ** (3.5 / 20) - 1) * (f / 3000) ** 2 / (1 + (f / 3000) ** 2)
    return np.fft.irfft(X * (hp * low * high)[:, None], len(x), axis=0)


def fftconv(x, h):
    n = len(x) + len(h) - 1
    N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[:n]


def reverb(x, seconds=2.3, seed=0):
    rng = np.random.default_rng(seed + 99)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros((len(x) + n - 1 + int(0.02 * SR), 2))
    pre = int(0.02 * SR)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * t / seconds)
        spec = np.fft.rfft(ir)
        fr = np.fft.rfftfreq(n, 1 / SR)
        ir = np.fft.irfft(spec / (1 + (fr / 3800) ** 2), n)
        ir /= np.sqrt(np.sum(ir ** 2))
        y = fftconv(x[:, ch], ir)
        out[pre:pre + len(y), ch] = y
    return out[:len(x)]


def generate(seconds, bpm=None, mood='warm', seed=7):
    """返回 (立体声 float 数组, bpm)。第一个强拍在 0 秒，最后两小节是收尾。"""
    cfg = MOODS[mood]
    bpm = float(bpm or cfg['bpm'])
    beat = 60.0 / bpm
    bar = 4 * beat
    nb = max(4, int(round(seconds / bar)))
    tail = 2.4
    n = int((nb * bar + tail) * SR)
    rng = np.random.default_rng(seed)
    pad, keys, low, drums = Bus(n), Bus(n), Bus(n), Bus(n)
    intro = 2 if nb >= 12 else 1
    outro = 2 if nb >= 8 else 1
    body_end = nb - outro
    brk = set(range(int(nb * 0.56), int(nb * 0.56) + 2)) if nb >= 40 else set()
    k1, sn, kh = kick(rng), snap(rng), [hat(rng) for _ in range(4)]
    arp_seq = [ARPS[0], ARPS[1], ARPS[0], ARPS[3], ARPS[1], ARPS[2]]

    for b in range(nb):
        t0 = b * bar
        if b >= body_end:
            notes, root = cfg['tonic']
        else:
            ph = cfg['phrases'][(b // 4) % len(cfg['phrases'])]
            notes, root = ph[b % 4]
        last = b >= body_end
        # 铺底：每小节一个和弦，收尾和弦拉长
        dur = bar * (outro if (last and b == body_end) else 1)
        if not (last and b > body_end):
            for det, pan in ((-5, -0.55), (5, 0.55)):
                pad.add(t0, pad_chord(notes, dur, rng, det), 0.30, pan)
        # 电钢琴琶音
        tones = sorted(notes) + [sorted(notes)[0] + 12, sorted(notes)[1] + 12]
        tones = [m + 12 for m in tones]
        if last:
            if b == body_end:
                for k, m in enumerate([tones[0], tones[2], tones[4], tones[5]]):
                    keys.add(t0 + k * beat, ep_note(hz(m), bar * 2 - k * beat, 0.8 - 0.08 * k), 0.30, -0.2 + 0.15 * k)
                low.add(t0, bass_note(hz(root), bar * 1.6, 0.8), 0.4)
                if cfg['drums'] != 'light':
                    drums.add(t0, k1, 0.5)
            continue
        pat = arp_seq[(b // 8) % len(arp_seq)]
        if b < intro or cfg['arp'] == 'quarter':
            steps = [(k * 2, pat[k * 2]) for k in range(4)]
            step_len = beat
        else:
            steps = list(enumerate(pat))
            step_len = beat / 2
        for k, ix in steps:
            if ix is None:
                continue
            tt = t0 + k * beat / 2 + rng.normal(0, 0.004)
            vel = (0.95 if k % 4 == 0 else 0.78) * rng.uniform(0.9, 1.0)
            keys.add(max(0, tt), ep_note(hz(tones[ix]), step_len * 1.6, vel), 0.30, rng.uniform(-0.35, 0.35))
        # 贝斯
        if b >= intro:
            f = hz(root)
            low.add(t0, bass_note(f, beat * 1.4, 0.9), 0.4)
            low.add(t0 + beat * 1.5, bass_note(f, beat * 0.45, 0.55), 0.4)
            low.add(t0 + beat * 2, bass_note(f, beat * 0.9, 0.75), 0.4)
            low.add(t0 + beat * 3.5, bass_note(hz(root + 7) if b % 2 else f * 2, beat * 0.45, 0.5), 0.4)
        # 鼓
        if b < intro or b in brk:
            continue
        full = b >= intro + 4 and cfg['drums'] != 'light'
        fill = (b - intro) % 8 == 7
        kicks = [0, 2] if cfg['drums'] != 'light' else [0]
        if fill and full:
            kicks = [0, 2, 3.5]
        if full or cfg['drums'] == 'light':
            for kb in kicks:
                drums.add(t0 + kb * beat, k1, 0.5 if cfg['drums'] != 'light' else 0.36)
        if full and cfg['drums'] == 'full' or (full and b >= intro + 8):
            for sb in (1, 3):
                drums.add(t0 + sb * beat, sn, 0.16, 0.1)
        hats = [0.5, 1.5, 2.5, 3.5] if not fill else [x * 0.5 for x in range(8)]
        for hb in hats:
            drums.add(t0 + hb * beat + rng.normal(0, 0.003), kh[rng.integers(4)],
                      0.12 * rng.uniform(0.75, 1.0) * (0.7 if cfg['drums'] == 'light' else 1.0), 0.35)

    dry = pad.x * 0.9 + keys.x + low.x + drums.x
    send = pad.x * 0.5 + keys.x * 0.6 + drums.x * 0.08
    wet = reverb(send, 2.4, seed)
    mix = master_eq(dry + wet * 0.32)
    mix /= max(1e-9, np.abs(mix).max())
    mix = np.tanh(mix * 1.3) / 1.3
    mix *= 0.89 / max(1e-9, np.abs(mix).max())
    fade = int(0.03 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)[:, None]
    end = int(tail * SR)
    mix[-end:] *= np.linspace(1, 0, end)[:, None] ** 1.5
    return mix.astype(np.float32), bpm


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--out', default='music.wav')
    ap.add_argument('--seconds', type=float, default=120)
    ap.add_argument('--bpm', type=float)
    ap.add_argument('--mood', default='warm', choices=sorted(MOODS))
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    x, bpm = generate(a.seconds, a.bpm, a.mood, a.seed)
    write_wav(a.out, x)
    print(f'written {a.out}  {len(x) / SR:.1f}s  {bpm:g} BPM  每小节 {240 / bpm:.3f}s  第一个强拍 0s')


if __name__ == '__main__':
    main()
