#!/usr/bin/env python3
"""会动的小插画库：每个图标画在以 (0,0) 为中心、约 120x120 的局部坐标里。

只用公众号能活下来的写法：没有 id / defs / style / script / 渐变 / 滤镜，
动画全部是 SMIL（animate / animateTransform / animateMotion），repeatCount="indefinite"。

    python3 icons.py gallery out.svg      # 把全部图标排成一张预览图
"""
import math
import sys


class Pal:
    """图标用到的颜色。dark=True 时给深色屏用。"""

    def __init__(self, theme, dark=False):
        t = theme
        self.dark = dark
        self.acc, self.acc_l, self.acc_p, self.sec = t['ACCENT'], t['ACCENT_L'], t['ACCENT_P'], t['SECOND']
        self.gold, self.gold_d, self.gold_l = '#D4A24C', '#A87B2C', '#F0D594'
        if dark:
            self.fg, self.bg, self.white = t['PAPER'], t['DARK'], '#2A3242'
            self.mute, self.rule, self.beige = '#6E7484', '#4A5265', '#3A4252'
            self.panel, self.panel2, self.fg2 = '#0F141D', '#2A3242', '#C9C3B8'
            self.acc = t['DACCENT']
        else:
            self.fg, self.bg, self.white = t['INK'], t['PAPER'], '#FFFFFF'
            self.mute, self.rule, self.beige = t['GRAY3'], t['RULE2'], '#E9DFC9'
            self.panel, self.panel2, self.fg2 = '#151B26', '#3A4252', '#2E3646'


def _f(v):
    s = '%.1f' % v
    return s[:-2] if s.endswith('.0') else s


def _pts(ps):
    return ' '.join(f'{_f(x)},{_f(y)}' for x, y in ps)


R = 'repeatCount="indefinite"'

SPARK = 'M0,-11 L2.6,-2.6 L11,0 L2.6,2.6 L0,11 L-2.6,2.6 L-11,0 L-2.6,-2.6 Z'


def sparkle(x, y, color, begin=0.0, dur=2.4, s=1.0):
    return (f'<g transform="translate({_f(x)} {_f(y)}) scale({s})"><path d="{SPARK}" fill="{color}">'
            f'<animateTransform attributeName="transform" type="scale" values="0;1;0;0" keyTimes="0;0.2;0.4;1" dur="{dur}s" begin="{begin}s" {R}/></path></g>')


def ring_pulse(x, y, color, r0, r1, dur=2.4, begin=0.0, w=2.5):
    return (f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{r0}" fill="none" stroke="{color}" stroke-width="{w}" opacity="0">'
            f'<animate attributeName="r" values="{r0};{r1}" dur="{dur}s" begin="{begin}s" {R}/>'
            f'<animate attributeName="opacity" values="0.8;0" dur="{dur}s" begin="{begin}s" {R}/></circle>')


def _bez_len(p0, p1, p2, p3, n=40):
    L, prev = 0.0, p0
    for i in range(1, n + 1):
        t = i / n
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
        L += math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
    return L


def cube_frames(cx, cy, r, n=12, tilt=0.42):
    verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    edges = [(a, b) for a in range(8) for b in range(a + 1, 8)
             if sum(abs(verts[a][k] - verts[b][k]) for k in range(3)) == 2]
    frames = []
    for f in range(n + 1):
        th = (math.pi / 2) * f / n + 0.35
        pts = []
        for (x, y, z) in verts:
            x1 = x * math.cos(th) + z * math.sin(th)
            z1 = -x * math.sin(th) + z * math.cos(th)
            y2 = y * math.cos(tilt) - z1 * math.sin(tilt)
            z2 = y * math.sin(tilt) + z1 * math.cos(tilt)
            p = 4.2 / (4.2 + z2)
            pts.append((cx + x1 * r * p, cy + y2 * r * p))
        frames.append(' '.join(f'M{pts[a][0]:.1f},{pts[a][1]:.1f} L{pts[b][0]:.1f},{pts[b][1]:.1f}' for a, b in edges))
    return frames


def gear_path(ro, ri, teeth):
    pts = []
    for k in range(teeth):
        a0 = 2 * math.pi * k / teeth
        step = 2 * math.pi / teeth
        for frac, rr in ((0.0, ri), (0.12, ro), (0.42, ro), (0.54, ri)):
            a = a0 + frac * step
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + ' Z'


# ---------------------------------------------------------------- 学习与工作
def i_book(P):
    lp = 'M0,-28 Q-28,-40 -58,-30 L-58,30 Q-28,20 0,32 Z'
    rp = 'M0,-28 Q28,-40 58,-30 L58,30 Q28,20 0,32 Z'
    s = f'<path d="{lp}" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    s += f'<path d="{rp}" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    for k in range(3):
        yy = -12 + k * 13
        s += f'<line x1="-46" y1="{yy}" x2="-12" y2="{yy + 2}" stroke="{P.mute}" stroke-width="2.5" stroke-linecap="round"/>'
        s += f'<line x1="12" y1="{yy + 2}" x2="46" y2="{yy}" stroke="{P.mute}" stroke-width="2.5" stroke-linecap="round"/>'
    page = f'<path d="{rp}" fill="{P.bg}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    for k in range(3):
        yy = -12 + k * 13
        page += f'<line x1="12" y1="{yy + 2}" x2="46" y2="{yy}" stroke="{P.acc_l}" stroke-width="2.5" stroke-linecap="round"/>'
    s += (f'<g>{page}<animateTransform attributeName="transform" type="scale" values="1 1;1 1;-1 1;-1 1;1 1" '
          f'keyTimes="0;0.3;0.45;0.8;1" dur="4.4s" {R}/></g>')
    return s


def i_cap(P):
    s = '<g transform="translate(0 -8)">'
    s += f'<path d="M-34,2 L-34,30 Q0,46 34,30 L34,2 Z" fill="{P.fg}"/>'
    s += f'<path d="M0,-34 L62,-8 L0,18 L-62,-8 Z" fill="{P.fg}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    s += f'<path d="M0,-26 L46,-8 L0,10 L-46,-8 Z" fill="{P.fg2 if not P.dark else P.panel2}"/>'
    s += f'<circle cx="0" cy="-8" r="4" fill="{P.acc_l}"/>'
    s += (f'<g><animateTransform attributeName="transform" type="rotate" values="-7 48 -4;9 48 -4;-7 48 -4" dur="2.8s" {R}/>'
          f'<path d="M0,-8 L48,-4 L48,34" fill="none" stroke="{P.acc_l}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
          f'<rect x="43" y="32" width="10" height="18" rx="3" fill="{P.acc_l}"/></g>')
    return s + '</g>'


def i_school(P):
    s = f'<line x1="-58" y1="50" x2="58" y2="50" stroke="{P.fg}" stroke-width="3" stroke-linecap="round"/>'
    s += f'<path d="M-50,-6 L0,-34 L50,-6 Z" fill="{P.acc}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    s += f'<rect x="-44" y="-6" width="88" height="56" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    for cx in (-30, -12, 12, 30):
        s += f'<rect x="{cx - 4}" y="2" width="8" height="40" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="2"/>'
    s += f'<rect x="-8" y="26" width="16" height="24" fill="{P.fg}"/>'
    s += f'<circle cx="0" cy="-14" r="6" fill="{P.white}" stroke="{P.fg}" stroke-width="2"/>'
    s += f'<line x1="0" y1="-34" x2="0" y2="-62" stroke="{P.fg}" stroke-width="2.5"/>'
    s += (f'<path d="M0,-62 Q8,-66 15,-62 T30,-62 V-48 Q22,-52 15,-48 T0,-48 Z" fill="{P.acc_l}">'
          f'<animate attributeName="d" values="M0,-62 Q8,-66 15,-62 T30,-62 V-48 Q22,-52 15,-48 T0,-48 Z;'
          f'M0,-62 Q8,-58 15,-62 T30,-62 V-48 Q22,-44 15,-48 T0,-48 Z;M0,-62 Q8,-66 15,-62 T30,-62 V-48 Q22,-52 15,-48 T0,-48 Z" dur="1.6s" {R}/></path>')
    return s


def i_computer(P):
    s = f'<rect x="-62" y="-58" width="124" height="90" rx="10" fill="{P.beige}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<rect x="-50" y="-47" width="100" height="66" rx="5" fill="#0F2418"/>'
    widths = (64, 44, 72, 36)
    for k, w in enumerate(widths):
        y = -38 + k * 14
        f0, f1 = 0.04 + k * 0.18, 0.18 + k * 0.18
        s += (f'<rect x="-42" y="{y}" width="0" height="6" rx="2" fill="#7CE38B">'
              f'<animate attributeName="width" values="0;0;{w};{w};0" keyTimes="0;{f0:.2f};{f1:.2f};0.92;1" dur="5s" {R}/></rect>')
    s += f'<rect x="-4" y="1" width="7" height="9" fill="#7CE38B"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="0.9s" {R}/></rect>'
    s += f'<rect x="-66" y="38" width="132" height="20" rx="6" fill="{P.beige}" stroke="{P.fg}" stroke-width="3"/>'
    for r in range(2):
        for c in range(9):
            s += f'<rect x="{-58 + c * 13}" y="{43 + r * 7}" width="10" height="4" rx="1.5" fill="{P.rule}"/>'
    return s


