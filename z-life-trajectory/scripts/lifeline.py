#!/usr/bin/env python3
"""z-life-trajectory 引擎：人物 JSON → 超长动态 SVG（每屏 750x1000，3:4，可直接粘进公众号）。

    python3 lifeline.py build spec.json -o out.svg      # 生成长图，同时打印排版警告
    python3 lifeline.py lint out.svg [--forbid 词1,词2]  # 只做公众号可用性检查（也能查 .md 里的内联 SVG）
    python3 lifeline.py icons gallery.svg [--theme terra] # 图标总览
    python3 lifeline.py embed out.svg article.md          # 把长图放进文章里 <!-- lifeline --> 的位置

公众号规矩：没有 id / defs / style 元素 / script / 渐变 / 滤镜 / url(#)，动画全是 SMIL，
SVG 里不出现全角句号，也没有空行。
"""
import argparse
import importlib.util
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import icons as ICONS  # noqa: E402

W, SH = 750, 1000
SPINE, TX, RX = 78, 118, 702
CONTENT_BOTTOM = 960
SERIF = "'Source Han Serif SC','Source Han Serif SC VF','Noto Serif SC','Noto Serif CJK SC','Songti SC',serif"
MONO = "'SF Mono',Menlo,Consolas,monospace"

_BASE = dict(PAPER='#F7F3EA', INK='#1E2430', GRAY='#5F636B', GRAY2='#8B877F', GRAY3='#A39E94', RULE='#E2D9C8',
             RULE2='#D8CFBF', WHITE='#FFFFFF', GOLD='#D4A24C', DARK='#1E2430', DGRAY='#A3A7AE', DLINE='#323A4A',
             WATER='#E9DFCC', DWATER='#2C3446', DOT='#E6DED0', DDOT='#2A3242', TRACK='#E6DDCD', CARD2='#EFE6D6')
THEMES = {
    'terra': dict(_BASE, ACCENT='#C65D3B', ACCENT_L='#D97757', ACCENT_P='#F2DCD0', SECOND='#2C6E6A', DACCENT='#E58A63',
                  BENCH='#E8C6B5', BENCH2='#D9A892', FLOW='#FFF3EA'),
    'indigo': dict(_BASE, ACCENT='#2F4A8A', ACCENT_L='#4A68B0', ACCENT_P='#DCE3F2', SECOND='#C2703D', DACCENT='#8FA8E0',
                   BENCH='#C9D3EA', BENCH2='#A9B8DC', FLOW='#EEF2FB'),
    'jade': dict(_BASE, ACCENT='#2C6E5A', ACCENT_L='#3E8A72', ACCENT_P='#D5E8DF', SECOND='#C65D3B', DACCENT='#7CC2A8',
                 BENCH='#C3DDD1', BENCH2='#9CC5B3', FLOW='#EAF5EF'),
    'crimson': dict(_BASE, ACCENT='#A8322D', ACCENT_L='#C4493F', ACCENT_P='#F1D6D2', SECOND='#2F4A8A', DACCENT='#E0827A',
                    BENCH='#E9C2BC', BENCH2='#D89C94', FLOW='#FBEDEB'),
}
FORBIDDEN_MARKUP = [
    (r'\sid=', '出现 id 属性，公众号会剥掉'), (r'url\(#', '引用了 url(#…)'), (r'href="#', '引用了 href=#'),
    (r'<style', '出现 <style> 元素'), (r'<script', '出现 <script>'), (r'<defs', '出现 <defs>'),
    (r'<filter', '出现滤镜'), (r'Gradient', '出现渐变'), (r'<use\b', '出现 <use>'), (r'<mpath', '出现 <mpath>'),
    (r'<clipPath', '出现 clipPath'), (r'<mask', '出现 mask'), (r'foreignObject', '出现 foreignObject'),
    (r'<image', '出现 <image>'), (r'@keyframes', '出现 CSS 动画'), (r'。', 'SVG 里出现全角句号'),
]
NO_LINE_START = set('，。、：；！？）》」』”’%…,.;:!?)')


# ---------------------------------------------------------------- 字宽测量
FONT_CANDIDATES = [
    '~/Library/Fonts/SourceHanSerifSC-VF.ttf', '~/Library/Fonts/SourceHanSerifSC-VF.otf', '/Library/Fonts/SourceHanSerifSC-VF.ttf',
    '~/Library/Fonts/SourceHanSerifSC-Heavy.otf', '~/Library/Fonts/SourceHanSerifSC-Bold.otf', '~/Library/Fonts/SourceHanSerifSC-Regular.otf',
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    '/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', '/System/Library/Fonts/Supplemental/Songti.ttc',
    'C:/Windows/Fonts/simsun.ttc',
]


class Meter:
    def __init__(self, path=None):
        self.path = None
        self._fonts = {}
        cands = [path, os.environ.get('LIFELINE_FONT')] + FONT_CANDIDATES
        try:
            from PIL import ImageFont  # noqa: F401
            for p in cands:
                if p and os.path.exists(os.path.expanduser(p)):
                    self.path = os.path.expanduser(p)
                    break
        except ImportError:
            pass

    def _font(self, weight):
        f = self._fonts.get(weight)
        if f is None:
            from PIL import ImageFont
            f = ImageFont.truetype(self.path, size=100)
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
            self._fonts[weight] = f
        return f

    def width(self, s, size, weight=400):
        if self.path:
            return self._font(int(weight or 400)).getlength(s) * size / 100.0
        w = 0.0
        for ch in s:
            o = ord(ch)
            if o >= 0x2E80:
                w += 1.0
            elif ch == ' ':
                w += 0.3
            elif ch in "il.,:;|!'’":
                w += 0.3
            elif ch.isupper():
                w += 0.68
            else:
                w += 0.56
        return w * size * (1.03 if (weight or 400) >= 700 else 1.0)

    def _greedy(self, s, size, weight, width):
        toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9.,%$+\-/·'’&]*|\s+|.", s)
        lines, cur = [], ''
        for t in toks:
            cand = cur + t
            if not cur.strip() or self.width(cand.rstrip(), size, weight) <= width or t in NO_LINE_START:
                cur = cand
            else:
                lines.append(cur.rstrip())
                cur = t.lstrip()
        if cur.strip():
            lines.append(cur.rstrip())
        return lines or ['']

    def wrap(self, s, size, weight, width):
        if self.width(s, size, weight) <= width:
            return [s]
        lines = self._greedy(s, size, weight, width)
        if len(lines) > 1:
            target = self.width(s, size, weight) / len(lines) * 1.08
            bal = self._greedy(s, size, weight, min(width, target))
            if len(bal) == len(lines):
                lines = bal
        return lines


