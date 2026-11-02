"""页脚小物件：任何图型都能加一排会动的小东西，给画面一点生活气。

用法：spec 里写 "scene": ["cup", "laptop", "plant"]，画面底部留出一条台面，
小物件等距摆开，各自做一点微动画（冒热气、光标闪、沙漏漏沙、小人走路）。
每个物件画在 80×80 的格子里，原点在底边中点，向上为负。
"""
import math

from .core import anim, n, shade, show_from
from .extra import walker
from .layouts import _g

SCENE_H = 118


def _ln(d, c, sw=2, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"{extra}/>'


def _blink(dur, vals="1;.15;1"):
    return f'<animate attributeName="opacity" values="{vals}" dur="{dur}s" repeatCount="indefinite"/>'


def cup(P, c, f):
    """奶茶：杯身、吸管、珍珠，热气一冒一散。"""
    out = _ln("M-20 -58L-16 0H16L20 -58Z", c, 2, f)
    out += _ln("M-22 -58H22", c, 2.4)
    out += _ln("M4 -58L12 -80", c, 2.4)
    out += "".join(P.circle(x, y, 3.4, c) for x, y in ((-8, -8), (0, -6), (8, -9), (-4, -14), (5, -15)))
    for i, x in enumerate((-8, 6)):
        out += _ln(f"M{x} -66c-5 -6 5 -10 0 -16", P.s["muted"], 1.6, extra=' opacity="0"') .replace(
            "/>", f'>{_blink(2.4, "0;.8;0") if not i else _blink(2.4, ".8;0;.8")}</path>')
    return out


def pot(P, c, f):
    """茶壶：壶嘴冒气。"""
    out = _ln("M-24 0C-34 -10 -32 -42 0 -42C32 -42 34 -10 24 0Z", c, 2, f)
    out += _ln("M-26 -30C-40 -30 -42 -14 -28 -10", c, 2)
    out += _ln("M26 -26L42 -40", c, 2.4)
    out += _ln("M-12 -42C-12 -52 12 -52 12 -42", c, 2) + P.circle(0, -53, 3, c)
    out += _ln("M44 -48c-6 -6 6 -10 0 -18", P.s["muted"], 1.6).replace("/>", f">{_blink(1.8, '.9;0;.9')}</path>")
    return out


def hourglass(P, c, f):
    """沙漏：上半沙子随周期变少，下半变多。"""
    T = P.T or 8
    out = _ln("M-18 -72H18M-18 0H18", c, 3)
    out += _ln("M-14 -72C-14 -48 -3 -42 -3 -36C-3 -30 -14 -24 -14 0M14 -72C14 -48 3 -42 3 -36C3 -30 14 -24 14 0", c, 2)
    a = P.s["accent"]
    out += (f'<rect x="-10" y="-42" width="20" height="2" fill="{a}" opacity=".85">'
            + anim("y", [(0, -62), (T * .9, -42)], T) + anim("height", [(0, 22), (T * .9, 2)], T) + "</rect>")
    out += (f'<rect x="-11" y="-24" width="22" height="22" fill="{a}" opacity=".85">'
            + anim("y", [(0, -4), (T * .9, -24)], T) + anim("height", [(0, 2), (T * .9, 22)], T) + "</rect>")
    out += _ln("M0 -36V-4", a, 1.2, extra=' stroke-dasharray="2 3"').replace("/>", f">{_blink(.5)}</path>")
    return out


def plant(P, c, f):
    """盆栽：叶子微微摆。"""
    g = P.s["good"]
    out = _ln("M-18 -26L-14 0H14L18 -26Z", c, 2, f)
    out += _ln("M-21 -26H21", c, 2.4)
    l1 = "M0 -26C-2 -44 -22 -56 -26 -58C-20 -46 -12 -36 0 -30"
    l1b = "M0 -26C-4 -44 -24 -52 -28 -54C-22 -44 -12 -36 0 -30"
    l2 = "M0 -26C2 -50 18 -66 22 -70C22 -54 12 -40 2 -32"
    l2b = "M0 -26C4 -50 22 -62 26 -66C24 -52 12 -40 2 -32"
    out += (f'<path d="{l1}" fill="{g}" fill-opacity=".45" stroke="{c}" stroke-width="2" stroke-linejoin="round">'
            f'<animate attributeName="d" values="{l1};{l1b};{l1}" dur="3s" repeatCount="indefinite"/></path>')
    out += (f'<path d="{l2}" fill="{g}" fill-opacity=".45" stroke="{c}" stroke-width="2" stroke-linejoin="round">'
            f'<animate attributeName="d" values="{l2};{l2b};{l2}" dur="3.4s" repeatCount="indefinite"/></path>')
    return out


def lamp(P, c, f):
    """台灯：灯罩下一圈光晕呼吸。"""
    a = P.s.get("yellow") or "#F2C94C"
    out = (f'<path d="M-30 -2L-10 -40H10L30 -2Z" fill="{a}" opacity=".22">'
           f'<animate attributeName="opacity" values=".12;.32;.12" dur="2.6s" repeatCount="indefinite"/></path>')
    out += _ln("M-16 0H16M0 0V-34M0 -34L14 -48", c, 2.4)
    out += _ln("M4 -52L26 -64L30 -44Z", c, 2, f)
    return out


def bell(P, c, f):
    """服务铃：小锤左右敲。"""
    out = _ln("M-28 0H28", c, 3)
    out += _ln("M-22 -4C-22 -34 22 -34 22 -4Z", c, 2, f)
    out += P.circle(0, -34, 4, c)
    out += (f'<circle cx="0" cy="-2" r="3.5" fill="{P.s["accent"]}">'
            f'<animate attributeName="cx" values="-6;6;-6" dur=".8s" repeatCount="indefinite"/></circle>')
    out += _ln("M30 -36l8 -6M32 -26h10", P.s["accent"], 1.8).replace("/>", f">{_blink(.8, '1;0;1')}</path>")
    return out


def laptop(P, c, f):
    """笔记本：屏幕上一行行字出现，光标闪。"""
    T = P.T or 8
    out = _ln("M-30 -52H30V-12H-30Z", c, 2, f)
    out += _ln("M-38 0H38L32 -12H-32Z", c, 2, P.s["panel2"])
    m = P.s["muted"]
    for i, (w, y) in enumerate(((36, -42), (24, -34), (40, -26))):
        t0 = T * (.15 + .2 * i)
        out += f'<rect x="-22" y="{y}" width="{w}" height="3" fill="{m}">' + anim("width", [(0, 0), (t0, 0), (t0 + .6, w), (T - .4, w), (T - .1, 0)], T) + "</rect>"
    out += f'<rect x="20" y="-28" width="4" height="7" fill="{P.s["accent"]}">{_blink(1, "1;0;1")}</rect>'
    return out


def server(P, c, f):
    """机柜：三排指示灯各闪各的。"""
    out = ""
    for i in range(3):
        y = -72 + i * 24
        out += _ln(f"M-24 {y}H24V{y + 22}H-24Z", c, 2, f)
        out += _ln(f"M-4 {y + 11}H16", P.s["muted"], 2)
        col = (P.s["good"], P.s["accent"], P.s["good"])[i]
        out += f'<circle cx="-14" cy="{y + 11}" r="3.6" fill="{col}">{_blink((.7, 1.3, .9)[i], "1;.2;1")}</circle>'
    return out


def coins(P, c, f):
    """一摞硬币：最上面那枚落下来。"""
    T = P.T or 8
    a = P.s.get("yellow") or "#E8B83A"
    out = ""
    for i in range(4):
        y = -6 - i * 9
        out += P.ellipse(0, y, 22, 7, a, c, 1.8) if not P.rough else f'<ellipse cx="0" cy="{y}" rx="22" ry="7" fill="{a}" stroke="{c}" stroke-width="1.8"/>'
    out += (f'<ellipse cx="0" cy="-42" rx="22" ry="7" fill="{a}" stroke="{c}" stroke-width="1.8">'
            + anim("cy", [(0, -80), (T * .3, -80), (T * .3 + .35, -42)], T)
            + anim("opacity", [(0, 0), (T * .3, 0), (T * .3 + .05, 1)], T) + "</ellipse>")
    return out


def book(P, c, f):
    """摊开的书：右页翻起又落下。"""
    out = _ln("M0 -8C-14 -16 -30 -16 -40 -10V-50C-30 -56 -14 -56 0 -48Z", c, 2, f)
    out += _ln("M0 -8C14 -16 30 -16 40 -10V-50C30 -56 14 -56 0 -48Z", c, 2, f)
    p1 = "M0 -48C10 -56 26 -58 38 -52V-12C26 -18 10 -16 0 -8Z"
    p2 = "M0 -48C4 -62 10 -70 18 -72V-30C10 -28 4 -18 0 -8Z"
    out += (f'<path d="{p1}" fill="{P.s["panel"]}" stroke="{c}" stroke-width="1.6" opacity=".9">'
            f'<animate attributeName="d" values="{p1};{p2};{p1}" dur="3.2s" repeatCount="indefinite"/></path>')
    return out


def sun(P, c, f):
    """太阳：光芒一长一短。"""
    a = P.s.get("yellow") or "#F2B544"
    out = ""
    for k in range(8):
        an = k * math.pi / 4
        x1, y1 = 26 * math.cos(an), -40 + 26 * math.sin(an)
        x2, y2 = 36 * math.cos(an), -40 + 36 * math.sin(an)
        out += _ln(f"M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}", c, 2.2).replace("/>", f">{_blink(1.6 + (k % 2) * .5, '1;.2;1')}</path>")
    out += P.circle(0, -40, 18, a, c, 2)
    return out


def moon(P, c, f):
    """弯月和三颗星，星星轮流闪。"""
    out = _ln("M8 -66C-12 -64 -20 -40 -6 -24C4 -14 18 -16 24 -22C6 -24 -4 -46 8 -66Z", c, 2, P.s.get("yellow") or "#F2D16B")
    for i, (x, y) in enumerate(((-28, -58), (26, -62), (-20, -18))):
        out += _ln(f"M{x - 5} {y}H{x + 5}M{x} {y - 5}V{y + 5}", c, 1.8).replace("/>", f">{_blink(1.2 + i * .4, '1;0;1')}</path>")
    return out


def bulb(P, c, f):
    """灯泡：亮一下暗一下，像想到了什么。"""
    a = P.s.get("yellow") or "#F2C94C"
    out = (f'<circle cx="0" cy="-46" r="30" fill="{a}" opacity=".25">'
           f'<animate attributeName="r" values="22;32;22" dur="2s" repeatCount="indefinite"/>'
           f'<animate attributeName="opacity" values=".1;.35;.1" dur="2s" repeatCount="indefinite"/></circle>')
    out += _ln("M-10 -18C-10 -30 -20 -34 -20 -48C-20 -60 -10 -68 0 -68C10 -68 20 -60 20 -48C20 -34 10 -30 10 -18Z", c, 2, a)
    out += _ln("M-8 -10H8M-6 -3H6", c, 2.4)
    out += _ln("M-5 -30L0 -40L5 -30", c, 1.6)
    return out


def cat(P, c, f):
    """趴着的猫：尾巴甩。"""
    out = _ln("M-30 0C-34 -18 -18 -26 0 -26C14 -26 20 -18 22 -12L30 -14L34 -26L38 -12C42 -6 38 0 30 0Z", c, 2, f)
    out += _ln("M26 -20h0M33 -18h0", c, 3)
    t1 = "M-30 -4C-44 -6 -46 -20 -40 -26"
    t2 = "M-30 -4C-46 -2 -52 -12 -50 -20"
    out += (f'<path d="{t1}" fill="none" stroke="{c}" stroke-width="2.4" stroke-linecap="round">'
            f'<animate attributeName="d" values="{t1};{t2};{t1}" dur="1.8s" repeatCount="indefinite"/></path>')
    return out


PROPS = dict(cup=cup, pot=pot, hourglass=hourglass, plant=plant, lamp=lamp, bell=bell, laptop=laptop, server=server,
             coins=coins, book=book, sun=sun, moon=moon, bulb=bulb, cat=cat)
PROPS_CN = dict(cup="奶茶杯", pot="茶壶", hourglass="沙漏", plant="盆栽", lamp="台灯", bell="服务铃", laptop="笔记本",
                server="机柜", coins="硬币", book="书", sun="太阳", moon="月亮星星", bulb="灯泡", cat="猫", walker="走路小人")


def scene(P, names, y0):
    """在 y0 到 y0+SCENE_H 之间摆一排小物件。walker 不占位，沿台面来回走。"""
    s = P.s
    c = s["ink"]
    base = y0 + SCENE_H - 22
    T = P.T or 8
    out = P.stroke_path([(P.L - 10, base), (P.R + 10, base + 1)], c, 1.8) if P.rough else \
        f'<path d="M{P.L - 10} {n(base)}H{P.R + 10}" stroke="{c}" stroke-width="1.8"/>'
    out += f'<path d="M{P.L - 10} {n(base + 6)}H{P.R + 10}" stroke="{s["rule"]}" stroke-width="1"/>'
    items = [k for k in names if k in PROPS]
    m = len(items)
    tones = s.get("tones") or [s["panel"], s["panel2"]]
    for i, k in enumerate(items):
        x = P.L + P.CW * (i + .5) / max(1, m)
        f = tones[i % len(tones)] if not P.dark else shade(s["panel"], tones[i % len(tones)], .4)
        g = PROPS[k](P, c, f)
        out += _g(f'<g transform="translate({n(x)} {n(base)})">{g}</g>', anim("opacity", show_from(.2 + i * .15, T, .3), T))
    if "walker" in names:
        out += walker(P, [(P.L + 10, base), (P.R - 10, base), (P.L + 10, base)], T, .3, s["ink"])
    return out