def i_workstation(P):
    s = f'<rect x="-62" y="-58" width="124" height="90" rx="10" fill="#DAD5CC" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<rect x="-51" y="-47" width="102" height="68" rx="6" fill="{P.panel}"/>'
    fr = cube_frames(0, -13, 22)
    s += (f'<path d="{fr[0]}" fill="none" stroke="#7FD6CF" stroke-width="2.4" stroke-linecap="round">'
          f'<animate attributeName="d" values="{";".join(fr)}" dur="2.6s" {R}/></path>')
    s += f'<path d="M-18,32 L18,32 L24,46 L-24,46 Z" fill="#C9C3B8" stroke="{P.fg}" stroke-width="2.5" stroke-linejoin="round"/>'
    s += f'<rect x="-46" y="46" width="92" height="9" rx="4" fill="#DAD5CC" stroke="{P.fg}" stroke-width="2.5"/>'
    return s


def i_cube(P):
    fr = cube_frames(0, -4, 36)
    s = f'<ellipse cx="0" cy="50" rx="40" ry="7" fill="{P.rule}" opacity="0.6"/>'
    s += (f'<path d="{fr[0]}" fill="none" stroke="{P.sec}" stroke-width="3.2" stroke-linecap="round">'
          f'<animate attributeName="d" values="{";".join(fr)}" dur="3s" {R}/></path>')
    return s


def i_code(P):
    s = f'<rect x="-64" y="-48" width="128" height="96" rx="10" fill="{P.panel if P.dark else "#1E2430"}" stroke="{P.rule if P.dark else "#1E2430"}" stroke-width="2"/>'
    for k, c in enumerate(('#E06C5A', '#E9A23B', '#5FB37A')):
        s += f'<circle cx="{-50 + k * 12}" cy="-34" r="4" fill="{c}"/>'
    rows = [(-50, 60, '#8B93A6'), (-40, 44, P.acc_l), (-40, 68, '#7FD6CF'), (-50, 30, '#8B93A6'), (-40, 52, P.acc_l)]
    for k, (x, w, c) in enumerate(rows):
        y = -18 + k * 13
        f0, f1 = 0.03 + k * 0.15, 0.15 + k * 0.15
        s += (f'<rect x="{x}" y="{y}" width="0" height="6" rx="3" fill="{c}">'
              f'<animate attributeName="width" values="0;0;{w};{w};0" keyTimes="0;{f0:.2f};{f1:.2f};0.93;1" dur="5s" {R}/></rect>')
    s += f'<rect x="16" y="33" width="8" height="10" fill="{P.acc_l}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" {R}/></rect>'
    return s


def i_chip(P):
    s = ''
    for k in range(5):
        p = -24 + k * 12
        s += f'<line x1="{p}" y1="-38" x2="{p}" y2="-50" stroke="{P.mute}" stroke-width="3.5" stroke-linecap="round"/>'
        s += f'<line x1="{p}" y1="38" x2="{p}" y2="50" stroke="{P.mute}" stroke-width="3.5" stroke-linecap="round"/>'
        s += f'<line x1="-38" y1="{p}" x2="-50" y2="{p}" stroke="{P.mute}" stroke-width="3.5" stroke-linecap="round"/>'
        s += f'<line x1="38" y1="{p}" x2="50" y2="{p}" stroke="{P.mute}" stroke-width="3.5" stroke-linecap="round"/>'
    s += f'<rect x="-40" y="-40" width="80" height="80" rx="9" fill="{P.panel2 if P.dark else P.fg}"/>'
    k = 0
    for r in range(3):
        for c in range(3):
            x, y = -29 + c * 20, -29 + r * 20
            s += f'<rect x="{x}" y="{y}" width="16" height="16" rx="3" fill="{P.panel2 if not P.dark else P.panel}"/>'
            s += (f'<rect x="{x}" y="{y}" width="16" height="16" rx="3" fill="{P.acc_l}" opacity="0">'
                  f'<animate attributeName="opacity" values="0;1;0" dur="1.8s" begin="{(c + r) * 0.15:.2f}s" {R}/></rect>')
            k += 1
    return s


# ---------------------------------------------------------------- 出行与地点
PLANE = 'M13,0 L4,-3 L-2,-12 L-6,-12 L-3,-3 L-10,-3 L-13,-8 L-16,-8 L-14,0 L-16,8 L-13,8 L-10,3 L-3,3 L-6,12 L-2,12 L4,3 Z'


def cloud(x, y, s, P):
    return (f'<g transform="translate({x} {y}) scale({s})"><path d="M-20,8 Q-22,-6 -8,-6 Q-4,-16 8,-12 Q20,-14 20,-2 Q28,0 24,8 Z" '
            f'fill="{P.white}" stroke="{P.rule}" stroke-width="2" stroke-linejoin="round"/></g>')