# ---------------------------------------------------------------- 绘图上下文
def n(v):
    if isinstance(v, float):
        s = '%.1f' % v
        return s[:-2] if s.endswith('.0') else s
    return str(v)


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Ctx:
    """块函数拿到的画笔。插件也只用这里的方法和常量。"""
    W, SH, SPINE, TX, RX, MONO, SERIF = W, SH, SPINE, TX, RX, MONO, SERIF

    def __init__(self, theme, meter, nscreens):
        self.T = theme
        self.m = meter
        self.buf = []
        self.measuring = False
        self.warns = []
        self.dark = False
        self.screen = 0
        self.y0 = 0
        self.last = nscreens - 1
        self.terminus_y = None
        self.rnd = random.Random(7)

    # 颜色（随深浅屏切换）
    @property
    def fg(self):
        return self.T['PAPER'] if self.dark else self.T['INK']

    @property
    def muted(self):
        return self.T['DGRAY'] if self.dark else self.T['GRAY']

    @property
    def faint(self):
        return '#6E7484' if self.dark else self.T['GRAY2']

    @property
    def acc(self):
        return self.T['DACCENT'] if self.dark else self.T['ACCENT']

    @property
    def bg(self):
        return self.T['DARK'] if self.dark else self.T['PAPER']

    @property
    def card_fill(self):
        return '#273042' if self.dark else self.T['WHITE']

    @property
    def card_stroke(self):
        return '#3A4252' if self.dark else self.T['RULE']

    def add(self, s):
        self.buf.append(s)

    def warn(self, msg):
        if not self.measuring:
            self.warns.append(f'[屏 {self.screen:02d}] {msg}')

    def tw(self, s, size, weight=400, ls=0, family=None):
        if family == MONO:
            return len(s) * size * 0.6 + ls * len(s)
        return self.m.width(s, size, weight) + ls * len(s)

    def wrap(self, s, size, weight, width):
        return self.m.wrap(s, size, weight, width)

    def wrap_lines(self, lines, size, weight, width):
        out = []
        for s in lines or []:
            out += self.wrap(s, size, weight, width)
        return out

    def lines_of(self, v, size, weight, width):
        """标题：写成列表就按你给的断行，写成字符串就自动折行。"""
        if isinstance(v, list):
            return [str(x) for x in v]
        return self.wrap(str(v or ''), size, weight, width) if v else []

    def text(self, x, y, s, size, fill, weight=None, anchor=None, ls=None, family=None, opacity=None, limit=None, left=30, extra=''):
        s = str(s)
        a = [f'x="{n(x)}"', f'y="{n(y)}"', f'font-size="{n(size)}"', f'fill="{fill}"']
        if weight:
            a.append(f'font-weight="{weight}"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if ls is not None:
            a.append(f'letter-spacing="{ls}"')
        if family:
            a.append(f'font-family="{family}"')
        if opacity is not None:
            a.append(f'opacity="{opacity}"')
        wdt = self.tw(s, size, weight or 400, ls or 0, family)
        x0, x1 = (x - wdt, x) if anchor == 'end' else ((x - wdt / 2, x + wdt / 2) if anchor == 'middle' else (x, x + wdt))
        lim = RX if limit is None else limit
        if x1 > lim + 0.5 or x0 < left - 0.5:
            self.warn(f'OVERFLOW 文字出界 {s!r}（{x0:.0f}→{x1:.0f}，右界 {lim}）')
        return f'<text {" ".join(a)}{extra}>{esc(s)}</text>'

    def styled(self, item):
        """文字行：字符串 = 普通；{"text":…, "style":"bold|accent|faint"}。"""
        if isinstance(item, dict):
            st = item.get('style', 'normal')
            col = {'bold': self.fg, 'accent': self.acc, 'faint': self.faint, 'second': self.T['SECOND']}.get(st, self.muted)
            return item.get('text', ''), col, (800 if st in ('bold', 'accent', 'second') else None)
        return str(item), self.muted, None

    def pulse(self, x, y, color=None, r0=13, r1=30, dur=2.6, begin=0.0):
        color = color or self.acc
        return (f'<circle cx="{n(x)}" cy="{n(y)}" r="{r0}" fill="none" stroke="{color}" stroke-width="2.5" opacity="0">'
                f'<animate attributeName="r" values="{r0};{r1}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.85;0" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>')

    def marker(self, x, y, kind='stop'):
        bg, fg = (self.T['DARK'], self.T['PAPER']) if self.dark else (self.T['PAPER'], self.T['INK'])
        if kind == 'major':
            self.add(self.pulse(x, y, self.acc))
            self.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="13.5" fill="{fg}"/>')
            self.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="5.5" fill="{self.T["ACCENT_L"]}"/>')
        elif kind == 'terminus':
            self.add(f'<rect x="{n(x - 24)}" y="{n(y - 5.5)}" width="48" height="11" rx="3" fill="{fg}"/>')
        else:
            self.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="9.5" fill="{bg}" stroke="{fg}" stroke-width="3.5"/>')

    def stub(self, y):
        self.add(f'<line x1="{SPINE + 10}" y1="{n(y)}" x2="{TX}" y2="{n(y)}" stroke="{self.fg}" stroke-width="2.5"/>')
        self.marker(SPINE, y, 'stop')

    def card(self, x, y, w, h, fill=None, stroke=None):
        self.add(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="16" fill="{fill or self.card_fill}" '
                 f'stroke="{stroke or self.card_stroke}" stroke-width="1.5"/>')

    def arrowhead(self, x, y, dx, dy, size=9, color=None, w=3):
        color = color or self.acc
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        px, py = -uy, ux
        a = (x - ux * size + px * size * 0.65, y - uy * size + py * size * 0.65)
        b = (x - ux * size - px * size * 0.65, y - uy * size - py * size * 0.65)
        self.add(f'<path d="M{a[0]:.1f},{a[1]:.1f} L{x:.1f},{y:.1f} L{b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')

    def icon(self, name, cx, cy, scale=1.0):
        try:
            self.add(ICONS.draw(name, self.T, cx, cy, scale, self.dark))
        except KeyError as e:
            self.warn(str(e))

    def grow_bar_h(self, x, y, w, h, color, begin=0.0, dur=7.0):
        yy = y + h / 2
        self.add(f'<line x1="{n(x)}" y1="{n(yy)}" x2="{n(x + w)}" y2="{n(yy)}" stroke="{color}" stroke-width="{n(h)}" '
                 f'stroke-dasharray="{w:.1f} {w:.1f}" stroke-dashoffset="{w:.1f}">'
                 f'<animate attributeName="stroke-dashoffset" values="{w:.1f};0;0;{w:.1f}" keyTimes="0;0.22;0.92;1" dur="{dur}s" '
                 f'begin="{begin:.2f}s" repeatCount="indefinite"/></line>')


# ---------------------------------------------------------------- 内容块（每个函数：在 top 处画，返回高度）
def blk_station(c, top, b):
    y = top + 14
    side = b.get('icon')
    lim = RX - 140 if side else RX
    tsize = b.get('title_size', 29)
    if b.get('marker', True):
        c.marker(SPINE, y, b.get('kind', 'stop'))
    if b.get('year'):
        c.add(c.text(TX, y + 8, b['year'], 23, c.acc, 800, ls=1, limit=lim))
    tl = c.lines_of(b.get('title', ''), tsize, 800, lim - TX) or ['']
    ty = y + 48
    for i, s in enumerate(tl):
        c.add(c.text(TX, ty + 38 * i, s, tsize, c.fg, 800, limit=lim))
    ty += 38 * (len(tl) - 1)
    lines = c.wrap_lines(b.get('lines'), 21, 400, lim - TX)
    for i, s in enumerate(lines):
        c.add(c.text(TX, ty + 38 + 33 * i, s, 21, c.muted, limit=lim))
    bottom = (ty + 38 + 33 * (len(lines) - 1) + 8) if lines else ty + 8
    h = bottom - top
    if side:
        sc = b.get('icon_scale', 0.85)
        ih = 124 * sc
        hh = max(h, ih)
        c.icon(side, RX - 64, top + hh / 2, sc)
        h = hh
    return h


def blk_terminus(c, top, b):
    y = top + 14
    c.marker(SPINE, y, 'terminus')
    c.add(f'<rect x="{SPINE - 24}" y="{n(y - 6)}" width="48" height="11" rx="3" fill="{c.acc}" opacity="0">'
          f'<animate attributeName="opacity" values="0;1;0" dur="2s" repeatCount="indefinite"/></rect>')
    if not c.measuring:
        c.terminus_y = y
    return blk_station(c, top, dict(b, marker=False))


def blk_compact(c, top, b):
    y = top + 14
    c.marker(SPINE, y, b.get('kind', 'stop'))
    tcol = b.get('_tcol', 118)
    c.add(c.text(TX, y + 9, b.get('year', ''), 23, c.acc, 800, ls=1))
    x2 = TX + tcol
    tl = c.lines_of(b.get('title', ''), 27, 800, RX - x2) or ['']
    for i, s in enumerate(tl):
        c.add(c.text(x2, y + 9 + 36 * i, s, 27, c.fg, 800))
    ty = y + 9 + 36 * (len(tl) - 1)
    lines = c.wrap_lines(b.get('lines'), 21, 400, RX - x2)
    for i, s in enumerate(lines):
        c.add(c.text(x2, ty + 36 + 32 * i, s, 21, c.muted))
    bottom = (ty + 36 + 32 * (len(lines) - 1) + 8) if lines else ty + 8
    return bottom - top


def blk_card(c, top, b):
    x0, x1 = TX, RX
    has_icon = bool(b.get('icon'))
    iw = b.get('icon_w', 216) if has_icon else 0
    tx = x0 + iw + (16 if has_icon else 28)
    lim = x1 - 20
    width = lim - tx
    rows = []
    if b.get('year'):
        rows.append([0, b['year'], 21, c.acc, 800])
    for i, s in enumerate(c.lines_of(b.get('title', ''), 25, 800, width)):
        rows.append([(40 if b.get('year') else 0) if i == 0 else 34, s, 25, c.fg, 800])
    for i, s in enumerate(c.wrap_lines(b.get('lines'), 19, 400, width)):
        rows.append([38 if i == 0 else 30, s, 19, c.muted, None])
    if b.get('note'):
        for i, s in enumerate(c.wrap(b['note'], 17, 600, width)):
            rows.append([36 if i == 0 else 26, s, 17, c.faint, 600])
    if not rows:
        rows = [[0, '', 19, c.muted, None]]
    rows[0][0] = 0
    text_h = rows[0][2] * 0.8 + sum(r[0] for r in rows[1:]) + 6
    sc = b.get('icon_scale', 1.0)
    cap = b.get('icon_label')
    h = max(b.get('height', 0), text_h + 60, (124 * sc + 44 + (26 if cap else 0)) if has_icon else 0)
    c.card(x0, top, x1 - x0, h, fill=b.get('fill'))
    if has_icon:
        icx = x0 + 16 + iw / 2
        c.icon(b['icon'], icx, top + (h - (26 if cap else 0)) / 2, sc)
        if cap:
            c.add(c.text(icx, top + h - 20, cap, 15, c.faint, 600, anchor='middle'))
    base = top + (h - text_h) / 2 + rows[0][2] * 0.8
    for k, (adv, s, size, col, wt) in enumerate(rows):
        base += adv
        c.add(c.text(tx, base, s, size, col, wt, limit=lim))
    if b.get('stub', True):
        c.stub(top + h / 2)
    return h


def blk_counter(c, top, b):
    cnt = max(1, min(int(b.get('count', 10)), 10))
    h = 140
    c.card(TX, top, RX - TX, h)
    c.icon(b.get('icon', 'book'), 200, top + 72, 0.8)
    x0 = 290
    c.add(c.text(x0, top + 42, b.get('title', ''), 22, c.fg, 800, limit=RX - 16))
    if b.get('sub'):
        c.add(c.text(x0, top + 70, b['sub'], 18, c.muted, limit=RX - 16))
    step = 41 if cnt == 10 else min(56, (RX - 16 - x0 - 34) / max(1, cnt - 1))
    labels = b.get('labels') or [str(k + 1) for k in range(cnt)]
    fill_tile = c.T['PAPER'] if not c.dark else '#273042'
    for k in range(cnt):
        x = x0 + k * step
        yy = top + 86
        lab = str(labels[k]) if k < len(labels) else ''
        c.add(f'<rect x="{n(x)}" y="{yy}" width="34" height="34" rx="6" fill="{fill_tile}" stroke="{c.T["RULE2"]}" stroke-width="1.5"/>')
        c.add(c.text(x + 17, yy + 22, lab, 13, c.T['GRAY3'], family=MONO, anchor='middle'))
        f = (0.3 + k * 0.42) / 6.0
        c.add(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{f:.3f};{f + 0.02:.3f};0.93;1" dur="6s" repeatCount="indefinite"/>'
              f'<rect x="{n(x)}" y="{yy}" width="34" height="34" rx="6" fill="{c.acc}"/>'
              + c.text(x + 17, yy + 22, lab, 13, '#FFFFFF', family=MONO, anchor='middle', weight=700) + '</g>')
    if b.get('stub'):
        c.stub(top + h / 2)
    return h


VEHICLES = {
    'plane': ICONS.PLANE,
    'ship': 'M-14,2 H14 L9,9 H-9 Z M-6,2 V-6 H4 V2 Z',
    'car': 'M-14,5 V0 Q-14,-3 -11,-3 L-6,-9 H5 L10,-3 Q14,-2 14,1 V5 Z',
    'train': 'M-15,-8 H11 Q16,-8 16,-2 V6 H-15 Z',
}


def blk_journey(c, top, b):
    y = top + 70
    x0, x1 = b.get('x0', 170), b.get('x1', 640)
    arc = f'M{x0},{y} C{x0 + 130},{y - 72} {x1 - 130},{y - 72} {x1},{y}'
    c.add(f'<path d="{arc}" fill="none" stroke="{c.acc}" stroke-width="4.5" stroke-linecap="round" stroke-dasharray="0.1 12"/>')
    for ex, lab in ((x0, b.get('from', '')), (x1, b.get('to', ''))):
        c.add(f'<circle cx="{ex}" cy="{y}" r="6.5" fill="{c.fg}"/>')
        c.add(c.text(ex, y + 32, lab, 17, c.muted, 700, anchor='middle'))
    if b.get('label'):
        c.add(c.text((x0 + x1) / 2, y - 15, b['label'], 15, c.faint, anchor='middle', ls=2))
    shape = VEHICLES.get(b.get('vehicle', 'plane'), VEHICLES['plane'])
    c.add(f'<path d="{shape}" fill="{c.fg}" opacity="0"><animateMotion path="{arc}" dur="3.6s" rotate="auto" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.88;1" dur="3.6s" repeatCount="indefinite"/></path>')
    return 108


def blk_quote(c, top, b):
    x = TX + 26
    lines = c.wrap_lines(b.get('lines'), 30, 900, RX - x)
    base = top + (72 if b.get('lead') else 30)
    if b.get('lead'):
        c.add(c.text(x, top + 24, b['lead'], 20, c.muted, 600))
    for i, s in enumerate(lines):
        last = i == len(lines) - 1
        c.add(c.text(x, base + 44 * i, s, 30, c.acc if (last and len(lines) > 1) else c.fg, 900))
    bottom = base + 44 * (len(lines) - 1) + 12
    if b.get('cite'):
        c.add(c.text(x, bottom + 26, b['cite'], 17, c.faint, 600))
        bottom += 34
    c.add(f'<rect x="{TX}" y="{top}" width="5" height="{n(bottom - top)}" rx="2.5" fill="{c.acc}"/>')
    return bottom - top


def blk_ring(c, top, b):
    R = 100
    cx, cy = b.get('cx', 410), top + 114
    C = 2 * math.pi * R
    drain = float(b.get('drain', 11 / 12))
    rescue = b.get('rescue', True)
    sec = c.T['SECOND']
    c.add(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{c.T["DLINE"] if c.dark else c.T["TRACK"]}" stroke-width="16"/>')
    if rescue:
        anim = (f'<animate attributeName="stroke-dashoffset" values="0;{C * drain:.1f};{C * drain:.1f};0;0" keyTimes="0;0.45;0.56;0.65;1" dur="9s" repeatCount="indefinite"/>'
                f'<animate attributeName="stroke" values="{c.acc};{c.acc};{sec};{sec};{c.acc}" keyTimes="0;0.56;0.58;0.96;1" dur="9s" repeatCount="indefinite"/>')
    else:
        anim = f'<animate attributeName="stroke-dashoffset" values="0;{C * drain:.1f};{C * drain:.1f};0" keyTimes="0;0.5;0.94;1" dur="9s" repeatCount="indefinite"/>'
    c.add(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{c.acc}" stroke-width="16" stroke-linecap="round" '
          f'stroke-dasharray="{C:.1f} {C:.1f}" transform="rotate(-90 {cx} {cy})">{anim}</circle>')
    c.add(f'<text x="{cx}" y="{cy + 22}" font-size="92" fill="{c.fg}" font-weight="900" text-anchor="middle">{esc(b.get("value", ""))}'
          f'<animate attributeName="fill" values="{c.fg};{c.fg};{c.acc};{c.fg};{c.acc};{c.fg};{c.fg}" keyTimes="0;0.36;0.42;0.46;0.5;0.54;1" dur="9s" repeatCount="indefinite"/></text>')
    if b.get('unit'):
        c.add(c.text(cx, cy + 60, b['unit'], 24, c.faint, 700, anchor='middle'))
    left = b.get('left', [])
    for i, it in enumerate(left):
        s, col, wt = c.styled(it)
        c.add(c.text(TX, cy - 10 + 32 * i - 16 * (len(left) - 2), s, 19, col, wt, limit=cx - R - 14))
    right = b.get('right', [])
    if right:
        g = ''
        for i, it in enumerate(right):
            s = it if isinstance(it, str) else it.get('text', '')
            g += c.text(cx + R + 30, cy - 10 + 32 * i, s, 22 if i == 0 else 19, sec, 800 if i == 0 else 700)
        if rescue:
            c.add(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.57;0.6;0.95;1" dur="9s" repeatCount="indefinite"/>{g}</g>')
        else:
            c.add(g)
    return 2 * R + 28


def blk_dots(c, top, b):
    total = int(b.get('total', 70))
    keep = max(1, int(b.get('keep', 2)))
    cols = int(b.get('cols', 14))
    rows = min(7, math.ceil(total / cols))
    cells = [(cc, r) for r in range(rows) for cc in range(cols)][:total]
    x0 = RX - 12 - (cols - 1) * 21
    rnd = random.Random(b.get('seed', 7))
    surv = rnd.sample(cells, min(keep, len(cells)))
    others = [p for p in cells if p not in surv]
    rnd.shuffle(others)
    ng = 8
    for g in range(ng):
        mem = others[g::ng]
        circ = ''.join(f'<circle cx="{x0 + cc * 21}" cy="{top + 10 + r * 21}" r="6.5" fill="{c.T["GRAY3"]}"/>' for (cc, r) in mem)
        f0 = 0.08 + g * 0.07
        c.add(f'<g><animate attributeName="opacity" values="1;1;0.12;0.12;1" keyTimes="0;{f0:.2f};{f0 + 0.05:.2f};0.9;1" dur="7s" repeatCount="indefinite"/>{circ}</g>')
    for (cc, r) in surv:
        x, yy = x0 + cc * 21, top + 10 + r * 21
        c.add(c.pulse(x, yy, c.acc, 7, 18, 2.0))
        c.add(f'<circle cx="{x}" cy="{yy}" r="8" fill="{c.acc}"/>')
    lines = b.get('lines', [])
    for i, it in enumerate(lines):
        s, col, wt = c.styled(it)
        c.add(c.text(TX, top + 18 + 30 * i, s, 19, col, wt, limit=x0 - 18))
    return max(rows * 21 + 2, 30 * len(lines) - 4)


def blk_exchange(c, top, b):
    h = 200
    c.card(TX, top, RX - TX, h)
    L, Rr = b.get('left', {}), b.get('right', {})
    c.icon(L.get('icon', 'book'), 250, top + 86, L.get('scale', 0.85))
    c.icon(Rr.get('icon', 'dumbbell'), 570, top + 86, Rr.get('scale', 0.85))
    up = f'M318,{top + 62} Q410,{top + 18} 494,{top + 58}'
    dn = f'M494,{top + 112} Q410,{top + 156} 318,{top + 112}'
    for d in (up, dn):
        c.add(f'<path d="{d}" fill="none" stroke="{c.T["RULE2"]}" stroke-width="3" stroke-linecap="round"/>')
        c.add(f'<path d="{d}" fill="none" stroke="{c.acc}" stroke-width="3" stroke-linecap="round" stroke-dasharray="12 14">'
              f'<animate attributeName="stroke-dashoffset" values="0;-26" dur="0.9s" repeatCount="indefinite"/></path>')
    c.arrowhead(494, top + 58, 84, 40)
    c.arrowhead(318, top + 112, -92, -44)
    if b.get('middle'):
        c.add(c.text(406, top + 93, b['middle'], 16, c.faint, 700, anchor='middle', ls=2))
    c.add(c.text(250, top + 174, L.get('label', ''), 18, c.fg, 800, anchor='middle'))
    c.add(c.text(570, top + 174, Rr.get('label', ''), 18, c.fg, 800, anchor='middle'))
    return h


def blk_team(c, top, b):
    T = c.T
    names = b.get('names', [])[:4]
    k = len(names)
    BY = top
    c.add(f'<rect x="150" y="{BY}" width="520" height="46" rx="16" fill="{T["BENCH"]}"/>')
    c.add(f'<rect x="150" y="{BY + 170}" width="520" height="46" rx="16" fill="{T["BENCH"]}"/>')
    c.add(f'<rect x="176" y="{BY + 56}" width="468" height="104" rx="14" fill="{c.card_fill}" stroke="{c.fg}" stroke-width="3"/>')
    pos = {1: [(410, 86)], 2: [(330, 86), (490, 86)], 3: [(300, 86), (520, 86), (410, 132)],
           4: [(300, 86), (520, 86), (300, 132), (520, 132)]}.get(k, [])
    for i, ((ux, dy), nm) in enumerate(zip(pos, names)):
        uy = BY + dy
        c.add(f'<rect x="{ux + 14}" y="{uy - 4}" width="10" height="8" rx="3" fill="none" stroke="{c.fg}" stroke-width="3"/>')
        c.add(f'<circle cx="{ux}" cy="{uy}" r="16" fill="{c.card_fill}" stroke="{c.fg}" stroke-width="3"/><circle cx="{ux}" cy="{uy}" r="10.5" fill="#6E4B3A"/>')
        c.add(f'<circle cx="{ux}" cy="{uy}" r="10.5" fill="none" stroke="{T["ACCENT_L"]}" stroke-width="2" opacity="0">'
              f'<animate attributeName="r" values="10;22" dur="3s" begin="{i:.0f}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="0.7;0" dur="3s" begin="{i:.0f}s" repeatCount="indefinite"/></circle>')
        ly = BY + 30 if dy < 100 else BY + 200
        bold = isinstance(nm, dict) and nm.get('style') == 'bold'
        label = nm.get('text', '') if isinstance(nm, dict) else nm
        c.add(c.text(ux, ly, label, 18 if bold else 17, T['INK'], 800 if bold else 600, anchor='middle'))
    rn = b.get('rename')
    if rn:
        g = (f'<g transform="rotate(-6 572 {BY + 132})"><rect x="526" y="{BY + 110}" width="94" height="46" rx="3" fill="#FBF7EE" stroke="{T["RULE2"]}" stroke-width="1.5"/>'
             + c.text(573, BY + 128, rn.get('from', ''), 14, T['GRAY2'], anchor='middle', limit=760)
             + f'<line x1="546" y1="{BY + 123}" x2="600" y2="{BY + 123}" stroke="{T["ACCENT"]}" stroke-width="2"/>'
             + c.text(573, BY + 149, rn.get('to', ''), 16, T['INK'], 800, anchor='middle', ls=1, limit=760) + '</g>')
        c.add(g)
    for i, it in enumerate(b.get('notes', [])[:3]):
        s, col, wt = c.styled(it)
        if col == c.muted:
            col = T['GRAY2']
        c.add(c.text(196, BY + 112 + 20 * i, s, 14, col, wt, limit=(510 if rn else 630)))
    return 216


def blk_tokens(c, top, b):
    items = b.get('items', [])[:6]
    x = b.get('x', TX)
    T = c.T
    k = len(items)
    for i, it in enumerate(items):
        w = max(70, c.tw(it, 15, 700, family=MONO) + 24)
        f0 = 0.08 + i * 0.12
        c.add(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{f0:.2f};{f0 + 0.04:.2f};0.92;1" dur="5s" repeatCount="indefinite"/>'
              f'<rect x="{n(x)}" y="{top}" width="{n(w)}" height="34" rx="5" fill="#E7EFE6" stroke="{T["SECOND"]}" stroke-width="2"/>'
              + c.text(x + w / 2, top + 23, it, 15, T['SECOND'], 700, anchor='middle', family=MONO) + '</g>')
        x += w + 12
    if b.get('total'):
        ft = 0.1 + k * 0.12
        c.add(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{ft:.2f};{ft + 0.04:.2f};0.92;1" dur="5s" repeatCount="indefinite"/>'
              + c.text(x + 6, top + 25, b['total'], 21, c.acc, 800, family=MONO) + '</g>')
    return 34


def blk_compare(c, top, b):
    h = b.get('height', 230)
    c.card(TX, top, RX - TX, h)
    verdict = b.get('verdict')
    for side, cx in (('left', 262), ('right', 552)):
        p = b.get(side, {})
        if p.get('icon'):
            c.icon(p['icon'], cx, top + 92, p.get('scale', 0.8))
        elif p.get('big'):
            c.add(c.text(cx, top + 112, p['big'], p.get('size', 44), c.acc if verdict == side else c.fg, 900, anchor='middle'))
        c.add(c.text(cx, top + h - 38, p.get('title', ''), 18, c.fg, 800, anchor='middle'))
        if p.get('sub'):
            c.add(c.text(cx, top + h - 14, p['sub'], 15, c.muted, anchor='middle'))
        if verdict:
            bx, by = cx + 84, top + 30
            if verdict == side:
                c.add(f'<circle cx="{bx}" cy="{by}" r="15" fill="{c.T["SECOND"]}"/><path d="M{bx - 7},{by} L{bx - 2},{by + 5} L{bx + 7},{by - 5}" fill="none" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
            else:
                c.add(f'<circle cx="{bx}" cy="{by}" r="15" fill="{c.acc}"/><path d="M{bx - 6},{by - 6} L{bx + 6},{by + 6} M{bx + 6},{by - 6} L{bx - 6},{by + 6}" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round"/>')
    c.add(c.text(407, top + 103, b.get('vs', 'VS'), 18, c.T['GRAY3'], 700, anchor='middle', family=MONO))
    return h


def blk_bars(c, top, b):
    h = b.get('height', 520)
    base = top + h - 46
    ax = b.get('axis', {})
    t0, t1 = ax.get('from', 0), ax.get('to', 10)
    X0, X1 = 172, 690
    xt = lambda t: X0 + (t - t0) / (t1 - t0) * (X1 - X0)  # noqa: E731
    items = b.get('items', [])
    vmax = max((it['v'] for it in items), default=1)
    unit = (h - 100) / vmax
    line = '#4A5265' if c.dark else c.T['RULE2']
    c.add(f'<line x1="150" y1="{base}" x2="{RX}" y2="{base}" stroke="{line}" stroke-width="2"/>')
    for t, lab in ax.get('ticks', []):
        xx = xt(t)
        c.add(f'<line x1="{n(xx)}" y1="{base}" x2="{n(xx)}" y2="{base + 10}" stroke="{line}" stroke-width="2"/>')
        c.add(c.text(xx + 6, base + 30, lab, 16, c.muted, 600))
    ins = b.get('inset')
    if ins:
        vs = ins.get('size', 72)
        c.add(c.text(170, top + 78, ins.get('value', ''), vs, c.acc, 900))
        if ins.get('unit'):
            c.add(c.text(170 + c.tw(ins['value'], vs, 900) + 12, top + 78, ins['unit'], 26, c.fg, 800))
        for i, it in enumerate(ins.get('lines', [])):
            s, col, wt = c.styled(it)
            c.add(c.text(170, top + 114 + 34 * i, s, 19 if i == 0 else 17, col, wt))
    bg = c.T['ACCENT'] if c.dark else c.T['ACCENT_P']
    for i, it in enumerate(items):
        xx = xt(it['t'])
        hh = unit * it['v']
        tp = base - hh
        c.add(f'<rect x="{n(xx - 16)}" y="{n(tp)}" width="32" height="{n(hh)}" fill="{bg}" opacity="{0.32 if c.dark else 1}"/>')
        col = c.acc
        c.add(f'<line x1="{n(xx)}" y1="{base}" x2="{n(xx)}" y2="{n(tp)}" stroke="{col}" stroke-width="32" stroke-dasharray="{hh:.1f} {hh:.1f}" stroke-dashoffset="{hh:.1f}">'
              f'<animate attributeName="stroke-dashoffset" values="{hh:.1f};0;0;{hh:.1f}" keyTimes="0;0.22;0.92;1" dur="7s" begin="{i * 0.35:.2f}s" repeatCount="indefinite"/></line>')
        if it.get('label'):
            c.add(c.text(xx + 16, tp - 34, it['label'], 20, c.fg, 800, anchor='end'))
        if it.get('note'):
            c.add(c.text(xx + 16, tp - 12, it['note'], 15, c.muted, 600, anchor='end'))
    if items:
        it = items[-1]
        c.add(c.pulse(xt(it['t']), base - unit * it['v'], c.acc, 6, 17, 2.2))
    br = b.get('bracket')
    if br and len(items) > max(br['from'], br['to']):
        xa, xb = xt(items[br['from']]['t']) + 22, xt(items[br['to']]['t']) - 22
        c.add(f'<path d="M{n(xa)},{base - 36} V{base - 28} H{n(xb)} V{base - 36}" fill="none" stroke="{c.acc}" stroke-width="2"/>')
        c.add(c.text((xa + xb) / 2, base - 44, br.get('text', ''), 16, c.acc, 800, anchor='middle'))
    ev = b.get('event')
    if ev:
        xd = xt(ev['t'])
        lv = ev.get('level', 146)
        c.add(f'<line x1="{n(xd)}" y1="{base - lv}" x2="{n(xd)}" y2="{base}" stroke="{c.muted}" stroke-width="1.5" stroke-dasharray="3 6" opacity="0.7"/>')
        c.add(f'<path d="M{n(xd - 7)},{base - lv - 18} L{n(xd + 7)},{base - lv - 18} L{n(xd)},{base - lv - 6} Z" fill="{c.acc}"/>')
        lines = ev.get('lines', [])
        for i, s in enumerate(lines):
            c.add(c.text(xd, base - lv - 30 - 22 * (len(lines) - 1 - i), s, 14, c.muted, 600, anchor='middle'))
    return h


def blk_hbars(c, top, b):
    items = b.get('items', [])
    y = top
    if b.get('title'):
        c.add(c.text(TX, top + 18, b['title'], 19, c.fg, 800))
        y = top + 40
    lw = max((c.tw(str(it.get('label', '')), 15, 700, family=MONO) for it in items), default=40)
    x0 = TX + lw + 16
    tmax = max((c.tw(str(it.get('text', '')), 16, 800) for it in items), default=40)
    wmax = RX - x0 - tmax - 14
    vmax = max((it['v'] for it in items), default=1)
    hl = b.get('highlight', len(items) - 1)
    for i, it in enumerate(items):
        yy = y + i * 50
        w = it['v'] / vmax * wmax
        on = i == hl
        c.add(c.text(TX, yy + 20, it.get('label', ''), 15, c.faint, 700, family=MONO))
        c.add(f'<rect x="{n(x0)}" y="{yy}" width="{w:.1f}" height="26" rx="3" fill="{c.acc}" opacity="0.16"/>')
        c.grow_bar_h(x0, yy, w, 26, c.acc if on else c.T['ACCENT_L'], begin=i * 0.3)
        c.add(c.text(x0 + w + 10, yy + 20, it.get('text', ''), 16, c.acc if on else c.muted, 800))
    return (y - top) + 50 * (len(items) - 1) + 26


def blk_bigstat(c, top, b):
    size = b.get('size', 96)
    base = top + size * 0.86
    col = c.acc if b.get('accent') else c.fg
    c.add(c.text(b.get('x', TX), base, b.get('value', ''), size, col, 900))
    if b.get('unit'):
        ux = b.get('x', TX) + c.tw(b['value'], size, 900) + 12
        c.add(c.text(ux, base, b['unit'], max(22, size * 0.36), c.fg, 800))
    ls = b.get('line_size', 22)
    for i, it in enumerate(b.get('lines', [])):
        s, col2, wt = c.styled(it)
        c.add(c.text(b.get('x', TX), base + ls * 2.2 + (ls + 12) * i, s, ls, col2, wt))
    k = len(b.get('lines', []))
    return (base - top) + (ls * 2.2 + (ls + 12) * (k - 1) + 8 if k else 10)


def blk_plaque(c, top, b):
    T = c.T
    booth = b.get('scene') == 'booth'
    h = 240 if booth else 150
    c.card(TX, top, RX - TX, h, fill=('#273042' if c.dark else T['CARD2']))
    if booth:
        c.add(f'<rect x="170" y="{top + 124}" width="480" height="84" rx="20" fill="{T["BENCH"]}"/>')
        c.add(f'<rect x="170" y="{top + 124}" width="480" height="16" rx="8" fill="{T["BENCH2"]}"/>')
        c.add(f'<rect x="300" y="{top + 158}" width="220" height="14" rx="4" fill="{T["INK"]}"/>')
        c.add(f'<rect x="404" y="{top + 172}" width="12" height="52" fill="{T["INK"]}"/>')
        c.add(f'<rect x="372" y="{top + 222}" width="76" height="8" rx="4" fill="{T["INK"]}"/>')
        c.add(f'<rect x="456" y="{top + 130}" width="30" height="28" rx="6" fill="#FFFFFF" stroke="{T["INK"]}" stroke-width="2.5"/>')
        for i, sx in enumerate((464, 478)):
            c.add(f'<path d="M{sx},{top + 124} c-6,-6 6,-10 0,-16 c-6,-6 6,-9 0,-14" fill="none" stroke="{T["GRAY3"]}" stroke-width="2.5" stroke-linecap="round" opacity="0">'
                  f'<animate attributeName="opacity" values="0;0.9;0" dur="2.4s" begin="{i * 1.2:.1f}s" repeatCount="indefinite"/>'
                  f'<animateTransform attributeName="transform" type="translate" values="0 6;0 -6" dur="2.4s" begin="{i * 1.2:.1f}s" repeatCount="indefinite"/></path>')
    title, sub = b.get('title', ''), b.get('sub', '')
    pw = max(220, c.tw(title, 20, 800) + 48)
    px = 410 - pw / 2
    py = top + 26 if booth else top + (h - 76) / 2
    c.add(f'<rect x="{n(px)}" y="{n(py)}" width="{n(pw)}" height="76" rx="6" fill="{T["INK"]}" stroke="#C9A45C" stroke-width="3"/>')
    c.add(c.text(410, py + 36, title, 20, '#F2D9A0', 800, anchor='middle'))
    if sub:
        c.add(c.text(410, py + 62, sub, 13, '#C9A45C', anchor='middle', ls=1, family=MONO))
    for (sx, sy, bg) in ((px + pw + 2, py + 2, 0.0), (px - 4, py + 72, 1.2)):
        c.add(f'<g transform="translate({n(sx)} {n(sy)})"><path d="{ICONS.SPARK}" fill="#F2D9A0">'
              f'<animateTransform attributeName="transform" type="scale" values="0;1;0;0" keyTimes="0;0.2;0.4;1" dur="2.4s" begin="{bg}s" repeatCount="indefinite"/></path></g>')
    return h


def blk_lifebar(c, top, b):
    T = c.T
    segs = b.get('segments', [])
    if not segs:
        return 0
    s0, s1 = b.get('start', segs[0]['from']), b.get('end', segs[-1]['to'])
    xo = lambda yr: TX + (yr - s0) / (s1 - s0) * (RX - TX)  # noqa: E731
    y = top
    if b.get('title'):
        c.add(c.text(TX, top + 18, b['title'], 24, c.fg, 800))
        y = top + 46
    bar_y = y + 10
    tones = ['#E6DCCB', '#D9CDB8', '#C9BBA3', '#B8A88E', '#A69479']
    k = 0
    for sg in segs:
        xa, xb = xo(sg['from']), xo(sg['to'])
        on = sg.get('accent')
        col = c.acc if on else tones[min(k, len(tones) - 1)]
        if not on:
            k += 1
        c.add(f'<rect x="{n(xa)}" y="{bar_y}" width="{n(xb - xa)}" height="24" fill="{col}"/>')
        c.add(c.text((xa + xb) / 2, bar_y + 50, sg.get('label', ''), 16, c.acc if on else c.muted, 800 if on else 600, anchor='middle', limit=RX + 30))
    ticks = b.get('ticks')
    if ticks is None:
        bounds = [s0] + [sg['to'] for sg in segs]
        ticks = [[v, str(int(v))] for v in bounds]
    for i, (v, lab) in enumerate(ticks):
        anc = 'start' if i == 0 else ('end' if i == len(ticks) - 1 else 'middle')
        c.add(c.text(xo(v), y, lab, 14, c.faint, anchor=None if anc == 'start' else anc, family=MONO))
    c.add(f'<rect x="{TX}" y="{bar_y - 4}" width="3.5" height="32" fill="{c.fg}"><animate attributeName="x" values="{TX};{RX - 3.5};{RX - 3.5}" '
          f'keyTimes="0;0.85;1" dur="8s" repeatCount="indefinite"/></rect>')
    if c.terminus_y and not c.measuring and b.get('tail', True):
        ty = bar_y + 12
        c.add(f'<path d="M{SPINE},{n(c.terminus_y + 20)} V{n(ty - 26)} Q{SPINE},{n(ty)} {SPINE + 26},{n(ty)} H{TX - 6}" fill="none" '
              f'stroke="{T["GRAY3"]}" stroke-width="4" stroke-linecap="round" stroke-dasharray="0.1 11"/>')
    return (bar_y - top) + 56


def blk_text(c, top, b):
    size = b.get('size', 19)
    adv = b.get('leading', round(size * 1.58))
    x = b.get('x', TX)
    lines = []
    for it in b.get('lines', []):
        s, col, wt = c.styled(it)
        for part in c.wrap(s, size, wt or 400, RX - x):
            lines.append((part, col, wt))
    for i, (s, col, wt) in enumerate(lines):
        c.add(c.text(x, top + size * 0.86 + adv * i, s, size, col, wt))
    return size * 0.86 + adv * (len(lines) - 1) + 8 if lines else 0


def blk_icons(c, top, b):
    items = b.get('items', [])[:4]
    k = max(1, len(items))
    w = (RX - TX) / k
    subs = any(it.get('sub') for it in items)
    h = 178 if subs else 150
    if b.get('card', True):
        c.card(TX, top, RX - TX, h)
    for i, it in enumerate(items):
        cx = TX + w * (i + 0.5)
        c.icon(it.get('icon', 'star'), cx, top + 62, it.get('scale', 0.62))
        c.add(c.text(cx, top + 124, it.get('label', ''), 18, c.fg, 800, anchor='middle', limit=cx + w / 2 - 4, left=cx - w / 2 + 4))
        if it.get('sub'):
            c.add(c.text(cx, top + 150, it['sub'], 15, c.muted, anchor='middle', limit=cx + w / 2 - 4, left=cx - w / 2 + 4))
    return h


def blk_raw(c, top, b):
    c.add(f'<g transform="translate(0 {n(top)})">{b.get("svg", "")}</g>')
    if b.get('stub_at') is not None:
        c.stub(top + b['stub_at'])
    return b.get('height', 100)


def blk_spacer(c, top, b):
    return b.get('height', 20)


BLOCKS = {
    'station': blk_station, 'terminus': blk_terminus, 'compact': blk_compact, 'card': blk_card, 'counter': blk_counter,
    'journey': blk_journey, 'quote': blk_quote, 'ring': blk_ring, 'dots': blk_dots, 'exchange': blk_exchange,
    'team': blk_team, 'tokens': blk_tokens, 'compare': blk_compare, 'bars': blk_bars, 'hbars': blk_hbars,
    'bigstat': blk_bigstat, 'plaque': blk_plaque, 'lifebar': blk_lifebar, 'text': blk_text, 'icons': blk_icons,
    'raw': blk_raw, 'spacer': blk_spacer,
}


# ---------------------------------------------------------------- 封面
def draw_cover(c, cov):
    T = c.T
    news = cov.get('news')
    if news:
        c.add(f'<rect x="48" y="44" width="654" height="56" rx="28" fill="{T["INK"]}"/>')
        c.add(f'<circle cx="80" cy="72" r="7" fill="{T["ACCENT_L"]}"><animate attributeName="opacity" values="1;0.15;1" dur="1.6s" repeatCount="indefinite"/></circle>')
        x = 100
        if news.get('date'):
            c.add(c.text(x, 79, news['date'], 18, T['PAPER'], 700, family=MONO, ls=0.5))
            x += c.tw(news['date'], 18, 700, 0.5, MONO) + 22
        ns = 19
        while ns > 15 and x + c.tw(news.get('text', ''), ns, 600) > 690:
            ns -= 0.5
        c.add(c.text(x, 79, news.get('text', ''), ns, T['PAPER'], 600, limit=690))
    name, big, unit = cov.get('name', ''), cov.get('big', ''), cov.get('big_unit', '')
    ns, bs = cov.get('name_size', 140), cov.get('big_size', 136)
    uw = c.tw(unit, 40, 800) if unit else 0
    for _ in range(40):
        bw = c.tw(big, bs, 900, -4) if big else 0
        br = RX - (uw + 6 if unit else 0)
        bl = br - bw
        lim = (bl - 28) if big else RX
        if 40 + c.tw(name, ns, 900, -4) <= lim:
            break
        ns *= 0.96
        bs = max(96, bs * 0.985)
    ns, bs = round(ns), round(bs)
    if cov.get('kicker'):
        c.add(c.text(RX, 198, cov['kicker'], 20, T['GRAY'], 700, anchor='end', ls=3))
    if big:
        c.add(c.text(br, 314, big, bs, T['ACCENT'], 900, anchor='end', ls=-4))
    if unit:
        c.add(c.text(RX, 312, unit, 40, T['ACCENT'], 800, anchor='end'))
    c.add(c.text(40, 314, name, ns, T['INK'], 900, ls=-4, limit=(bl - 16) if big else RX))
    sub, yrs = cov.get('subtitle', '的人生轨迹'), cov.get('years', '')
    ss = 70
    yw = c.tw(yrs, 28, 600) if yrs else 0
    while ss > 44 and 46 + c.tw(sub, ss, 700) > RX - yw - 30:
        ss -= 2
    c.add(c.text(46, 404, sub, ss, T['INK'], 700))
    if yrs:
        c.add(c.text(RX, 404, yrs, 28, T['GRAY2'], 600, anchor='end'))
    if cov.get('route'):
        rs = 22
        while rs > 16 and 48 + c.tw(cov['route'], rs, 400) > RX:
            rs -= 0.5
        c.add(c.text(48, 458, cov['route'], rs, T['GRAY']))
    c.add(f'<line x1="48" y1="494" x2="702" y2="494" stroke="{T["RULE2"]}" stroke-width="1.5"/>')
    c.add(f'<rect x="48" y="527" width="24" height="5" rx="2.5" fill="{T["ACCENT"]}"/>')
    c.add(c.text(84, 535, cov.get('map_title', '人生线路图'), 20, T['INK'], 800, ls=2))
    stops = cov.get('stops', [])
    if cov.get('map_note', f'{len(stops)} 站' if stops else ''):
        c.add(c.text(RX, 535, cov.get('map_note', f'{len(stops)} 站'), 17, T['GRAY2'], 600, anchor='end'))
    if stops:
        draw_snake(c, stops, cov)
    c.add(c.text(650, 964, cov.get('hint', '往下，逐站细看'), 18, T['GRAY2'], anchor='end'))
    c.add(f'<path d="M664,950 l14,12 l14,-12" fill="none" stroke="{T["ACCENT"]}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'
          f'<animateTransform attributeName="transform" type="translate" values="0 -4;0 6;0 -4" dur="1.6s" repeatCount="indefinite"/></path>')


def draw_snake(c, stops, cov):
    T = c.T
    k = len(stops)
    if k > 15:
        c.warn(f'封面站点 {k} 个，最多 15 个，多出来的不画')
        stops = stops[:15]
        k = 15
    cols = cov.get('cols', 5 if k > 8 else 4)
    rows = math.ceil(k / cols)
    gap = 130
    ys = [742 + (r - (rows - 1) / 2) * gap for r in range(rows)]
    xs = [110 + j * (510 / (cols - 1)) for j in range(cols)]
    d = f'M{n(xs[0])},{n(ys[0])}'
    length = 0.0
    for r in range(rows):
        cnt = cols if r < rows - 1 else k - cols * (rows - 1)
        if r > 0:
            d += (f' A65,65 0 0 1 {n(xs[-1])},{n(ys[r])}' if (r - 1) % 2 == 0 else f' A65,65 0 0 0 {n(xs[0])},{n(ys[r])}')
            length += math.pi * 65
        end_x = xs[cnt - 1] if r % 2 == 0 else xs[cols - cnt]
        d += f' H{n(end_x)}'
        length += abs(end_x - (xs[0] if r % 2 == 0 else xs[-1]))
    c.add(f'<path d="{d}" fill="none" stroke="{T["ACCENT"]}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
    spacing = 510 / (cols - 1)
    for idx, st in enumerate(stops):
        r, j = divmod(idx, cols)
        x = xs[j] if r % 2 == 0 else xs[cols - 1 - j]
        y = ys[r]
        kind = st.get('kind') or ('start' if idx == 0 else ('end' if idx == k - 1 else 'stop'))
        if kind in ('start', 'end'):
            c.add(f'<rect x="{n(x - 5)}" y="{n(y - 22)}" width="10" height="44" rx="3" fill="{T["INK"]}"/>')
        elif kind == 'major':
            c.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="12" fill="{T["INK"]}"/><circle cx="{n(x)}" cy="{n(y)}" r="5" fill="{T["ACCENT_L"]}"/>')
        else:
            c.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="8.5" fill="{T["PAPER"]}" stroke="{T["INK"]}" stroke-width="3.2"/>')
        c.add(c.text(x, y - 26, st.get('year', ''), 20, T['INK'], 800, anchor='middle', limit=740, left=10))
        lab = st.get('label', '')
        if c.tw(lab, 18, 700) > spacing - 6:
            c.warn(f'封面站名太长：{lab!r}（每站最多约 {int((spacing - 6) / 18)} 个字）')
        c.add(c.text(x, y + 40, lab, 18, T['ACCENT'] if kind == 'end' else T['GRAY'], 700 if kind == 'end' else None,
                     anchor='middle', limit=745, left=5))
    dur = max(8.0, length / 129)
    c.add(f'<g><animateMotion path="{d}" dur="{dur:.1f}s" rotate="auto" repeatCount="indefinite"/>'
          f'<rect x="-17" y="-8" width="34" height="16" rx="8" fill="{T["INK"]}"/><rect x="-11" y="-3.5" width="7" height="7" rx="1.5" fill="{T["PAPER"]}"/>'
          f'<rect x="-1" y="-3.5" width="7" height="7" rx="1.5" fill="{T["PAPER"]}"/><circle cx="12" cy="0" r="2.6" fill="{T["ACCENT_L"]}"/></g>')


# ---------------------------------------------------------------- 每屏
def header(c, i, y0, scr):
    T = c.T
    dark = scr.get('dark')
    c.add(c.text(RX + 4, y0 + 98, f'{i:02d}', 104, T['DWATER'] if dark else T['WATER'], 900, anchor='end', ls=-3, limit=760))
    c.add(f'<rect x="{TX}" y="{y0 + 80}" width="24" height="5" rx="2.5" fill="{c.acc}"/>')
    c.add(c.text(TX + 36, y0 + 87, scr.get('era', ''), 19, c.acc, 700, ls=2, limit=RX - 110))
    if scr.get('title'):
        ts = scr.get('title_size', 52)
        while ts > 40 and TX + c.tw(scr['title'], ts, 900) > RX:
            ts -= 1
        c.add(c.text(TX, y0 + 152, scr['title'], ts, c.fg, 900))
    if scr.get('sub'):
        c.add(c.text(TX, y0 + 196, scr['sub'], 22, c.muted))


def prepare_blocks(blocks, c):
    out = [dict(b) for b in blocks]
    i = 0
    while i < len(out):
        if out[i].get('type') == 'compact':
            j = i
            while j < len(out) and out[j].get('type') == 'compact':
                j += 1
            yw = max(c.tw(str(b.get('year', '')), 23, 800, 1) for b in out[i:j])
            for b in out[i:j]:
                b.setdefault('_tcol', max(118, round(yw + 26)))
            i = j
        else:
            i += 1
    return out


def default_gap(prev, cur):
    if cur.get('type') == 'tokens':
        return 12
    if prev.get('type') == 'compact' and cur.get('type') == 'compact':
        return 22
    return 26


def run(c, fn, top, b, dry):
    if not dry:
        return fn(c, top, b)
    saved = c.buf, c.measuring
    c.buf, c.measuring = [], True
    try:
        return fn(c, top, b)
    finally:
        c.buf, c.measuring = saved


def draw_screen(c, i, scr, registry):
    y0 = i * SH
    top0 = y0 + (236 if scr.get('sub') else (200 if scr.get('title') else 124))
    bottom = y0 + CONTENT_BOTTOM
    blocks = prepare_blocks(scr.get('blocks', []), c)
    pairs, attached = [], {}
    for b in blocks:
        fn = registry.get(b.get('type'))
        if fn is None:
            c.warn(f'未知块类型 {b.get("type")!r}，跳过')
            continue
        if b.get('attach') and pairs:
            attached.setdefault(len(pairs) - 1, []).append((b, fn))
        else:
            pairs.append((b, fn))
    hs = [run(c, f, y0 + 300, b, True) for b, f in pairs]
    gaps = [float(b.get('gap', default_gap(pairs[k][0], b))) for k, (b, _) in enumerate(pairs[1:])]
    flex = [('gap' not in b and b.get('type') != 'tokens') for b, _ in pairs[1:]]
    total = sum(hs) + sum(gaps)
    avail = bottom - top0
    if total > avail + 0.5:
        room = sum(g - 14 for g, f in zip(gaps, flex) if f and g > 14)
        over = total - avail
        if room >= over:
            k = over / room
            gaps = [g - (g - 14) * k if (f and g > 14) else g for g, f in zip(gaps, flex)]
            total = avail
        else:
            c.warn(f'CROWDED 内容比可用高度多 {over - room:.0f}px：删字、换成 compact，或拆成两屏')
    elif pairs and total / avail < 0.62:
        c.warn(f'SPARSE 内容只占可用高度的 {total / avail:.0%}：加一个插画块或再补一站')
    extra = max(0.0, avail - total)
    nf = sum(flex)
    per = min(extra / nf, 46) if nf else 0
    y = top0
    for k, ((b, f), h) in enumerate(zip(pairs, hs)):
        if k > 0:
            y += gaps[k - 1] + (per if flex[k - 1] else 0)
        run(c, f, y, b, False)
        for (ab, af) in attached.get(k, []):
            run(c, af, y + ab.get('dy', 0), ab, False)
        y += h


# ---------------------------------------------------------------- 组装
def load_plugins(spec, base_dir):
    reg = {}
    for k, p in enumerate(spec.get('plugins', [])):
        path = p if os.path.isabs(p) else os.path.join(base_dir, p)
        sp = importlib.util.spec_from_file_location(f'lifeline_plugin_{k}', path)
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
        reg.update(getattr(mod, 'BLOCKS', {}))
    return reg


def shift_long_animations(chunks, off, min_dur=4.5):
    def _shift(m):
        tag = m.group(0)
        dm = re.search(r'dur="([0-9.]+)s"', tag)
        if not dm or float(dm.group(1)) < min_dur:
            return tag
        bm = re.search(r'begin="([0-9.]+)s"', tag)
        if bm:
            return tag.replace(bm.group(0), f'begin="{float(bm.group(1)) + off:.3f}s"')
        return tag.replace(' dur=', f' begin="{off:.3f}s" dur=', 1)
    return [re.sub(r'<animate(?:Transform|Motion)?\b[^>]*>', _shift, s) for s in chunks]


def build(spec, base_dir='.', video_offsets=None, font=None):
    """返回 (svg, 错误列表, 提醒列表, 屏数)。

    video_offsets[i] 是第 i 屏在视频里到达的秒数：时长 ≥4.5s 的动画会推迟到那一刻开始，
    录屏时观众看到的是每屏动画的开头。写公众号用的长图时不传。
    """
    theme = dict(THEMES.get(spec.get('theme', 'terra'), THEMES['terra']))
    theme.update(spec.get('colors', {}))
    screens = spec.get('screens', [])
    ns = 1 + len(screens)
    c = Ctx(theme, Meter(font or spec.get('font')), ns)
    registry = dict(BLOCKS)
    registry.update(load_plugins(spec, base_dir))
    H = SH * ns
    T = theme

    bgl = [f'<rect width="{W}" height="{H}" fill="{T["PAPER"]}"/>',
           f'<path d="{"".join(f"M15 {y}H750" for y in range(15, H, 30))}" fill="none" stroke="{T["DOT"]}" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="0 30"/>']
    for i, scr in enumerate(screens, 1):
        if scr.get('dark'):
            yd = i * SH
            bgl.append(f'<rect x="0" y="{yd}" width="{W}" height="{SH}" fill="{T["DARK"]}"/>')
            bgl.append(f'<path d="{"".join(f"M15 {y}H750" for y in range(yd + 15, yd + SH, 30))}" fill="none" stroke="{T["DDOT"]}" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="0 30"/>')

    heads = []
    for i, scr in enumerate(screens, 1):
        c.buf, c.screen, c.dark = [], i, bool(scr.get('dark'))
        header(c, i, i * SH, scr)
        heads += c.buf

    per_screen = []
    c.buf, c.screen, c.dark = [], 0, False
    draw_cover(c, spec.get('cover', {}))
    per_screen.append(c.buf)
    for i, scr in enumerate(screens, 1):
        c.buf, c.screen, c.dark, c.y0 = [], i, bool(scr.get('dark')), i * SH
        draw_screen(c, i, scr, registry)
        c.add(c.text(RX, i * SH + 988, f'{i:02d} / {ns - 1:02d}', 15, '#6E7484' if c.dark else T['GRAY3'], family=MONO, anchor='end', ls=1))
        if i == ns - 1 and spec.get('sources'):
            c.add(c.text(TX, i * SH + 990, spec['sources'], 14, T['GRAY3'], limit=600))
        per_screen.append(c.buf)

    spine = []
    if screens:
        end_y = c.terminus_y or ((ns - 1) * SH + 900)
        d = f'M{SPINE},{SH + 62} V{n(end_y)}'
        spine = [f'<path d="{d}" fill="none" stroke="{T["ACCENT"]}" stroke-width="10" stroke-linecap="round"/>',
                 f'<path d="{d}" fill="none" stroke="{T["FLOW"]}" stroke-width="3.4" stroke-linecap="round" stroke-dasharray="22 218" opacity="0.95">'
                 f'<animate attributeName="stroke-dashoffset" values="0;-240" dur="2.2s" repeatCount="indefinite"/></path>',
                 f'<rect x="{SPINE - 24}" y="{SH + 56}" width="48" height="11" rx="3" fill="{T["INK"]}"/>']

    if video_offsets:
        per_screen = [shift_long_animations(chunks, video_offsets[i]) if i < len(video_offsets) and video_offsets[i] > 0 else chunks
                      for i, chunks in enumerate(per_screen)]

    body = bgl + heads + spine + [s for chunks in per_screen for s in chunks]
    style = f'display:block;max-width:750px;margin:0 auto;font-family:{SERIF}'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" style="{style}">\n'
           + '\n'.join(s for s in body if s.strip()) + '\n</svg>')
    errs, warns = lint(svg, spec.get('forbid', []))
    return svg, errs, c.warns + warns, ns


def lint(svg, forbid=()):
    errs, warns = [], []
    for pat, msg in FORBIDDEN_MARKUP:
        if re.search(pat, svg):
            errs.append(msg)
    if '\n\n' in svg or re.search(r'\n\s*\n', svg):
        errs.append('SVG 里有空行，粘进公众号会断开')
    for w in forbid or []:
        if w and w in svg:
            errs.append(f'出现禁用词「{w}」')
    sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', svg)]
    if sizes and min(sizes) < 13:
        errs.append(f'最小字号 {min(sizes)} < 13，手机上看不清')
    for tag in re.findall(r'<animate(?:Transform|Motion)?\b[^>]*>', svg):
        if 'repeatCount="indefinite"' not in tag:
            warns.append('有动画没写 repeatCount="indefinite"，播一次就停')
            break
    kb = len(svg.encode('utf-8')) / 1024
    if kb > 400:
        warns.append(f'体积 {kb:.0f}KB，偏大，公众号编辑器可能变卡')
    return errs, warns


# ---------------------------------------------------------------- 命令行
def _cmd_build(a):
    spec = json.load(open(a.spec, encoding='utf-8'))
    svg, errs, warns, ns = build(spec, os.path.dirname(os.path.abspath(a.spec)), font=a.font)
    out = a.out or os.path.splitext(a.spec)[0] + '.svg'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'written {out}  {ns} 屏（750x{ns * SH}）  {len(svg.encode()) / 1024:.0f}KB  '
          f'{svg.count("<animate")} 个动画')
    for w in warns:
        print('  [提醒] ' + w)
    for e in errs:
        print('  [错误] ' + e)
    if errs or (a.strict and warns):
        sys.exit(1)


def _cmd_lint(a):
    text = open(a.file, encoding='utf-8').read()
    svgs = re.findall(r'<svg.*?</svg>', text, re.S) if a.file.endswith('.md') else [text]
    forbid = [w for w in (a.forbid or '').split(',') if w]
    ok = True
    for k, s in enumerate(svgs, 1):
        errs, warns = lint(s, forbid)
        print(('✗ ' if errs else '✓ ') + f'{a.file} #{k}  {len(s.encode()) / 1024:.0f}KB')
        for e in errs:
            print('   [错误] ' + e)
        for w in warns:
            print('   [提醒] ' + w)
        ok &= not errs
    sys.exit(0 if ok else 1)


def embed(svg, md):
    """把 SVG 放进 Markdown：替换 <!-- lifeline:start -->…<!-- lifeline:end --> 之间的内容，
    或者把 <!-- lifeline --> 标记换成这一对标记加 SVG。重复执行只会更新同一处。"""
    block = f'<!-- lifeline:start -->\n\n{svg.strip()}\n\n<!-- lifeline:end -->'
    pair = re.compile(r'<!-- lifeline:start -->.*?<!-- lifeline:end -->', re.S)
    if pair.search(md):
        return pair.sub(lambda m: block, md, count=1)
    if '<!-- lifeline -->' in md:
        return md.replace('<!-- lifeline -->', block, 1)
    raise ValueError('文章里没有 <!-- lifeline --> 标记：先在想放长图的地方单独起一行写上它')


def _cmd_embed(a):
    svg = open(a.svg, encoding='utf-8').read()
    md = open(a.md, encoding='utf-8').read()
    try:
        out = embed(svg, md)
    except ValueError as e:
        sys.exit(str(e))
    with open(a.md, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'embedded {a.svg} -> {a.md}  {len(svg.encode()) / 1024:.0f}KB')


def _cmd_icons(a):
    open(a.out, 'w', encoding='utf-8').write(ICONS.gallery(THEMES[a.theme]))
    print('written', a.out, len(ICONS.ICONS), 'icons')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('spec')
    b.add_argument('-o', '--out')
    b.add_argument('--font', help='用来量字宽的字体文件（默认找思源宋体）')
    b.add_argument('--strict', action='store_true', help='有提醒也算失败')
    b.set_defaults(fn=_cmd_build)
    l_ = sub.add_parser('lint')
    l_.add_argument('file')
    l_.add_argument('--forbid', help='逗号分隔的禁用词')
    l_.set_defaults(fn=_cmd_lint)
    g = sub.add_parser('icons')
    g.add_argument('out')
    g.add_argument('--theme', default='terra', choices=sorted(THEMES))
    g.set_defaults(fn=_cmd_icons)
    e = sub.add_parser('embed')
    e.add_argument('svg')
    e.add_argument('md')
    e.set_defaults(fn=_cmd_embed)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