def i_plane(P):
    arc = 'M-58,30 C-26,-34 26,-34 58,30'
    s = f'<g><animateTransform attributeName="transform" type="translate" values="10 0;-10 0" dur="5s" {R}/>{cloud(-30, 36, 1.0, P)}{cloud(34, -36, 0.8, P)}</g>'
    s += f'<path d="{arc}" fill="none" stroke="{P.acc}" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="0.1 10"/>'
    s += (f'<path d="{PLANE}" fill="{P.fg}" opacity="0"><animateMotion path="{arc}" dur="3.2s" rotate="auto" {R}/>'
          f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.88;1" dur="3.2s" {R}/></path>')
    return s


def i_ship(P):
    s = (f'<g><animateTransform attributeName="transform" type="rotate" values="-3 0 20;3 0 20;-3 0 20" dur="3s" {R}/>'
         f'<path d="M-50,14 H50 L38,38 H-38 Z" fill="{P.fg}"/>'
         f'<rect x="-30" y="-6" width="56" height="20" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
         f'<rect x="-18" y="-24" width="18" height="18" fill="{P.acc}" stroke="{P.fg}" stroke-width="3"/>'
         f'<rect x="6" y="-20" width="12" height="14" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3"/>')
    for k in range(4):
        s += f'<circle cx="{-20 + k * 13}" cy="4" r="3" fill="{P.sec}"/>'
    s += '</g>'
    for k in range(3):
        s += (f'<circle cx="-9" cy="-30" r="5" fill="{P.rule}" opacity="0">'
              f'<animate attributeName="cy" values="-30;-62" dur="2.4s" begin="{k * 0.8:.1f}s" {R}/>'
              f'<animate attributeName="r" values="4;9" dur="2.4s" begin="{k * 0.8:.1f}s" {R}/>'
              f'<animate attributeName="opacity" values="0.9;0" dur="2.4s" begin="{k * 0.8:.1f}s" {R}/></circle>')
    w1 = 'M-56,42 q7,-5 14,0 t14,0 t14,0 t14,0 t14,0 t14,0 t14,0 t14,0'
    w2 = 'M-56,42 q7,5 14,0 t14,0 t14,0 t14,0 t14,0 t14,0 t14,0 t14,0'
    s += (f'<path d="{w1}" fill="none" stroke="{P.sec}" stroke-width="3" stroke-linecap="round">'
          f'<animate attributeName="d" values="{w1};{w2};{w1}" dur="1.6s" {R}/></path>')
    return s


def i_car(P):
    road = f'<line x1="-60" y1="44" x2="60" y2="44" stroke="{P.fg}" stroke-width="3" stroke-linecap="round"/>'
    road += (f'<line x1="-60" y1="54" x2="60" y2="54" stroke="{P.mute}" stroke-width="3" stroke-dasharray="14 12">'
             f'<animate attributeName="stroke-dashoffset" values="0;26" dur="0.5s" {R}/></line>')
    s = road
    for k, y in enumerate((-10, 4, 18)):
        s += (f'<line x1="-62" y1="{y}" x2="-46" y2="{y}" stroke="{P.rule}" stroke-width="3" stroke-linecap="round" opacity="0">'
              f'<animate attributeName="opacity" values="0;1;0" dur="0.9s" begin="{k * 0.3:.1f}s" {R}/></line>')
    body = (f'<path d="M-44,30 V14 Q-44,6 -36,4 L-22,-14 Q-18,-20 -10,-20 H18 Q26,-20 30,-14 L40,2 Q52,4 52,14 V30 Z" '
            f'fill="{P.acc}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M-30,2 L-18,-12 H4 V2 Z M10,2 V-12 H20 L30,2 Z" fill="{P.acc_p}"/>')
    s += f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -2;0 0" dur="0.5s" {R}/>{body}</g>'
    for wx in (-26, 32):
        s += (f'<g transform="translate({wx} 32)"><circle r="12" fill="{P.fg}"/><g>'
              f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="0.6s" {R}/>'
              f'<path d="M0,-7 V7 M-7,0 H7" stroke="{P.mute}" stroke-width="2.5"/></g><circle r="3" fill="{P.white}"/></g>')
    return s


def i_globe(P):
    s = f'<circle cx="0" cy="0" r="46" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3"/>'
    for y in (-24, 0, 24):
        hw = math.sqrt(46 ** 2 - y ** 2) - 2
        s += f'<line x1="{-hw:.1f}" y1="{y}" x2="{hw:.1f}" y2="{y}" stroke="{P.fg}" stroke-width="1.8" opacity="0.55"/>'
    for ph in (0.0, math.pi / 3, 2 * math.pi / 3):
        vals = ';'.join(f'{abs(44 * math.cos(ph + 2 * math.pi * k / 24) ):.1f}' for k in range(25))
        s += (f'<ellipse cx="0" cy="0" rx="44" ry="45" fill="none" stroke="{P.fg}" stroke-width="1.8" opacity="0.55">'
              f'<animate attributeName="rx" values="{vals}" dur="6s" {R}/></ellipse>')
    a, b, rot = 62, 17, math.radians(-18)
    p1 = (a * math.cos(rot), a * math.sin(rot))
    p2 = (-p1[0], -p1[1])
    orbit = f'M{p1[0]:.1f},{p1[1]:.1f} A{a},{b} -18 1 1 {p2[0]:.1f},{p2[1]:.1f} A{a},{b} -18 1 1 {p1[0]:.1f},{p1[1]:.1f}'
    s += f'<path d="{orbit}" fill="none" stroke="{P.acc}" stroke-width="2" stroke-dasharray="0.1 7" stroke-linecap="round"/>'
    s += f'<circle r="6" fill="{P.acc}" stroke="{P.white}" stroke-width="2"><animateMotion path="{orbit}" dur="4s" {R}/></circle>'
    return s


def i_pin(P):
    s = (f'<path d="M-58,-20 L-20,-32 L20,-20 L58,-32 V40 L20,52 L-20,40 L-58,52 Z" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
         f'<path d="M-20,-32 V40 M20,-20 V52" stroke="{P.fg}" stroke-width="2" opacity="0.4"/>'
         f'<path d="M-44,30 C-30,4 -12,30 4,12" fill="none" stroke="{P.acc}" stroke-width="3" stroke-dasharray="0.1 8" stroke-linecap="round"/>')
    s += (f'<ellipse cx="4" cy="16" rx="12" ry="4" fill="{P.fg}" opacity="0.25">'
          f'<animate attributeName="rx" values="12;7;12" dur="1.4s" {R}/></ellipse>')
    pin = (f'<path d="M4,14 C-8,-2 -16,-12 -16,-24 A20,20 0 0 1 24,-24 C24,-12 16,-2 4,14 Z" fill="{P.acc}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
           f'<circle cx="4" cy="-24" r="7" fill="{P.white}"/>')
    s += f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -12;0 0" dur="1.4s" {R}/>{pin}</g>'
    return s


def i_house(P):
    s = f'<line x1="-58" y1="52" x2="58" y2="52" stroke="{P.fg}" stroke-width="3" stroke-linecap="round"/>'
    for k in range(3):
        s += (f'<circle cx="30" cy="-48" r="5" fill="{P.rule}" opacity="0">'
              f'<animate attributeName="cy" values="-48;-76" dur="2.7s" begin="{k * 0.9:.1f}s" {R}/>'
              f'<animate attributeName="r" values="4;10" dur="2.7s" begin="{k * 0.9:.1f}s" {R}/>'
              f'<animate attributeName="opacity" values="0.9;0" dur="2.7s" begin="{k * 0.9:.1f}s" {R}/></circle>')
    s += f'<rect x="24" y="-44" width="13" height="24" fill="{P.fg}"/>'
    s += f'<path d="M-54,-2 L0,-46 L54,-2 Z" fill="{P.acc}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    s += f'<rect x="-42" y="-4" width="84" height="56" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<rect x="-10" y="20" width="20" height="32" rx="2" fill="{P.sec}"/>'
    for k, wx in enumerate((-34, 16)):
        s += f'<rect x="{wx}" y="6" width="18" height="16" fill="{P.rule}" stroke="{P.fg}" stroke-width="2"/>'
        s += (f'<rect x="{wx}" y="6" width="18" height="16" fill="{P.gold}" stroke="{P.fg}" stroke-width="2">'
              f'<animate attributeName="opacity" values="1;1;0.15;1" keyTimes="0;0.6;0.7;1" dur="{3 + k}s" {R}/></rect>')
    return s


def i_building(P):
    s = f'<line x1="-58" y1="56" x2="58" y2="56" stroke="{P.fg}" stroke-width="3" stroke-linecap="round"/>'
    s += f'<rect x="20" y="-14" width="36" height="70" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<rect x="-40" y="-50" width="64" height="106" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<line x1="-8" y1="-50" x2="-8" y2="-66" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<circle cx="-8" cy="-68" r="4" fill="{P.acc}"><animate attributeName="opacity" values="1;0.2;1" dur="1.2s" {R}/></circle>'
    seq = [3, 9, 1, 14, 6, 11, 0, 16, 8, 4, 13, 2, 10, 7, 15, 5, 12, 17, 19, 18]
    k = 0
    for r in range(5):
        for c in range(4):
            x, y = -32 + c * 14, -40 + r * 18
            s += f'<rect x="{x}" y="{y}" width="9" height="11" fill="{P.rule}"/>'
            st = seq[k % len(seq)] / 20
            s += (f'<rect x="{x}" y="{y}" width="9" height="11" fill="{P.gold}" opacity="0">'
                  f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{st * 0.8:.2f};{st * 0.8 + 0.03:.2f};0.9;1" dur="6s" {R}/></rect>')
            k += 1
    for r in range(3):
        s += f'<rect x="28" y="{-2 + r * 18}" width="20" height="9" fill="{P.white}" stroke="{P.fg}" stroke-width="1.5"/>'
    return s


# ---------------------------------------------------------------- 荣誉与财富
def i_medal(P):
    m = (f'<polygon points="-22,-56 -7,-56 7,8 -8,10" fill="{P.sec}"/>'
         f'<polygon points="7,-56 22,-56 8,10 -7,8" fill="{P.acc}"/>'
         f'<circle cx="0" cy="34" r="30" fill="{P.gold}" stroke="{P.gold_d}" stroke-width="3"/>'
         f'<circle cx="0" cy="34" r="21" fill="none" stroke="{P.gold_l}" stroke-width="2"/>'
         f'<path d="M0,20 L4,30 L15,30 L6,37 L9,48 L0,41 L-9,48 L-6,37 L-15,30 L-4,30 Z" fill="#FFF3D6"/>')
    s = f'<g><animateTransform attributeName="transform" type="rotate" values="-6 0 -56;6 0 -56;-6 0 -56" dur="3.2s" {R}/>{m}</g>'
    s += f'<rect x="-28" y="-62" width="56" height="9" rx="4" fill="{P.fg}"/>'
    return s


def i_trophy(P):
    s = (f'<path d="M-30,-36 C-54,-36 -54,-4 -24,0" fill="none" stroke="{P.gold}" stroke-width="7" stroke-linecap="round"/>'
         f'<path d="M30,-36 C54,-36 54,-4 24,0" fill="none" stroke="{P.gold}" stroke-width="7" stroke-linecap="round"/>'
         f'<path d="M-34,-44 H34 V-22 C34,4 18,18 0,20 C-18,18 -34,4 -34,-22 Z" fill="{P.gold}" stroke="{P.gold_d}" stroke-width="3" stroke-linejoin="round"/>'
         f'<rect x="-22" y="-38" width="6" height="36" rx="3" fill="#FFF3D6" opacity="0.75"/>'
         f'<rect x="-6" y="20" width="12" height="14" fill="{P.gold_d}"/>'
         f'<rect x="-24" y="34" width="48" height="10" rx="3" fill="{P.fg}"/>'
         f'<rect x="-32" y="44" width="64" height="11" rx="3" fill="{P.fg}"/>')
    s += sparkle(-46, -50, P.gold, 0.0) + sparkle(48, -24, P.gold, 0.8, s=0.8) + sparkle(44, 34, P.acc_l, 1.6, s=0.7)
    return s


def i_star(P):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 42 if k % 2 == 0 else 18
        pts.append((r * math.cos(a), r * math.sin(a) + 4))
    star = f'<polygon points="{_pts(pts)}" fill="{P.gold}" stroke="{P.gold_d}" stroke-width="3" stroke-linejoin="round"/>'
    s = ring_pulse(0, 4, P.gold, 30, 58, 2.4)
    s += f'<g><animateTransform attributeName="transform" type="rotate" values="-8 0 4;8 0 4;-8 0 4" dur="3s" {R}/>{star}</g>'
    s += sparkle(-48, -40, P.gold, 0.3, s=0.8) + sparkle(50, -30, P.acc_l, 1.1, s=0.7) + sparkle(42, 46, P.gold, 1.8, s=0.6)
    return s


def i_crown(P):
    c = (f'<path d="M-50,26 L-54,-22 L-26,2 L0,-34 L26,2 L54,-22 L50,26 Z" fill="{P.gold}" stroke="{P.gold_d}" stroke-width="3" stroke-linejoin="round"/>'
         f'<rect x="-50" y="22" width="100" height="16" rx="3" fill="{P.gold_d}"/>'
         f'<circle cx="-26" cy="30" r="4.5" fill="{P.sec}"/><circle cx="0" cy="30" r="5.5" fill="{P.acc}"/><circle cx="26" cy="30" r="4.5" fill="{P.sec}"/>'
         f'<circle cx="0" cy="-34" r="5" fill="{P.acc}"/><circle cx="-54" cy="-22" r="4" fill="{P.acc}"/><circle cx="54" cy="-22" r="4" fill="{P.acc}"/>')
    s = f'<g><animateTransform attributeName="transform" type="translate" values="0 2;0 -5;0 2" dur="2.4s" {R}/>{c}</g>'
    s += sparkle(-40, -48, P.gold, 0.2, s=0.8) + sparkle(42, -52, P.gold, 1.2, s=0.9)
    return s


def i_money(P):
    s = ''
    for k in range(5):
        y = 40 - k * 13
        f0 = 0.05 + k * 0.12
        coin = (f'<rect x="-50" y="{y - 1}" width="56" height="10" fill="{P.gold_d}"/>'
                f'<ellipse cx="-22" cy="{y + 9}" rx="28" ry="8" fill="{P.gold_d}"/>'
                f'<ellipse cx="-22" cy="{y - 1}" rx="28" ry="8" fill="{P.gold}" stroke="{P.gold_d}" stroke-width="2"/>')
        s += (f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{f0:.2f};{f0 + 0.05:.2f};0.9;1" dur="5s" {R}/>'
              f'<animateTransform attributeName="transform" type="translate" values="0 -18;0 -18;0 0;0 0;0 0" keyTimes="0;{f0:.2f};{f0 + 0.05:.2f};0.9;1" dur="5s" {R}/>{coin}</g>')
    s += (f'<ellipse cx="34" cy="-22" rx="22" ry="22" fill="{P.gold}" stroke="{P.gold_d}" stroke-width="3">'
          f'<animate attributeName="rx" values="22;3;22" dur="1.6s" {R}/></ellipse>')
    s += (f'<ellipse cx="34" cy="-22" rx="13" ry="13" fill="none" stroke="{P.gold_l}" stroke-width="2.5">'
          f'<animate attributeName="rx" values="13;1.5;13" dur="1.6s" {R}/></ellipse>')
    return s


def i_chart(P, down=False):
    s = f'<path d="M-52,-48 V44 H58" fill="none" stroke="{P.fg}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    hs = (22, 34, 30, 52, 70) if not down else (70, 56, 60, 36, 22)
    for k, h in enumerate(hs):
        s += f'<rect x="{-42 + k * 20}" y="{40 - h}" width="13" height="{h}" fill="{P.acc_p}"/>'
    pts = [(-40, 22), (-20, 8), (0, 14), (22, -12), (46, -38)]
    if down:
        pts = [(-40, -36), (-20, -22), (0, -28), (22, 0), (46, 26)]
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    col = P.acc
    s += (f'<polyline points="{_pts(pts)}" fill="none" stroke="{col}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" '
          f'stroke-dasharray="{L:.1f} {L:.1f}" stroke-dashoffset="{L:.1f}">'
          f'<animate attributeName="stroke-dashoffset" values="{L:.1f};0;0;{L:.1f}" keyTimes="0;0.45;0.9;1" dur="4s" {R}/></polyline>')
    ex, ey = pts[-1]
    s += (f'<circle cx="{ex}" cy="{ey}" r="6" fill="{col}" opacity="0">'
          f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.44;0.46;0.9;1" dur="4s" {R}/></circle>')
    s += ring_pulse(ex, ey, col, 6, 18, 2.0)
    return s


def i_chart_down(P):
    return i_chart(P, down=True)


# ---------------------------------------------------------------- 表达与创作
def i_mic(P):
    s = ''
    for k, r in enumerate((26, 40)):
        for side in (-1, 1):
            a0, a1 = (-40, 40) if side > 0 else (140, 220)
            x0, y0 = r * math.cos(math.radians(a0)), -18 + r * math.sin(math.radians(a0))
            x1, y1 = r * math.cos(math.radians(a1)), -18 + r * math.sin(math.radians(a1))
            s += (f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{P.acc_l}" stroke-width="3" stroke-linecap="round" opacity="0">'
                  f'<animate attributeName="opacity" values="0;1;0" dur="1.6s" begin="{k * 0.4:.1f}s" {R}/></path>')
    s += f'<rect x="-15" y="-52" width="30" height="54" rx="15" fill="{P.fg}"/>'
    for y in (-40, -30, -20):
        s += f'<line x1="-9" y1="{y}" x2="9" y2="{y}" stroke="{P.mute}" stroke-width="2"/>'
    s += f'<path d="M-26,-14 V-4 C-26,22 26,22 26,-4 V-14" fill="none" stroke="{P.fg}" stroke-width="4" stroke-linecap="round"/>'
    s += f'<line x1="0" y1="16" x2="0" y2="42" stroke="{P.fg}" stroke-width="4"/>'
    s += f'<rect x="-22" y="42" width="44" height="8" rx="4" fill="{P.fg}"/>'
    return s


def i_pen(P):
    s = f'<rect x="-58" y="-46" width="116" height="92" rx="6" fill="{P.white}" stroke="{P.rule}" stroke-width="2"/>'
    for y in (-26, 30):
        s += f'<line x1="-46" y1="{y}" x2="46" y2="{y}" stroke="{P.rule}" stroke-width="1.5"/>'
    segs = [((-42, 14), (-32, -14), (-18, -14), (-16, 6)), ((-16, 6), (-14, 26), (-2, 22), (4, 2)),
            ((4, 2), (8, -12), (18, -12), (20, 6)), ((20, 6), (22, 20), (34, 20), (44, -4))]
    d = f'M{segs[0][0][0]},{segs[0][0][1]} ' + ' '.join(f'C{a[0]},{a[1]} {b[0]},{b[1]} {c[0]},{c[1]}' for (_, a, b, c) in segs)
    L = sum(_bez_len(*sg) for sg in segs)
    s += (f'<path d="{d}" fill="none" stroke="{P.acc}" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="{L:.1f} {L:.1f}" stroke-dashoffset="{L:.1f}">'
          f'<animate attributeName="stroke-dashoffset" values="{L:.1f};0;0;{L:.1f}" keyTimes="0;0.6;0.92;1" dur="3.6s" {R}/></path>')
    pen = (f'<polygon points="0,0 5,-13 30,-38 38,-30 13,-5" fill="{P.fg}" stroke="{P.fg}" stroke-width="1.5" stroke-linejoin="round"/>'
           f'<polygon points="0,0 5,-13 13,-5" fill="{P.gold}"/>'
           f'<line x1="24" y1="-32" x2="32" y2="-24" stroke="{P.acc_l}" stroke-width="3"/>')
    s += (f'<g><animateMotion path="{d}" keyPoints="0;1;1;0" keyTimes="0;0.6;0.92;1" calcMode="linear" dur="3.6s" {R}/>{pen}</g>')
    return s


def i_brush(P):
    s = (f'<path d="M-52,10 C-60,-26 -16,-48 18,-36 C44,-28 46,-6 30,0 C18,4 20,16 30,22 C40,30 22,46 -6,44 C-30,42 -48,30 -52,10 Z" '
         f'fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
         f'<ellipse cx="14" cy="12" rx="8" ry="6" fill="{P.bg}" stroke="{P.fg}" stroke-width="2"/>')
    for k, (x, y, c) in enumerate(((-32, -10, P.acc), (-14, -26, P.sec), (8, -24, P.gold), (-34, 16, P.fg))):
        s += (f'<circle cx="{x}" cy="{y}" r="7" fill="{c}"><animate attributeName="r" values="7;8.5;7" dur="2s" begin="{k * 0.5:.1f}s" {R}/></circle>')
    sw = 'M-40,56 C-16,40 10,62 54,42'
    L = _bez_len((-40, 56), (-16, 40), (10, 62), (54, 42))
    s += (f'<path d="{sw}" fill="none" stroke="{P.acc}" stroke-width="7" stroke-linecap="round" stroke-dasharray="{L:.1f} {L:.1f}" stroke-dashoffset="{L:.1f}">'
          f'<animate attributeName="stroke-dashoffset" values="{L:.1f};0;0;{L:.1f}" keyTimes="0;0.4;0.9;1" dur="3.4s" {R}/></path>')
    s += (f'<g transform="rotate(35 40 -20)"><rect x="36" y="-58" width="8" height="40" rx="3" fill="{P.fg}"/>'
          f'<rect x="35" y="-20" width="10" height="8" fill="{P.mute}"/><path d="M35,-12 H45 L40,4 Z" fill="{P.acc}"/></g>')
    return s


def i_camera(P):
    s = f'<rect x="-24" y="-42" width="40" height="16" rx="4" fill="{P.fg}"/>'
    s += f'<rect x="-58" y="-30" width="116" height="74" rx="12" fill="{P.fg}"/>'
    s += f'<circle cx="0" cy="8" r="28" fill="{P.panel2 if not P.dark else P.panel}" stroke="{P.white}" stroke-width="3"/>'
    s += f'<circle cx="0" cy="8" r="17" fill="{P.panel}"/>'
    s += (f'<circle cx="0" cy="8" r="11" fill="none" stroke="{P.sec}" stroke-width="3" stroke-dasharray="6 5">'
          f'<animateTransform attributeName="transform" type="rotate" from="0 0 8" to="360 0 8" dur="4s" {R}/></circle>')
    s += f'<circle cx="-6" cy="2" r="4" fill="{P.white}" opacity="0.7"/>'
    s += f'<rect x="34" y="-22" width="14" height="8" rx="2" fill="{P.gold}"/>'
    s += (f'<circle cx="41" cy="-18" r="4" fill="#FFFFFF" opacity="0">'
          f'<animate attributeName="r" values="4;4;46;56" keyTimes="0;0.8;0.88;1" dur="2.6s" {R}/>'
          f'<animate attributeName="opacity" values="0;0;0.9;0" keyTimes="0;0.8;0.84;1" dur="2.6s" {R}/></circle>')
    return s


def i_film(P):
    s = ''
    for cx in (-28, 28):
        s += f'<g transform="translate({cx} -18)"><circle r="26" fill="{P.fg}"/><g>'
        s += f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="3s" {R}/>'
        for k in range(5):
            a = 2 * math.pi * k / 5
            s += f'<circle cx="{14 * math.cos(a):.1f}" cy="{14 * math.sin(a):.1f}" r="5.5" fill="{P.bg}"/>'
        s += f'</g><circle r="4" fill="{P.acc_l}"/></g>'
    s += f'<rect x="-58" y="20" width="116" height="30" rx="3" fill="{P.fg}"/>'
    s += (f'<line x1="-56" y1="25" x2="56" y2="25" stroke="{P.bg}" stroke-width="4" stroke-dasharray="6 6">'
          f'<animate attributeName="stroke-dashoffset" values="0;-12" dur="0.6s" {R}/></line>')
    s += (f'<line x1="-56" y1="45" x2="56" y2="45" stroke="{P.bg}" stroke-width="4" stroke-dasharray="6 6">'
          f'<animate attributeName="stroke-dashoffset" values="0;-12" dur="0.6s" {R}/></line>')
    for k, x in enumerate((-46, -14, 18)):
        s += (f'<rect x="{x}" y="30" width="26" height="10" rx="2" fill="{P.acc_l}" opacity="0.4">'
              f'<animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" begin="{k * 0.5:.1f}s" {R}/></rect>')
    return s


def i_music(P):
    s = ''
    for y in (-20, -6, 8, 22, 36):
        s += f'<line x1="-58" y1="{y}" x2="58" y2="{y}" stroke="{P.rule}" stroke-width="1.5"/>'
    pair = (f'<ellipse cx="-36" cy="30" rx="10" ry="7.5" fill="{P.fg}" transform="rotate(-20 -36 30)"/>'
            f'<ellipse cx="-4" cy="22" rx="10" ry="7.5" fill="{P.fg}" transform="rotate(-20 -4 22)"/>'
            f'<path d="M-27,28 V-26 L5,-34 V20" fill="none" stroke="{P.fg}" stroke-width="3.5"/>'
            f'<path d="M-27,-26 L5,-34 V-24 L-27,-16 Z" fill="{P.fg}"/>')
    s += f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -8;0 0" dur="1.2s" {R}/>{pair}</g>'
    one = (f'<ellipse cx="34" cy="14" rx="10" ry="7.5" fill="{P.acc}" transform="rotate(-20 34 14)"/>'
           f'<path d="M43,12 V-40 Q54,-30 58,-18" fill="none" stroke="{P.acc}" stroke-width="3.5" stroke-linecap="round"/>')
    s += f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -10;0 0" dur="1.2s" begin="0.6s" {R}/>{one}</g>'
    return s


def i_chat(P):
    bx0, by0, bw, bh = -62, -40, 124, 66
    bub = (f'M{bx0 + 16},{by0} H{bx0 + bw - 16} Q{bx0 + bw},{by0} {bx0 + bw},{by0 + 16} V{by0 + bh - 16} Q{bx0 + bw},{by0 + bh} {bx0 + bw - 16},{by0 + bh} '
           f'H{bx0 + 52} L{bx0 + 26},{by0 + bh + 18} L{bx0 + 32},{by0 + bh} H{bx0 + 16} Q{bx0},{by0 + bh} {bx0},{by0 + bh - 16} V{by0 + 16} Q{bx0},{by0} {bx0 + 16},{by0} Z')
    s = f'<path d="{bub}" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    dots = ''
    for k in range(3):
        dots += (f'<circle cx="{-22 + k * 22}" cy="-7" r="6.5" fill="{P.mute}">'
                 f'<animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" begin="{k * 0.2:.1f}s" {R}/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 2;0 -4;0 2" dur="1.2s" begin="{k * 0.2:.1f}s" {R}/></circle>')
    s += f'<g><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1" dur="5s" {R}/>{dots}</g>'
    lines = ''
    for k, w in enumerate((92, 64)):
        lines += (f'<rect x="-46" y="{-20 + k * 18}" width="{w}" height="9" rx="4.5" fill="{P.acc_l if k == 0 else P.acc_p}">'
                  f'<animate attributeName="width" values="0;0;{w};{w}" keyTimes="0;{0.5 + k * 0.08:.2f};{0.62 + k * 0.08:.2f};1" dur="5s" {R}/></rect>')
    s += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.49;0.5;0.95;1" dur="5s" {R}/>{lines}</g>'
    return s


def i_phone(P):
    s = f'<rect x="-34" y="-60" width="68" height="120" rx="13" fill="{P.fg}"/>'
    s += f'<rect x="-28" y="-50" width="56" height="96" rx="6" fill="{P.white}"/>'
    s += f'<rect x="-8" y="50" width="16" height="4" rx="2" fill="{P.mute}"/>'
    rows = [(-22, -42, 36, P.acc_p), (-6, -26, 30, P.acc_l), (-22, -10, 40, P.acc_p), (-6, 6, 26, P.acc_l)]
    for k, (x, y, w, c) in enumerate(rows):
        f0 = 0.08 + k * 0.17
        s += (f'<rect x="{x}" y="{y}" width="{w}" height="12" rx="6" fill="{c}" opacity="0">'
              f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{f0:.2f};{f0 + 0.04:.2f};0.92;1" dur="5s" {R}/></rect>')
    heart = 'M0,8 C-10,2 -12,-6 -6,-9 C-3,-10 -1,-8 0,-6 C1,-8 3,-10 6,-9 C12,-6 10,2 0,8 Z'
    s += (f'<g transform="translate(14 32)"><path d="{heart}" fill="{P.acc}">'
          f'<animateTransform attributeName="transform" type="scale" values="0;0;1.3;1;1;0" keyTimes="0;0.74;0.8;0.86;0.92;1" dur="5s" {R}/></path></g>')
    return s


def i_letter(P):
    s = f'<rect x="-54" y="-10" width="108" height="64" rx="4" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3"/>'
    paper = (f'<rect x="-40" y="-42" width="80" height="70" rx="3" fill="{P.white}" stroke="{P.fg}" stroke-width="2.5"/>'
             + ''.join(f'<line x1="-30" y1="{-30 + k * 11}" x2="{30 - (k % 2) * 14}" y2="{-30 + k * 11}" stroke="{P.mute}" stroke-width="2.5" stroke-linecap="round"/>' for k in range(4)))
    s += f'<g><animateTransform attributeName="transform" type="translate" values="0 22;0 -14;0 -14;0 22" keyTimes="0;0.35;0.75;1" dur="4s" {R}/>{paper}</g>'
    s += f'<path d="M-54,-10 L0,26 L54,-10 V54 H-54 Z" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    s += f'<path d="M-54,54 L-12,18 M54,54 L12,18" stroke="{P.fg}" stroke-width="2.5" opacity="0.5"/>'
    s += f'<circle cx="0" cy="30" r="8" fill="{P.acc}"/>'
    return s


def i_newspaper(P):
    s = f'<rect x="-48" y="-50" width="106" height="94" rx="3" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="2.5"/>'
    s += f'<rect x="-58" y="-42" width="106" height="94" rx="3" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<rect x="-48" y="-34" width="86" height="9" fill="{P.fg}"/>'
    s += (f'<rect x="-50" y="-19" width="0" height="14" fill="{P.acc_l}" opacity="0.45">'
          f'<animate attributeName="width" values="0;0;90;90;0" keyTimes="0;0.15;0.45;0.9;1" dur="4s" {R}/></rect>')
    s += f'<rect x="-48" y="-16" width="86" height="8" rx="1" fill="{P.fg2 if not P.dark else P.fg}"/>'
    s += f'<rect x="-48" y="0" width="38" height="30" fill="{P.rule}"/>'
    s += f'<path d="M-46,28 L-34,14 L-26,22 L-20,16 L-12,28 Z" fill="{P.mute}"/>'
    for k in range(5):
        s += f'<line x1="-4" y1="{3 + k * 7}" x2="38" y2="{3 + k * 7}" stroke="{P.mute}" stroke-width="2.2" stroke-linecap="round"/>'
    for k in range(2):
        s += f'<line x1="-48" y1="{38 + k * 7}" x2="38" y2="{38 + k * 7}" stroke="{P.mute}" stroke-width="2.2" stroke-linecap="round"/>'
    return s


def i_calendar(P):
    s = f'<rect x="-50" y="-40" width="100" height="92" rx="8" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<path d="M-50,-18 V-32 Q-50,-40 -42,-40 H42 Q50,-40 50,-32 V-18 Z" fill="{P.acc}"/>'
    s += f'<line x1="-50" y1="-18" x2="50" y2="-18" stroke="{P.fg}" stroke-width="3"/>'
    for x in (-26, 26):
        s += f'<rect x="{x - 4}" y="-50" width="8" height="18" rx="4" fill="{P.fg}"/>'
    cells = []
    for r in range(4):
        for c in range(5):
            x, y = -40 + c * 17, -10 + r * 15
            cells.append((x, y))
            s += f'<rect x="{x}" y="{y}" width="12" height="10" rx="2" fill="{P.rule}"/>'
    order = [6, 7, 8, 12, 13, 17]
    xs = ';'.join(str(cells[i][0] - 2) for i in order)
    ys = ';'.join(str(cells[i][1] - 2) for i in order)
    s += (f'<rect x="{cells[order[0]][0] - 2}" y="{cells[order[0]][1] - 2}" width="16" height="14" rx="3" fill="none" stroke="{P.acc}" stroke-width="3">'
          f'<animate attributeName="x" values="{xs}" dur="4.2s" calcMode="discrete" {R}/>'
          f'<animate attributeName="y" values="{ys}" dur="4.2s" calcMode="discrete" {R}/></rect>')
    return s


def i_clock(P):
    s = f'<circle cx="0" cy="0" r="48" fill="{P.white}" stroke="{P.fg}" stroke-width="4"/>'
    for k in range(12):
        a = 2 * math.pi * k / 12
        r0 = 36 if k % 3 else 32
        s += (f'<line x1="{r0 * math.cos(a):.1f}" y1="{r0 * math.sin(a):.1f}" x2="{41 * math.cos(a):.1f}" y2="{41 * math.sin(a):.1f}" '
              f'stroke="{P.fg}" stroke-width="{3 if k % 3 == 0 else 2}" stroke-linecap="round"/>')
    s += (f'<line x1="0" y1="0" x2="0" y2="-22" stroke="{P.fg}" stroke-width="5" stroke-linecap="round">'
          f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="18s" {R}/></line>')
    s += (f'<line x1="0" y1="6" x2="0" y2="-34" stroke="{P.acc}" stroke-width="3" stroke-linecap="round">'
          f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="3s" {R}/></line>')
    s += f'<circle cx="0" cy="0" r="5" fill="{P.acc}"/>'
    return s


# ---------------------------------------------------------------- 人与生活
def i_people(P):
    s = ring_pulse(0, -8, P.acc_l, 30, 56, 2.6)

    def bust(x, y, sc, fill):
        return (f'<g transform="translate({x} {y}) scale({sc})"><circle cx="0" cy="-20" r="15" fill="{fill}" stroke="{P.fg}" stroke-width="3"/>'
                f'<path d="M-28,28 C-28,0 28,0 28,28 Z" fill="{fill}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/></g>')
    s += bust(-38, 14, 0.8, P.acc_p) + bust(38, 14, 0.8, P.acc_p) + bust(0, 4, 1.05, P.acc)
    return s


def i_heart(P):
    hp = 'M0,30 C-40,6 -44,-26 -22,-34 C-10,-38 -2,-30 0,-22 C2,-30 10,-38 22,-34 C44,-26 40,6 0,30 Z'
    s = ring_pulse(0, -2, P.acc_l, 30, 58, 1.4)
    s += (f'<g><animateTransform attributeName="transform" type="scale" values="1;1.12;1;1.06;1;1" keyTimes="0;0.12;0.24;0.36;0.5;1" dur="1.4s" {R}/>'
          f'<path d="{hp}" fill="{P.acc}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
          f'<path d="M-24,-20 Q-26,-30 -16,-30" fill="none" stroke="{P.white}" stroke-width="4" stroke-linecap="round" opacity="0.7"/></g>')
    return s


def i_ecg(P):
    s = f'<rect x="-60" y="-46" width="120" height="82" rx="10" fill="{P.panel}" stroke="{P.fg}" stroke-width="3"/>'
    for y in (-26, -6, 14):
        s += f'<line x1="-52" y1="{y}" x2="52" y2="{y}" stroke="#2A3242" stroke-width="1.5"/>'
    pts = [(-52, 0), (-28, 0), (-22, -8), (-16, 0), (-10, 0), (-5, 14), (2, -30), (8, 18), (13, 0), (24, 0), (30, -6), (36, 0), (52, 0)]
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    s += f'<polyline points="{_pts(pts)}" fill="none" stroke="#2F5A4A" stroke-width="2.5" stroke-linejoin="round"/>'
    s += (f'<polyline points="{_pts(pts)}" fill="none" stroke="#7CE38B" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" '
          f'stroke-dasharray="46 {L:.0f}"><animate attributeName="stroke-dashoffset" values="46;-{L:.0f}" dur="1.8s" {R}/></polyline>')
    s += f'<rect x="-14" y="36" width="28" height="12" fill="{P.fg}"/><rect x="-30" y="48" width="60" height="7" rx="3" fill="{P.fg}"/>'
    return s


def i_candle(P):
    s = (f'<circle cx="0" cy="-30" r="30" fill="{P.gold}" opacity="0.18">'
         f'<animate attributeName="r" values="26;32;26" dur="1.8s" {R}/>'
         f'<animate attributeName="opacity" values="0.14;0.26;0.14" dur="1.8s" {R}/></circle>')
    s += f'<ellipse cx="0" cy="52" rx="34" ry="7" fill="{P.fg}"/>'
    s += f'<rect x="-15" y="-10" width="30" height="62" rx="4" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<path d="M-15,-2 Q-6,8 0,-2 Q4,14 15,-2" fill="none" stroke="{P.rule}" stroke-width="2.5"/>'
    s += f'<line x1="0" y1="-10" x2="0" y2="-18" stroke="{P.fg}" stroke-width="2.5"/>'
    f1 = 'M0,-50 C8,-38 10,-26 0,-18 C-10,-26 -8,-38 0,-50 Z'
    f2 = 'M2,-48 C10,-36 9,-25 0,-18 C-9,-25 -7,-38 2,-48 Z'
    f3 = 'M-2,-52 C7,-39 10,-26 0,-18 C-10,-26 -9,-37 -2,-52 Z'
    s += f'<path d="{f1}" fill="{P.gold}"><animate attributeName="d" values="{f1};{f2};{f3};{f1}" dur="0.9s" {R}/></path>'
    s += f'<path d="M0,-38 C4,-31 4,-25 0,-21 C-4,-25 -4,-31 0,-38 Z" fill="{P.acc_l}"/>'
    return s


def i_cake(P):
    s = f'<ellipse cx="0" cy="48" rx="58" ry="9" fill="{P.rule}"/>'
    s += f'<rect x="-46" y="10" width="92" height="36" rx="6" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<rect x="-34" y="-14" width="68" height="26" rx="5" fill="{P.white}" stroke="{P.fg}" stroke-width="3"/>'
    s += f'<path d="M-46,18 Q-38,28 -30,18 Q-22,28 -14,18 Q-6,28 2,18 Q10,28 18,18 Q26,28 34,18 Q40,26 46,18 V14 H-46 Z" fill="{P.acc_l}"/>'
    for k, x in enumerate((-20, 0, 20)):
        s += f'<rect x="{x - 3}" y="-36" width="6" height="22" rx="2" fill="{(P.sec, P.acc, P.sec)[k]}"/>'
        f1 = f'M{x},-50 C{x + 5},-44 {x + 5},-40 {x},-37 C{x - 5},-40 {x - 5},-44 {x},-50 Z'
        f2 = f'M{x + 1.5},-48 C{x + 6},-43 {x + 4},-39 {x},-37 C{x - 4},-40 {x - 4},-44 {x + 1.5},-48 Z'
        s += f'<path d="{f1}" fill="{P.gold}"><animate attributeName="d" values="{f1};{f2};{f1}" dur="{0.7 + k * 0.15:.2f}s" {R}/></path>'
    return s


def i_coffee(P):
    s = f'<ellipse cx="0" cy="52" rx="60" ry="9" fill="{P.bg}" stroke="{P.fg}" stroke-width="3"/>'
    for k, sx in enumerate((-18, 0, 18)):
        s += (f'<path d="M{sx},-20 c-8,-7 8,-12 0,-19 c-8,-7 8,-11 0,-18" fill="none" stroke="{P.mute}" stroke-width="3" stroke-linecap="round" opacity="0">'
              f'<animate attributeName="opacity" values="0;0.9;0" dur="2.4s" begin="{k * 0.8:.1f}s" {R}/>'
              f'<animateTransform attributeName="transform" type="translate" values="0 6;0 -6" dur="2.4s" begin="{k * 0.8:.1f}s" {R}/></path>')
    s += f'<path d="M40,2 h10 a15,15 0 0 1 0,30 h-10" fill="none" stroke="{P.fg}" stroke-width="4.5"/>'
    s += f'<rect x="-40" y="-14" width="80" height="62" rx="12" fill="{P.white}" stroke="{P.fg}" stroke-width="4.5"/>'
    s += f'<rect x="-38" y="6" width="76" height="11" fill="{P.acc_p}"/>'
    return s


def i_dumbbell(P):
    bars = (f'<line x1="-60" y1="0" x2="60" y2="0" stroke="{P.fg}" stroke-width="5" stroke-linecap="round"/>'
            f'<rect x="-52" y="-29" width="13" height="58" rx="3" fill="{P.fg}"/><rect x="-37" y="-20" width="10" height="40" rx="3" fill="{P.acc}"/>'
            f'<rect x="39" y="-29" width="13" height="58" rx="3" fill="{P.fg}"/><rect x="27" y="-20" width="10" height="40" rx="3" fill="{P.acc}"/>')
    s = f'<g><animateTransform attributeName="transform" type="translate" values="0 14;0 -6;0 14" dur="1.8s" {R}/>{bars}</g>'
    s += f'<ellipse cx="0" cy="50" rx="44" ry="6" fill="{P.rule}" opacity="0.7"/>'
    return s


def i_ball(P):
    s = (f'<ellipse cx="0" cy="54" rx="26" ry="6" fill="{P.fg}" opacity="0.2">'
         f'<animate attributeName="rx" values="26;12;26" keyTimes="0;0.5;1" dur="1.2s" calcMode="spline" keySplines="0.2 0.6 0.4 1;0.6 0 0.8 0.4" {R}/></ellipse>')
    ball = (f'<circle r="27" fill="{P.acc_l}" stroke="{P.fg}" stroke-width="3"/>'
            f'<path d="M-27,0 H27 M0,-27 V27 M-19,-19 Q-1,0 -19,19 M19,-19 Q1,0 19,19" fill="none" stroke="{P.fg}" stroke-width="2.4"/>')
    s += (f'<g><animateTransform attributeName="transform" type="translate" values="0 24;0 -26;0 24" keyTimes="0;0.5;1" dur="1.2s" '
          f'calcMode="spline" keySplines="0.2 0.6 0.4 1;0.6 0 0.8 0.4" {R}/><g>'
          f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="2.4s" {R}/>{ball}</g></g>')
    return s


def i_briefcase(P):
    case = (f'<path d="M-16,-30 V-38 Q-16,-44 -10,-44 H10 Q16,-44 16,-38 V-30" fill="none" stroke="{P.fg}" stroke-width="5"/>'
            f'<rect x="-52" y="-30" width="104" height="70" rx="9" fill="{P.acc}" stroke="{P.fg}" stroke-width="3"/>'
            f'<line x1="-52" y1="-4" x2="52" y2="-4" stroke="{P.fg}" stroke-width="3"/>'
            f'<rect x="-9" y="-10" width="18" height="13" rx="2" fill="{P.gold}" stroke="{P.fg}" stroke-width="2.5"/>')
    s = f'<g><animateTransform attributeName="transform" type="translate" values="0 2;0 -4;0 2" dur="2s" {R}/>{case}'
    s += (f'<g><animateTransform attributeName="transform" type="rotate" values="-14 12 -40;14 12 -40;-14 12 -40" dur="2s" {R}/>'
          f'<line x1="12" y1="-40" x2="20" y2="-18" stroke="{P.fg}" stroke-width="2"/><rect x="14" y="-18" width="14" height="18" rx="2" fill="{P.white}" stroke="{P.fg}" stroke-width="2"/></g></g>')
    s += f'<ellipse cx="0" cy="52" rx="46" ry="6" fill="{P.rule}" opacity="0.7"/>'
    return s


def i_flag(P):
    s = (f'<path d="M-60,52 L-12,-18 L8,10 L22,-6 L60,52 Z" fill="{P.acc_p}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
         f'<path d="M-24,0 L-12,-18 L-1,-2 L-8,4 L-14,-2 Z" fill="{P.white}"/>'
         f'<line x1="-12" y1="-18" x2="-12" y2="-62" stroke="{P.fg}" stroke-width="3" stroke-linecap="round"/>')
    d1 = 'M-12,-62 Q2,-68 14,-62 T40,-62 V-40 Q28,-46 14,-40 T-12,-40 Z'
    d2 = 'M-12,-62 Q2,-56 14,-62 T40,-62 V-40 Q28,-34 14,-40 T-12,-40 Z'
    s += f'<path d="{d1}" fill="{P.acc}"><animate attributeName="d" values="{d1};{d2};{d1}" dur="1.4s" {R}/></path>'
    return s


def i_rocket(P):
    s = ''
    for k, x in enumerate((-40, 36, -24, 46)):
        s += (f'<line x1="{x}" y1="-40" x2="{x}" y2="-24" stroke="{P.rule}" stroke-width="3" stroke-linecap="round">'
              f'<animateTransform attributeName="transform" type="translate" values="0 -20;0 90" dur="{1.1 + k * 0.2:.1f}s" begin="{k * 0.3:.1f}s" {R}/>'
              f'<animate attributeName="opacity" values="0;1;0" dur="{1.1 + k * 0.2:.1f}s" begin="{k * 0.3:.1f}s" {R}/></line>')
    f1, f2 = 'M-10,30 Q0,68 10,30 Z', 'M-8,30 Q0,52 8,30 Z'
    g1, g2 = 'M-5,30 Q0,50 5,30 Z', 'M-4,30 Q0,42 4,30 Z'
    body = (f'<path d="{f1}" fill="{P.acc_l}"><animate attributeName="d" values="{f1};{f2};{f1}" dur="0.35s" {R}/></path>'
            f'<path d="{g1}" fill="{P.gold}"><animate attributeName="d" values="{g1};{g2};{g1}" dur="0.35s" {R}/></path>'
            f'<path d="M-16,8 L-32,30 L-16,26 Z M16,8 L32,30 L16,26 Z" fill="{P.acc}" stroke="{P.fg}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<path d="M0,-56 C18,-40 20,-10 16,26 L-16,26 C-20,-10 -18,-40 0,-56 Z" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
            f'<circle cx="0" cy="-14" r="9" fill="{P.sec}" stroke="{P.fg}" stroke-width="3"/>'
            f'<rect x="-11" y="25" width="22" height="7" rx="2" fill="{P.fg}"/>')
    s += f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -6;0 0" dur="1.6s" {R}/>{body}</g>'
    return s


def i_bulb(P):
    s = ''
    for k in range(7):
        a = math.radians(-180 + k * 30)
        x0, y0, x1, y1 = 44 * math.cos(a), -12 + 44 * math.sin(a), 56 * math.cos(a), -12 + 56 * math.sin(a)
        s += (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{P.gold}" stroke-width="3.5" stroke-linecap="round">'
              f'<animate attributeName="opacity" values="0.15;1;0.15" dur="1.8s" begin="{(k % 2) * 0.3:.1f}s" {R}/></line>')
    s += (f'<path d="M-20,16 C-36,2 -36,-40 0,-44 C36,-40 36,2 20,16 L18,26 L-18,26 Z" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round">'
          f'<animate attributeName="fill" values="{P.white};#FFE9AE;{P.white}" dur="1.8s" {R}/></path>')
    s += f'<path d="M-8,16 V0 C-8,-14 8,-14 8,0 V16" fill="none" stroke="{P.acc}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
    s += f'<rect x="-17" y="28" width="34" height="8" rx="2" fill="{P.mute}"/><rect x="-15" y="38" width="30" height="8" rx="2" fill="{P.mute}"/>'
    s += f'<rect x="-9" y="48" width="18" height="7" rx="3" fill="{P.fg}"/>'
    return s


def i_gear(P):
    s = (f'<g transform="translate(-14 -10)"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="6s" {R}/>'
         f'<path d="{gear_path(36, 28, 10)}" fill="{P.fg}"/><circle r="10" fill="{P.bg}"/></g></g>')
    s += (f'<g transform="translate(34 30)"><g><animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="3.6s" {R}/>'
          f'<path d="{gear_path(22, 16, 6)}" fill="{P.acc}"/><circle r="6" fill="{P.bg}"/></g></g>')
    return s


def i_flask(P):
    s = f'<path d="M-12,-50 H12 V-18 L40,36 Q44,48 32,48 H-32 Q-44,48 -40,36 L-12,-18 Z" fill="{P.white}" stroke="{P.fg}" stroke-width="3" stroke-linejoin="round"/>'
    w1 = 'M-32,12 Q-16,6 0,12 T32,12 L40,36 Q44,46 32,46 H-32 Q-44,46 -40,36 Z'
    w2 = 'M-32,12 Q-16,18 0,12 T32,12 L40,36 Q44,46 32,46 H-32 Q-44,46 -40,36 Z'
    s += f'<path d="{w1}" fill="{P.sec}" opacity="0.85"><animate attributeName="d" values="{w1};{w2};{w1}" dur="2s" {R}/></path>'
    for k, (x, r) in enumerate(((-12, 4), (6, 3), (16, 5), (-2, 3.5))):
        s += (f'<circle cx="{x}" cy="40" r="{r}" fill="{P.white}" opacity="0">'
              f'<animate attributeName="cy" values="40;6" dur="2.2s" begin="{k * 0.55:.2f}s" {R}/>'
              f'<animate attributeName="opacity" values="0;0.9;0" dur="2.2s" begin="{k * 0.55:.2f}s" {R}/></circle>')
    s += f'<rect x="-16" y="-56" width="32" height="8" rx="3" fill="{P.fg}"/>'
    return s


def i_gavel(P):
    s = f'<rect x="-50" y="40" width="64" height="14" rx="4" fill="{P.fg}"/>'
    for k, (x1, y1, x2, y2) in enumerate(((-58, 28, -66, 20), (-40, 22, -40, 10), (-20, 28, -12, 20))):
        s += (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{P.acc}" stroke-width="3" stroke-linecap="round" opacity="0">'
              f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.16;0.2;0.34;1" dur="2s" {R}/></line>')
    gav = (f'<line x1="-12" y1="4" x2="48" y2="4" stroke="{P.acc}" stroke-width="7" stroke-linecap="round"/>'
           f'<rect x="-34" y="-16" width="24" height="40" rx="5" fill="{P.fg}"/>'
           f'<rect x="-36" y="-10" width="28" height="6" rx="2" fill="{P.gold}"/><rect x="-36" y="12" width="28" height="6" rx="2" fill="{P.gold}"/>')
    s += (f'<g><animateTransform attributeName="transform" type="rotate" values="34 48 4;-28 48 4;-24 48 4;34 48 4" keyTimes="0;0.18;0.3;1" dur="2s" {R}/>{gav}</g>')
    return s


def i_fire(P):
    a1 = 'M0,50 C-36,50 -42,16 -24,-6 C-20,8 -12,10 -10,4 C-14,-20 0,-40 10,-54 C12,-30 40,-16 34,22 C30,42 18,50 0,50 Z'
    a2 = 'M0,50 C-38,48 -40,14 -26,-10 C-20,6 -12,8 -8,0 C-10,-24 4,-42 8,-58 C16,-32 42,-18 36,20 C32,42 18,50 0,50 Z'
    b1 = 'M0,50 C-18,50 -22,30 -10,14 C-8,22 -2,24 0,18 C0,6 8,-4 12,-12 C14,6 24,18 18,34 C14,46 8,50 0,50 Z'
    b2 = 'M0,50 C-20,48 -20,28 -12,12 C-8,20 -2,22 2,14 C2,4 8,-6 10,-16 C16,4 26,18 20,34 C16,46 8,50 0,50 Z'
    s = f'<path d="{a1}" fill="{P.acc_l}"><animate attributeName="d" values="{a1};{a2};{a1}" dur="0.8s" {R}/></path>'
    s += f'<path d="{b1}" fill="{P.gold}"><animate attributeName="d" values="{b1};{b2};{b1}" dur="0.6s" {R}/></path>'
    return s


ICONS = {
    'book': i_book, 'cap': i_cap, 'school': i_school, 'computer': i_computer, 'workstation': i_workstation,
    'cube': i_cube, 'code': i_code, 'chip': i_chip,
    'plane': i_plane, 'ship': i_ship, 'car': i_car, 'globe': i_globe, 'pin': i_pin, 'house': i_house, 'building': i_building,
    'medal': i_medal, 'trophy': i_trophy, 'star': i_star, 'crown': i_crown, 'money': i_money, 'chart': i_chart, 'chart_down': i_chart_down,
    'mic': i_mic, 'pen': i_pen, 'brush': i_brush, 'camera': i_camera, 'film': i_film, 'music': i_music, 'chat': i_chat,
    'phone': i_phone, 'letter': i_letter, 'newspaper': i_newspaper, 'calendar': i_calendar, 'clock': i_clock,
    'people': i_people, 'heart': i_heart, 'ecg': i_ecg, 'candle': i_candle, 'cake': i_cake, 'coffee': i_coffee, 'dumbbell': i_dumbbell,
    'ball': i_ball, 'briefcase': i_briefcase, 'flag': i_flag, 'rocket': i_rocket, 'bulb': i_bulb, 'gear': i_gear,
    'flask': i_flask, 'gavel': i_gavel, 'fire': i_fire,
}

ICON_NOTES = {
    'book': '读书、语言、写作（书页来回翻）', 'cap': '毕业、学位（流苏摆动）', 'school': '入学、学校（旗子飘）',
    'computer': '电脑、编程启蒙（绿屏打字）', 'workstation': '图形、3D、工作站（屏里立方体旋转）', 'cube': '3D、建模、产品（线框立方体旋转）',
    'code': '写代码、软件（终端打字）', 'chip': '芯片、硬件（核心阵列闪烁）',
    'plane': '出国、远行（飞机沿航线飞）', 'ship': '远渡、移民（船在浪上摇）', 'car': '汽车、出行（车轮转、路在走）',
    'globe': '全球化、国际（地球转、卫星绕）', 'pin': '地点、搬迁（定位针弹跳）', 'house': '家、童年、车库（窗灯明灭、烟囱冒烟）',
    'building': '公司、总部（窗户逐个亮起）', 'medal': '奖章、勋章（摆动）', 'trophy': '冠军、奖杯（闪光）', 'star': '荣誉、明星（旋转闪光）',
    'crown': '登顶、第一（浮动闪光）', 'money': '融资、财富（硬币堆高、旋转）', 'chart': '增长、市值（折线上扬）', 'chart_down': '下跌、危机（折线下坠）',
    'mic': '演讲、发布会（声波）', 'pen': '签约、写作（笔写出签名）', 'brush': '艺术、设计（调色盘、笔触）', 'camera': '拍摄、媒体（闪光）',
    'film': '电影、影视（胶片转）', 'music': '音乐（音符跳）', 'chat': '对话、AI 聊天（打字气泡）', 'phone': '手机、社交（消息弹出）',
    'letter': '信件、公开信（信纸滑出）', 'newspaper': '新闻、报道（标题被划重点）', 'calendar': '日期、日程（日期框跳动）', 'clock': '时间、倒计时（指针转）',
    'people': '团队、合伙人（中心人物波纹）', 'heart': '婚姻、爱情、公益（心跳）', 'ecg': '健康、疾病（心电图）', 'candle': '纪念、离世（烛光摇曳）',
    'cake': '生日、周年（烛火跳）', 'coffee': '咖啡馆、打工、深夜（热气升起）', 'dumbbell': '健身、体育（杠铃上下）', 'ball': '运动、比赛（球弹跳）', 'briefcase': '入职、跳槽（公文包）',
    'flag': '里程碑、登顶（旗帜飘）', 'rocket': '发射、创业起飞（火焰）', 'bulb': '灵感、发明（灯泡发光）', 'gear': '工程、制造（齿轮咬合）',
    'flask': '科研、实验（烧瓶冒泡）', 'gavel': '诉讼、判决（法槌落下）', 'fire': '爆红、热潮（火苗）',
}


def draw(name, theme, cx, cy, scale=1.0, dark=False):
    """在 (cx, cy) 画一个图标，scale=1 时约 120x120。"""
    fn = ICONS.get(name)
    if fn is None:
        raise KeyError(f'未知图标 {name!r}，可用：{", ".join(sorted(ICONS))}')
    body = fn(Pal(theme, dark))
    sc = '' if abs(scale - 1) < 1e-6 else f' scale({scale:g})'
    return f'<g transform="translate({_f(cx)} {_f(cy)}){sc}">{body}</g>'


def gallery(theme, cols=6):
    names = sorted(ICONS)
    rows = (len(names) + cols - 1) // cols
    W, cell = 750, 125
    H = rows * 170 + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" style="display:block;font-family:sans-serif">',
           f'<rect width="{W}" height="{H}" fill="{theme["PAPER"]}"/>']
    for k, nm in enumerate(names):
        c, r = k % cols, k // cols
        cx, cy = 62 + c * cell, 90 + r * 170
        out.append(draw(nm, theme, cx, cy, 0.8))
        out.append(f'<text x="{cx}" y="{cy + 70}" font-size="15" fill="{theme["GRAY"]}" text-anchor="middle">{nm}</text>')
    out.append('</svg>')
    return '\n'.join(out)


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'gallery':
        sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
        from lifeline import THEMES
        th = THEMES[sys.argv[3]] if len(sys.argv) > 3 else THEMES['terra']
        open(sys.argv[2], 'w', encoding='utf-8').write(gallery(th))
        print('written', sys.argv[2], len(ICONS), 'icons')
    else:
        print(__doc__)
