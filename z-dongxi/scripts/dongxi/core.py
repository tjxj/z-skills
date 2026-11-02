"""绘制层：画布、文字测量、时间轴、动画原语、按风格出图的画笔。

约束（公众号可用）：不用 id / defs / url(#) / <style> / <script>，动画只用 SMIL，
所有动画共用一个周期 T，靠 keyTimes 排队，不依赖事件触发。
"""
import html
import math
import random

# 画幅：比例 -> (宽, 高)。3:4 是公众号正文默认
CANVAS = {
    "3:4": (750, 1000),
    "9:16": (750, 1334),
    "1:1": (900, 900),
    "4:3": (1200, 900),
    "16:9": (1280, 720),
}
DEFAULT_RATIO = "3:4"


def esc(s):
    return html.escape(str(s), quote=True)


def n(v):
    """数字转短字符串。"""
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else str(v)


# ---------- 颜色 ----------

def _rgb(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def lum(c):
    def ch(v):
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _rgb(c))
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + .05) / (min(la, lb) + .05)


def is_dark(c):
    return lum(c) < .2


def shade(a, b, t):
    """两色线性混合，t=0 取 a，t=1 取 b。"""
    x, y = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round((p + (q - p) * t) * 255):02X}" for p, q in zip(x, y))


# ---------- 文字 ----------

NARROW = set("il.,:;|!'`()[]{} ")


def char_w(c):
    o = ord(c)
    if o >= 0x2E80 or c in "，。：；！？、（）《》“”‘’—…·×→←↑↓✓✕":
        return 1.0
    if c in NARROW:
        return 0.32
    if c in "mwMW@%":
        return 0.86
    if c.isupper() or c.isdigit():
        return 0.62
    return 0.55


def text_w(s, size):
    return sum(char_w(c) for c in str(s)) * size


def _tokens(s):
    """中文按字切，英文按词切。"""
    out, buf = [], ""
    for c in str(s):
        if ord(c) >= 0x2E80:
            if buf:
                out.append(buf)
                buf = ""
            out.append(c)
        elif c == " ":
            buf += c
            out.append(buf)
            buf = ""
        else:
            buf += c
    if buf:
        out.append(buf)
    return out


def wrap(s, size, maxw, max_lines=3):
    if s is None or s == "":
        return []
    lines, cur = [], ""
    for tk in _tokens(s):
        if text_w(cur + tk, size) <= maxw or not cur:
            cur += tk
        else:
            lines.append(cur.rstrip())
            cur = tk.lstrip()
    if cur:
        lines.append(cur.rstrip())
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_w(last + "…", size) > maxw:
            last = last[:-1]
        lines[-1] = last + "…"
    # 行首不留中文标点
    for i in range(1, len(lines)):
        if lines[i] and lines[i][0] in "，。、：；！？）》”":
            lines[i - 1] += lines[i][0]
            lines[i] = lines[i][1:]
    return [x for x in lines if x]


def fit(s, size, maxw, floor=14):
    """单行放不下就缩字号，最小 floor。"""
    while size > floor and text_w(s, size) > maxw:
        size -= 1
    return size


# ---------- 时间轴 ----------

def _keytimes(pts, T):
    """pts: [(秒, 值)]，补齐首尾并保证 keyTimes 严格递增。"""
    pts = sorted(((max(0.0, min(T, t)), v) for t, v in pts), key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0.0, pts[0][1]))
    if pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    kt, vals, last = [], [], -1.0
    for t, v in pts:
        fr = t / T
        if fr <= last:
            fr = last + 0.0004
        if fr > 1:
            continue
        kt.append(fr)
        vals.append(v)
        last = fr
    kt[0] = 0.0
    if kt[-1] < 1:
        kt.append(1.0)
        vals.append(vals[-1])
    kt[-1] = 1.0
    return ";".join(f"{x:.4f}".rstrip("0").rstrip(".") or "0" for x in kt), ";".join(str(v) for v in vals)


def anim(attr, pts, T, discrete=False):
    kt, vals = _keytimes(pts, T)
    mode = ' calcMode="discrete"' if discrete else ""
    return (f'<animate attributeName="{attr}" values="{vals}" keyTimes="{kt}" dur="{n(T)}s"'
            f' repeatCount="indefinite"{mode}/>')


def motion(d, pts, T, rotate=False):
    kt, vals = _keytimes(pts, T)
    rot = ' rotate="auto"' if rotate else ""
    return (f'<animateMotion path="{d}" keyPoints="{vals}" keyTimes="{kt}" calcMode="linear"'
            f' dur="{n(T)}s" repeatCount="indefinite"{rot}/>')


def ambient(attr, frm, to, dur):
    """与叙事无关的环境动画（流动虚线、光标闪烁）。"""
    return f'<animate attributeName="{attr}" from="{frm}" to="{to}" dur="{n(dur)}s" repeatCount="indefinite"/>'


FADE = 0.3


def show_from(t0, T, d=FADE):
    """t0 前隐藏，之后常亮，周期末淡出。"""
    return [(0, 0), (t0, 0), (t0 + d, 1), (T - 0.5, 1), (T - 0.15, 0)]


def window(t0, t1, T, d=FADE):
    return [(0, 0), (t0, 0), (t0 + d, 1), (max(t0 + d, t1), 1), (max(t0 + d, t1) + d, 0)]


def fade_in(t0, T, d=FADE):
    return anim("opacity", show_from(t0, T, d), T)


# ---------- 几何 ----------

def poly_d(pts, closed=False):
    d = "M" + " L".join(f"{n(x)} {n(y)}" for x, y in pts)
    return d + (" Z" if closed else "")


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def cubic(p0, p1, p2, p3, k=22):
    out = []
    for i in range(k + 1):
        t = i / k
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def quad(p0, c, p1, k=18):
    out = []
    for i in range(k + 1):
        t = i / k
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]))
    return out


def elbow(p, q, r=14, horizontal=False):
    """先竖后横再竖的折线，带圆角；horizontal=True 时先横后竖再横。"""
    if horizontal:
        return [(y, x) for x, y in elbow((p[1], p[0]), (q[1], q[0]), r)]
    mx = (p[1] + q[1]) / 2
    if abs(p[0] - q[0]) < 1:
        return [p, q]
    sx = 1 if q[0] > p[0] else -1
    r = min(r, abs(q[0] - p[0]) / 2, abs(mx - p[1]))
    a = [p, (p[0], mx - r)]
    a += quad((p[0], mx - r), (p[0], mx), (p[0] + sx * r, mx), 6)[1:]
    a += [(q[0] - sx * r, mx)]
    a += quad((q[0] - sx * r, mx), (q[0], mx), (q[0], mx + r), 6)[1:]
    a += [q]
    return a


def arc_pts(cx, cy, r, a0, a1, k=None):
    k = k or max(8, int(abs(a1 - a0) / .08))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / k), cy + r * math.sin(a0 + (a1 - a0) * i / k)) for i in range(k + 1)]


def rect_edge_point(cx, cy, w, h, tx, ty, pad=4):
    """从矩形中心朝 (tx,ty) 方向出发，与矩形边框的交点。"""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2 + pad) / abs(dx) if dx else 1e9
    sy = (h / 2 + pad) / abs(dy) if dy else 1e9
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


# ---------- 画笔 ----------

class Painter:
    def __init__(self, style, name="", seed=11, ratio=DEFAULT_RATIO):
        self.s = style
        self.name = name
        self.rng = random.Random(seed)
        self.tone_i = 0
        self.rough = style.get("shape") == "rough"
        self.ratio = ratio if ratio in CANVAS else DEFAULT_RATIO
        self.W, self.H = CANVAS[self.ratio]
        self.land = self.W > self.H
        pad = 56 if self.land else 44
        self.L, self.R = pad, self.W - pad
        self.CW = self.R - self.L
        self.CX = self.W / 2
        # 字号阶梯：手机上 750 宽缩到约 375，正文不低于 16 才看得清
        self.f = dict(h1=48, node=24, sub=17, label=16, mono=15, small=14, big=40)
        self.dark = is_dark(style["bg"])

    # 颜色
    def on(self, fill):
        """在 fill 上写字用什么颜色：从墨色、底色、黑、白里挑对比最高的。"""
        s = self.s
        if fill in (None, "none"):
            return s["ink"]
        cands = [s["ink"], s["bg"], "#FFFFFF", "#111111"]
        return max(cands, key=lambda c: contrast(c, fill))

    def tone(self, i=None):
        """返回 (填充, 描边)。"""
        tones = self.s.get("tones")
        if not tones:
            return self.s["panel"], self.s["ink"]
        if i is None:
            i = self.tone_i
            self.tone_i += 1
        strokes = self.s.get("tone_strokes")
        return tones[i % len(tones)], (strokes[i % len(strokes)] if strokes else self.s["ink"])

    def role_colors(self, role):
        s = self.s
        acc_st = s["accent"] if s.get("shape") != "cut" else s["ink"]
        if s.get("outline_ink"):
            acc_st = s["ink"]
        a2 = s["accent2"]
        return {
            "node": (s["panel"], s["node_stroke"] if s.get("node_stroke") else s["ink"], s["ink"]),
            "soft": (s["panel2"], s["rule"], self.on(s["panel2"])),
            "accent": (s["accent"], acc_st, s.get("accent_ink") or self.on(s["accent"])),
            "accent2": (a2, a2 if not s.get("outline_ink") else s["ink"], self.on(a2)),
            "dark": (s["ink"], s["ink"], s["bg"]),
            "ghost": ("none", s["rule"], s["muted"]),
        }[role]

    def node_colors(self, role, tone=None):
        """(填充, 描边, 文字, 次要文字)，自动处理色板轮换和对比度。"""
        s = self.s
        f, st, tc = self.role_colors(role)
        if role == "node":
            if isinstance(tone, tuple):
                f, st = tone
            elif isinstance(tone, str):
                f = tone
            elif s.get("tones"):
                f, st = self.tone(tone)
            if contrast(tc, f) < 4:
                tc = self.on(f)
        bgc = f if f != "none" else s["bg"]
        sub = s["muted"] if role in ("node", "ghost", "soft") and contrast(s["muted"], bgc) >= 3.2 else tc
        return f, st, tc, sub

    # 文字
    def font(self, role):
        return {"title": self.s["font_title"], "body": self.s["font_body"], "mono": self.s["font_mono"]}[role]

    def text(self, x, y, s, size=16, role="body", fill=None, anchor="start", weight=None, ls=None, extra=""):
        fill = fill or self.s["ink"]
        w = f' font-weight="{weight}"' if weight else ""
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        fam = self.font(role).replace('"', "'")
        return (f'<text x="{n(x)}" y="{n(y)}" font-family="{fam}" font-size="{n(size)}"{w}{a}{l}'
                f' fill="{fill}"{extra}>{esc(s)}</text>')

    def lines(self, x, y, lines, size, lh=None, **kw):
        lh = lh or size * 1.35
        return "".join(self.text(x, y + i * lh, ln, size, **kw) for i, ln in enumerate(lines))

    def tw(self):
        """标题字重。"""
        return self.s["title_weight"]

    # 手绘笔触
    def _jit(self, a):
        a *= self.s.get("rough_amp", 1)
        return self.rng.uniform(-a, a)

    def _rough_seg(self, p, q, amp=1.6, over=2.0):
        L = math.dist(p, q) or 1
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        nx, ny = -uy, ux
        o1, o2 = self._jit(over), self._jit(over)
        a = (p[0] - ux * o1 + self._jit(amp * .5), p[1] - uy * o1 + self._jit(amp * .5))
        b = (q[0] + ux * o2 + self._jit(amp * .5), q[1] + uy * o2 + self._jit(amp * .5))
        k1, k2 = self._jit(amp), self._jit(amp)
        c1 = (p[0] + (q[0] - p[0]) * .35 + nx * k1, p[1] + (q[1] - p[1]) * .35 + ny * k1)
        c2 = (p[0] + (q[0] - p[0]) * .7 + nx * k2, p[1] + (q[1] - p[1]) * .7 + ny * k2)
        return f"M{n(a[0])} {n(a[1])} C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(b[0])} {n(b[1])}"

    def _rough_poly(self, pts, amp=1.2):
        out = []
        for i, (x, y) in enumerate(pts):
            j = 0 if i in (0, len(pts) - 1) else amp
            out.append((x + self._jit(j), y + self._jit(j)))
        return poly_d(out)

    def stroke_path(self, d_or_pts, color, sw, dash=None, extra="", closed=False):
        """普通路径；手绘风格自动抖动并描两遍，霓虹风格叠光。"""
        dash_a = f' stroke-dasharray="{dash}"' if dash else ""
        base = f' fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round"{dash_a}'
        if isinstance(d_or_pts, str):
            ds = [d_or_pts]
        elif self.rough and not dash:
            pts = list(d_or_pts) + ([d_or_pts[0]] if closed else [])
            ds = [self._rough_poly(pts), self._rough_poly(pts, 1.6)]
        else:
            ds = [poly_d(d_or_pts, closed)]
        out = ""
        if self.s.get("glow"):
            for wmul, op in ((5, .12), (2.4, .28)):
                out += f'<path d="{ds[0]}"{base} stroke-width="{n(sw * wmul)}" opacity="{op}"{extra}/>'
        for i, d in enumerate(ds):
            w = sw if i == 0 else sw * .7
            out += f'<path d="{d}"{base} stroke-width="{n(w)}"{extra}/>'
        return out

    def hachure(self, x, y, w, h, color, gap=7.5, sw=1.7, op=.9):
        segs = []
        c = x + y + gap
        while c < x + w + y + h:
            x0 = max(x, c - (y + h))
            x1 = min(x + w, c - y)
            if x1 - x0 > 2:
                segs.append(f"M{n(x0 + self._jit(1))} {n(c - x0)} L{n(x1)} {n(c - x1 + self._jit(1))}")
            c += gap
        return (f'<path d="{" ".join(segs)}" fill="none" stroke="{color}" stroke-width="{n(sw)}"'
                f' stroke-linecap="round" opacity="{n(op)}"/>')

    # 形状
    def shape_d(self, x, y, w, h, r=None):
        """当前风格下矩形的轮廓路径。"""
        s = self.s
        shp = s.get("shape")
        r = s["radius"] if r is None else r
        if shp == "cut":
            c = min(12, w / 4, h / 4)
            return poly_d([(x + c, y), (x + w, y), (x + w, y + h - c), (x + w - c, y + h), (x, y + h), (x, y + c)], True)
        if shp == "pixel":
            p = 6
            return poly_d([(x + p, y), (x + w - p, y), (x + w - p, y + p), (x + w, y + p), (x + w, y + h - p), (x + w - p, y + h - p),
                           (x + w - p, y + h), (x + p, y + h), (x + p, y + h - p), (x, y + h - p), (x, y + p), (x + p, y + p)], True)
        r = min(r, w / 2, h / 2)
        if r <= 0:
            return f"M{n(x)} {n(y)}H{n(x + w)}V{n(y + h)}H{n(x)}Z"
        return (f"M{n(x + r)} {n(y)}H{n(x + w - r)}A{n(r)} {n(r)} 0 0 1 {n(x + w)} {n(y + r)}V{n(y + h - r)}"
                f"A{n(r)} {n(r)} 0 0 1 {n(x + w - r)} {n(y + h)}H{n(x + r)}A{n(r)} {n(r)} 0 0 1 {n(x)} {n(y + h - r)}"
                f"V{n(y + r)}A{n(r)} {n(r)} 0 0 1 {n(x + r)} {n(y)}Z")

    def box(self, x, y, w, h, role="node", tone=None, sw=None, dash=None, fill=None, stroke=None):
        s = self.s
        f, st, _, _ = self.node_colors(role, tone)
        if fill:
            f = fill
        if stroke:
            st = stroke
        sw = s["stroke"] if sw is None else sw
        if s.get("node_dash") and role in ("node", "soft") and not dash:
            dash = s["node_dash"]
        if s.get("outline") is False and role != "ghost" and not dash:
            sw = 0
        out = ""
        shp = s.get("shape")
        if s.get("shadow") and role != "ghost":
            o = s["shadow"]
            out += f'<path d="{self.shape_d(x + o, y + o, w, h)}" fill="{s.get("shadow_color", s["ink"])}"/>'
        if s.get("soft_shadow") and role != "ghost":
            out += f'<path d="{self.shape_d(x, y + 4, w, h)}" fill="{s["ink"]}" opacity=".06"/>'
            out += f'<path d="{self.shape_d(x, y + 1.5, w, h)}" fill="{s["ink"]}" opacity=".05"/>'
        if s.get("misreg") and role != "ghost":
            out += f'<path d="{self.shape_d(x + 5, y + 5, w, h)}" fill="{s["accent"] if role != "accent" else s["accent2"]}" opacity=".55"/>'
            if role == "node":
                st = s["accent2"]
        if s.get("die") and role != "ghost":
            out += f'<path d="{self.shape_d(x - 5, y - 5, w + 10, h + 10, s["radius"] + 5)}" fill="#FFFFFF"/>'
        if shp == "rough":
            if s.get("hatch_shadow") and role != "ghost":
                o = s["hatch_shadow"]
                out += self.hachure(x + o, y + o, w, h, s["ink"], 4.5, 1.1, .55)
                out += f'<path d="{self.shape_d(x, y, w, h)}" fill="{s["panel"] if role == "node" else f}"/>'
            if f != "none" and s.get("pencil"):
                out += f'<path d="{self.shape_d(x, y, w, h)}" fill="{f}" opacity="{.55 if role == "node" else .9}"/>'
                out += self.hachure(x + 3, y + 3, w - 6, h - 6, shade(f, s["ink"], .28), 6, 1.2, .5)
            elif f != "none":
                if s.get("hachure") and role == "node":
                    out += f'<path d="{self.shape_d(x, y, w, h)}" fill="{f}" opacity=".35"/>'
                    out += self.hachure(x + 3, y + 3, w - 6, h - 6, f)
                else:
                    out += f'<path d="{self.shape_d(x, y, w, h)}" fill="{f}" opacity="{.95 if role != "node" else .6}"/>'
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            dpath = " ".join(self._rough_seg(corners[i], corners[(i + 1) % 4]) for i in range(4))
            dash_a = f' stroke-dasharray="{dash}"' if dash else ""
            out += f'<path d="{dpath}" fill="none" stroke="{st}" stroke-width="{n(sw)}" stroke-linecap="round"{dash_a}/>'
            if not dash:
                dpath2 = " ".join(self._rough_seg(corners[i], corners[(i + 1) % 4], 1.2, 1) for i in range(4))
                out += f'<path d="{dpath2}" fill="none" stroke="{st}" stroke-width="{n(sw * .6)}" stroke-linecap="round" opacity=".8"/>'
            return out + self.pin(x, y, w, role)
        dash_a = f' stroke-dasharray="{dash}"' if dash else ""
        stroke_a = f' stroke="{st}" stroke-width="{n(sw)}"' if sw else ""
        out += f'<path d="{self.shape_d(x, y, w, h)}" fill="{f}"{stroke_a}{dash_a}/>'
        if s.get("glow") and role != "ghost":
            out += f'<path d="{self.shape_d(x - 3, y - 3, w + 6, h + 6, s["radius"] + 3)}" fill="none" stroke="{st if role != "node" else s["accent"]}" stroke-width="5" opacity=".14"/>'
        if s.get("tape") and role in ("node", "accent"):
            cx = x + w / 2
            out += (f'<rect x="{n(cx - 30)}" y="{n(y - 9)}" width="60" height="18" fill="#FFFFFF" opacity=".55"'
                    f' transform="rotate({n(self._jit(5))} {n(cx)} {n(y)})"/>')
        out += self.pin(x, y, w, role)
        if s.get("topbar") and role in ("node", "soft"):
            out += f'<path d="{self.shape_d(x, y, w, 6, min(s["radius"], 3))}" fill="{st if s.get("tone_strokes") else s["accent"]}"/>'
        return out

    def pin(self, x, y, w, role):
        """图钉：卡片顶边中间钉一颗，颜色轮换。"""
        s = self.s
        if not s.get("pin") or role not in ("node", "accent"):
            return ""
        cols = s.get("pin_colors") or [s["accent"], s["accent2"]]
        c = cols[int(x + y) % len(cols)]
        cx = x + min(22, w / 4)
        return (self.circle(cx, y, 6.5, c, s["ink"], 1.3)
                + self.circle(cx - 2, y - 2, 1.8, "#FFFFFF", extra=' opacity=".8"'))

    def lit(self, x, y, w, h, color=None, pad=6):
        """高亮框：叠在卡片上，靠动画控制显隐。"""
        c = color or self.s["accent"]
        x, y, w, h = x - pad, y - pad, w + 2 * pad, h + 2 * pad
        r = self.s["radius"] + pad if self.s.get("shape") not in ("cut", "pixel") else 0
        out = f'<path d="{self.shape_d(x, y, w, h, r)}" fill="{c}" opacity=".16"/>'
        if self.rough:
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            d = " ".join(self._rough_seg(corners[i], corners[(i + 1) % 4], 2, 3) for i in range(4))
            out += f'<path d="{d}" fill="none" stroke="{c}" stroke-width="3.6" stroke-linecap="round"/>'
        else:
            if self.s.get("glow"):
                out += f'<path d="{self.shape_d(x, y, w, h, r)}" fill="none" stroke="{c}" stroke-width="12" opacity=".22"/>'
            out += f'<path d="{self.shape_d(x, y, w, h, r)}" fill="none" stroke="{c}" stroke-width="3.6"/>'
        return out

    def ellipse(self, cx, cy, rx, ry, fill, stroke, sw):
        if not self.rough:
            return f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" fill="{fill}" stroke="{stroke}" stroke-width="{n(sw)}"/>'
        out = f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" fill="{fill}" opacity=".6"/>'
        for amp in (1.6, 2.2):
            pts = []
            st = self.rng.uniform(0, 6.28)
            for i in range(27):
                a = st + i / 24 * 6.4
                pts.append((cx + (rx + self._jit(amp)) * math.cos(a), cy + (ry + self._jit(amp)) * math.sin(a)))
            out += f'<path d="{poly_d(pts)}" fill="none" stroke="{stroke}" stroke-width="{n(sw if amp < 2 else sw * .6)}" stroke-linecap="round"/>'
        return out

    def circle(self, cx, cy, r, fill, stroke="none", sw=0, extra=""):
        st = f' stroke="{stroke}" stroke-width="{n(sw)}"' if stroke != "none" and sw else ""
        return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"{st}{extra}/>'

    def disc(self, cx, cy, r, fill, stroke=None, sw=None):
        """风格化圆：手绘抖动、贴纸白边、硬投影都跟着风格走。"""
        s = self.s
        out = ""
        if s.get("shadow"):
            out += self.circle(cx + s["shadow"] * .7, cy + s["shadow"] * .7, r, s.get("shadow_color", s["ink"]))
        if s.get("die"):
            out += self.circle(cx, cy, r + 5, "#FFFFFF")
        stroke = stroke or (s["ink"] if s.get("outline") is not False else fill)
        sw = s["stroke"] if sw is None else sw
        if self.rough:
            return out + self.ellipse(cx, cy, r, r, fill, stroke, sw)
        return out + self.circle(cx, cy, r, fill, stroke, sw)

    def arrowhead(self, p_prev, p_end, color, size=11):
        ang = math.atan2(p_end[1] - p_prev[1], p_end[0] - p_prev[0])
        a1 = (p_end[0] - size * math.cos(ang - .45), p_end[1] - size * math.sin(ang - .45))
        a2 = (p_end[0] - size * math.cos(ang + .45), p_end[1] - size * math.sin(ang + .45))
        if self.rough:
            return self.stroke_path([a1, p_end, a2], color, self.s["stroke"])
        return f'<path d="{poly_d([a1, p_end, a2], True)}" fill="{color}"/>'

    def edge(self, pts, color=None, arrow=True, dash=None, sw=None):
        color = color or self.s.get("edge", self.s["ink"])
        sw = sw or self.s.get("edge_w", self.s["stroke"])
        out = self.stroke_path(pts, color, sw, dash)
        if arrow:
            out += self.arrowhead(pts[-2], pts[-1], color)
        return out

    def label_chip(self, x, y, s, size=None, fill=None, color=None, anchor="middle"):
        """线上标签：底色块 + 文字。y 为文字基线。"""
        if self.s.get("label") == "italic" and fill is None:
            size = size or 17
            w = text_w(s, size) + 10
            x0 = x - w / 2 if anchor == "middle" else x
            return (f'<rect x="{n(x0)}" y="{n(y - size)}" width="{n(w)}" height="{n(size + 7)}" fill="{self.s["bg"]}" opacity=".92"/>'
                    + self.text(x0 + w / 2, y, s, size, "body", color or self.s["ink"], "middle", 500, extra=' font-style="italic"'))
        size = size or self.f["mono"]
        w = text_w(s, size) + 16
        x0 = x - w / 2 if anchor == "middle" else x
        fill = fill or self.s["bg"]
        r = min(self.s["radius"], 6)
        return (f'<rect x="{n(x0)}" y="{n(y - size - 4)}" width="{n(w)}" height="{n(size + 11)}" rx="{r}" fill="{fill}"/>'
                + self.text(x0 + w / 2, y, s, size, "mono", color or self.s["muted"], "middle", 700))

    def pill(self, x, y, s, fill, color=None, size=None, anchor="start"):
        """胶囊标签，返回 (svg, 宽)。y 为胶囊顶部。"""
        size = size or self.f["small"]
        w = text_w(s, size) + 20
        h = size + 12
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        out = f'<rect x="{n(x0)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(h / 2)}" fill="{fill}"/>'
        out += self.text(x0 + w / 2, y + h / 2 + size * .36, s, size, "mono", color or self.on(fill), "middle", 700)
        return out, w

    def token(self, glyph=None, color=None, r=10, txt=None):
        """沿路径移动的小物件，画在原点，由 animateMotion 搬运。"""
        c = color or self.s["accent"]
        out = ""
        if self.s.get("glow"):
            out += self.circle(0, 0, r * 2.2, c, extra=' opacity=".18"')
        if glyph:
            size = 15
            w = max(30, text_w(glyph, size) + 14)
            out += (f'<rect x="{n(-w / 2)}" y="-14" width="{n(w)}" height="28" rx="6" fill="{c}"'
                    f' stroke="{self.s["ink"] if not self.dark else self.s["bg"]}" stroke-width="1.5"/>')
            out += self.text(0, 5.5, glyph, size, "mono", txt or self.on(c), "middle", 800)
        else:
            out += self.circle(0, 0, r, c, self.s["ink"] if (self.rough or self.s.get("shadow")) else "none", 2)
        return out

    def card(self, x, y, w, h, title, sub=None, role="node", tone=None, size=None, sub_size=None, align="center", tag=None):
        s = self.s
        size = size or self.f["node"]
        sub_size = sub_size or self.f["sub"]
        if tone is None and role == "node" and s.get("tones"):
            tone = self.tone()
        elif isinstance(tone, int) and role == "node" and s.get("tones"):
            tone = self.tone(tone)
        out = self.box(x, y, w, h, role, tone)
        f, _, tc, sc = self.node_colors(role, tone)
        padx = 18
        tl = wrap(title, size, w - 2 * padx, 2)
        if len(tl) == 2 and size > 18:
            size2 = fit(title, size, w - 2 * padx, max(17, size - 5))
            if text_w(title, size2) <= w - 2 * padx:
                size, tl = size2, [title]
        sl = wrap(sub, sub_size, w - 2 * padx, 2) if sub else []
        while sl and (len(tl) * size * 1.22 + len(sl) * sub_size * 1.35 + 6 > h - 14) and len(sl) > 1:
            sl = wrap(sub, sub_size, w - 2 * padx, len(sl) - 1)
        if sl and len(tl) * size * 1.22 + sub_size * 1.35 + 6 > h - 10:
            sl = []
        block = len(tl) * size * 1.22 + (len(sl) * sub_size * 1.35 + 4 if sl else 0)
        ty = y + (h - block) / 2 + size * .9
        ax = x + w / 2 if align == "center" else x + padx
        anchor = "middle" if align == "center" else "start"
        wt = s["title_weight"] if s["title_weight"] < 900 else 800
        out += self.lines(ax, ty, tl, size, size * 1.22, role="title", fill=tc, anchor=anchor, weight=wt)
        if sl:
            out += self.lines(ax, ty + len(tl) * size * 1.22 + 2, sl, sub_size, sub_size * 1.35, role="body", fill=sc, anchor=anchor)
        if tag:
            out += self.text(x + w - 12, y + 20, tag, self.f["small"], "mono", sc, "end", 700)
        return out

    def card_h(self, title, sub, w, size=None, sub_size=None, pad=16):
        size = size or self.f["node"]
        sub_size = sub_size or self.f["sub"]
        tl = len(wrap(title, size, w - 36, 2))
        if tl == 2 and text_w(title, max(17, size - 5)) <= w - 36:
            tl = 1
        sl = len(wrap(sub, sub_size, w - 36, 2)) if sub else 0
        return pad * 2 + tl * size * 1.22 + (sl * sub_size * 1.35 + 4 if sl else 0)

    def num(self, x, y, k, size=None, fill=None, anchor="start"):
        """大号序号 01 02，做视觉锚点。"""
        size = size or self.f["mono"]
        return self.text(x, y, f"{k:02d}", size, "mono", fill or self.s["accent"], anchor, 800)

    # 画布
    def background(self):
        s, W, H = self.s, self.W, self.H
        out = f'<rect x="0" y="0" width="{W}" height="{H}" fill="{s["bg"]}"/>'
        tx = s.get("texture")
        if tx == "dots":
            d = "".join(f"M{x} {y}h0" for y in range(26, H, 26) for x in range(26, W, 26))
            out += f'<path d="{d}" stroke="{s["rule"]}" stroke-width="2" stroke-linecap="round" opacity=".55"/>'
        elif tx == "grid":
            minor = "".join(f"M{x} 0V{H}" for x in range(0, W + 1, 25)) + "".join(f"M0 {y}H{W}" for y in range(0, H + 1, 25))
            major = "".join(f"M{x} 0V{H}" for x in range(0, W + 1, 125)) + "".join(f"M0 {y}H{W}" for y in range(0, H + 1, 125))
            out += f'<path d="{minor}" stroke="{s["rule"]}" stroke-width=".6" opacity=".5"/>'
            out += f'<path d="{major}" stroke="{s["rule"]}" stroke-width="1.2" opacity=".85"/>'
        elif tx == "paper":
            d = "".join(f"M0 {y}H{W}" for y in range(40, H, 34))
            out += f'<path d="{d}" stroke="{s["rule"]}" stroke-width="1" opacity=".55"/>'
            out += f'<path d="M{self.L - 14} 0V{H}" stroke="{s["accent"]}" stroke-width="1.4" opacity=".35"/>'
        elif tx == "lines":
            d = "".join(f"M{x} 40V{H - 40}" for x in range(40, W, 112))
            out += f'<path d="{d}" stroke="{s["rule"]}" stroke-width=".7" opacity=".55"/>'
        elif tx == "grain":
            r = random.Random(3)
            d = "".join(f"M{r.randint(0, W)} {r.randint(0, H)}h0" for _ in range(int(W * H / 530)))
            out += f'<path d="{d}" stroke="{s["ink"]}" stroke-width="1.3" stroke-linecap="round" opacity=".08"/>'
        elif tx == "scan":
            d = "".join(f"M0 {y}H{W}" for y in range(0, H, 4))
            out += f'<path d="{d}" stroke="{s["accent"]}" stroke-width="1" opacity=".05"/>'
        elif tx == "halftone":
            out += "".join(
                f'<circle cx="{x}" cy="{y}" r="{n(max(.4, 4.2 * (1 - math.hypot(W - x, H - y) / (W * .75))))}" fill="{s["accent"]}" opacity=".22"/>'
                for y in range(H - 20, int(H * .45), -22) for x in range(W - 20, int(W * .35), -22)
                if math.hypot(W - x, H - y) < W * .72)
        out += self.deco()
        if s.get("frame"):
            fw = s["frame"]
            out += f'<rect x="{fw / 2}" y="{fw / 2}" width="{W - fw}" height="{H - fw}" rx="{s["radius"] + 2 if s["radius"] < 20 else 0}" fill="none" stroke="{s["ink"]}" stroke-width="{fw}"/>'
        return out

    def deco(self):
        """风格自带的背景装饰，只占角落，不抢主体。"""
        s, W, H = self.s, self.W, self.H
        d = s.get("deco")
        if d == "bauhaus":
            return (f'<circle cx="{W - 70}" cy="{H - 80}" r="120" fill="{s["accent2"]}" opacity=".10"/>'
                    f'<path d="M0 {H} L0 {H - 210} A210 210 0 0 1 210 {H} Z" fill="{s["accent"]}" opacity=".10"/>'
                    f'<rect x="{W - 46}" y="0" width="46" height="{n(H * .32)}" fill="{s["yellow"]}"/>')
        if d == "stars":
            r = random.Random(5)
            return "".join(f'<rect x="{r.randint(0, W)}" y="{r.randint(0, H)}" width="3" height="3" fill="{s["ink"]}" opacity="{r.choice([".25", ".5", ".8"])}"/>'
                           for _ in range(60))
        if d == "blobs":
            return (f'<ellipse cx="{W - 40}" cy="{H - 30}" rx="190" ry="130" fill="{s["tones"][0]}" opacity=".7"/>'
                    f'<ellipse cx="20" cy="{H * .55}" rx="90" ry="140" fill="{s["tones"][1]}" opacity=".6"/>')
        if d == "corner":
            return f'<rect x="0" y="{H - 14}" width="{W}" height="14" fill="{s["accent"]}"/>'
        if d == "torn":
            c, k = s.get("counter", "#DCD6C8"), 14
            top = "".join(f"L{x + k / 2} 12 L{x + k} 0 " for x in range(0, W, k))
            bot = "".join(f"L{x + k / 2} {H - 12} L{x + k} {H} " for x in range(0, W, k))
            r = random.Random(7)
            bars = "".join(f"M{W - 150 + i * 4} {H - 33}v13" for i in range(28) if r.random() > .35)
            return (f'<path d="M0 0 {top}Z" fill="{c}"/><path d="M0 {H} {bot}Z" fill="{c}"/>'
                    f'<path d="{bars}" stroke="{s["ink"]}" stroke-width="2" opacity=".6"/>')
        if d == "aurora":
            return (f'<ellipse cx="{W * .85}" cy="-40" rx="{W * .5}" ry="220" fill="{s["accent"]}" opacity=".10"/>'
                    f'<ellipse cx="{W * .1}" cy="-80" rx="{W * .4}" ry="200" fill="{s["accent2"]}" opacity=".08"/>')
        return ""

    def header(self, kicker, title, subtitle=None, seal=None, animate=True):
        """返回 (svg, 正文起始 y)。"""
        s, L, R, CW = self.s, self.L, self.R, self.CW
        hv = s.get("header", "rule")
        out, x = "", L
        tsize = self.f["h1"] if text_w(title, self.f["h1"]) <= CW - (90 if hv in ("seal", "tag") else 0) else 42
        tmax = CW - (90 if hv in ("seal", "tag") else 0)
        tl = wrap(title, tsize, tmax, 2)
        if len(tl) == 2 and tsize > 38:
            tsize = 38 if text_w(title, 38) > tmax else tsize
            tl = wrap(title, tsize, tmax, 2)
        lh = tsize * 1.18
        top = 40 if not self.land else 34
        ink = s["ink"]
        ky = top + 22
        ty = ky + 20 + tsize * .92 if kicker else top + tsize
        if hv == "band":
            band_h = (ty + (len(tl) - 1) * lh) + (44 if subtitle else 24) + 12
            band_c = s.get("band", s["accent"])
            out += f'<rect x="0" y="0" width="{self.W}" height="{n(band_h)}" fill="{band_c}"/>'
            ink = self.on(band_c)
        if hv == "bar":
            out += f'<rect x="{L}" y="{top}" width="12" height="{n(ty + (len(tl) - 1) * lh - top + 6)}" fill="{s["accent"]}"/>'
            x = L + 28
        if kicker:
            k = ("$ " + kicker) if hv == "prompt" else kicker
            kc = ink if hv == "band" else s["accent"]
            if hv == "highlight":
                pw = text_w(k, self.f["mono"]) + 22
                out += f'<rect x="{x}" y="{ky - 19}" width="{n(pw)}" height="28" fill="{s["ink"]}"/>'
                out += self.text(x + 11, ky, k, self.f["mono"], "mono", s["bg"], weight=800, ls=1.5)
            elif hv == "plate":
                out += self.text(x, ky, k, 16, "body", s["accent"], weight=600, ls=4)
            else:
                out += self.text(x, ky, k, self.f["mono"], "mono", kc, weight=800, ls=2)
        if hv == "receipt":
            return self._receipt_header(kicker, tl, tsize, lh, subtitle, top)
        if hv == "highlight":
            for i, ln in enumerate(tl):
                yy = ty + i * lh
                out += f'<rect x="{x - 6}" y="{n(yy - tsize * .62)}" width="{n(text_w(ln, tsize) + 12)}" height="{n(tsize * .58)}" fill="{s.get("yellow", s["accent2"])}"/>'
        if hv == "riso" or s.get("misreg"):
            out += self.lines(x + 4, ty + 4, tl, tsize, lh, role="title", fill=s["accent"], weight=s["title_weight"], extra=' opacity=".75"')
        out += self.lines(x, ty, tl, tsize, lh, role="title", fill=ink, weight=s["title_weight"])
        y = ty + (len(tl) - 1) * lh
        if hv == "prompt" and animate:
            cx = x + min(CW - 20, text_w(tl[-1], tsize) * 1.04) + 10
            out += (f'<rect x="{n(cx)}" y="{n(y - tsize * .8)}" width="16" height="{n(tsize * .9)}" fill="{s["accent"]}">'
                    f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" dur="1s" repeatCount="indefinite" calcMode="discrete"/></rect>')
        if subtitle:
            y += 40
            sub_c = ink if hv == "band" else s["muted"]
            sl = wrap(subtitle, 19, CW - (x - L), 2)
            ex = ' opacity=".85"' if hv == "band" else ' font-style="italic"' if hv == "plate" else ""
            out += self.lines(x, y, sl, 19, 26, role="body", fill=sub_c, extra=ex)
            y += (len(sl) - 1) * 26
        y += 26
        if hv == "band":
            y += 14
        elif hv == "scribble":
            out += self.stroke_path([(L, y), (L + 220, y + 3), (L + 420, y - 1)], s["accent"], 4)
        elif hv == "double":
            out += f'<path d="M{L} {n(y)}H{R}M{L} {n(y + 6)}H{R}" stroke="{s["ink"]}" stroke-width="1.2"/>'
        elif hv == "double-accent":
            out += f'<path d="M{L} {n(y)}H{R}" stroke="{s["accent"]}" stroke-width="2"/><path d="M{L} {n(y + 6)}H{R}" stroke="{s["accent2"]}" stroke-width="1"/>'
        elif hv == "plain":
            pass
        elif hv == "plate":
            out += self.stroke_path([(L, y), (L + 150, y + 1)], s["ink"], 1.3)
            out += f'<path d="M{L + 164} {n(y)}l5 -5l5 5l-5 5Z" fill="{s["accent"]}"/>'
            out += self.stroke_path([(L + 182, y), (R, y - 1)], s["rule"], 1.1)
        elif hv == "thin":
            out += f'<line x1="{L}" y1="{n(y)}" x2="{R}" y2="{n(y)}" stroke="{s["rule"]}" stroke-width="1.5"/>'
        elif hv == "seal":
            out += self.stroke_path([(L, y), (L + 300, y + 1)], s["ink"], 1.4)
        elif hv == "highlight":
            out += f'<line x1="{L}" y1="{n(y)}" x2="{R}" y2="{n(y)}" stroke="{s["ink"]}" stroke-width="4"/>'
        else:
            out += f'<line x1="{L}" y1="{n(y)}" x2="{R}" y2="{n(y)}" stroke="{s["ink"]}" stroke-width="3"/>'
        if hv == "seal":
            sl2 = (seal or "动悉")[:2]
            out += f'<rect x="{R - 62}" y="{top - 4}" width="62" height="62" rx="4" fill="{s["accent"]}"/>'
            out += self.text(R - 31, top + 22, sl2[0], 22, "title", s["accent_ink"], "middle", 700)
            out += self.text(R - 31, top + 49, sl2[-1], 22, "title", s["accent_ink"], "middle", 700)
        if hv == "tag":
            out += f'<rect x="{R - 160}" y="{top - 6}" width="160" height="36" fill="none" stroke="{s["ink"]}" stroke-width="1.2"/>'
            out += self.text(R - 80, top + 17, "DWG · " + (seal or "A-01"), 14, "mono", s["ink"], "middle", 700)
        return out, y + 30

    def _receipt_header(self, kicker, tl, tsize, lh, subtitle, top):
        """小票抬头：全部居中，星号夹住店名，底下一条虚线。"""
        s, cx = self.s, self.CX
        out, y = "", top + 22
        if kicker:
            out += self.text(cx, y, f"*** {kicker} ***", self.f["mono"], "mono", s["muted"], "middle", 700, 2)
            y += 20
        y += tsize * .92
        for i, ln in enumerate(tl):
            out += self.text(cx, y + i * lh, ln, tsize, "title", s["ink"], "middle", s["title_weight"])
        y += (len(tl) - 1) * lh
        if subtitle:
            y += 38
            sl = wrap(subtitle, 18, self.CW - 40, 2)
            for i, ln in enumerate(sl):
                out += self.text(cx, y + i * 25, ln, 18, "body", s["muted"], "middle")
            y += (len(sl) - 1) * 25
        y += 24
        out += f'<line x1="{self.L}" y1="{n(y)}" x2="{self.R}" y2="{n(y)}" stroke="{s["ink"]}" stroke-width="1.6" stroke-dasharray="7 6"/>'
        return out, y + 30

    def foot(self, text):
        if not text:
            return ""
        return self.text(self.L, self.H - 26, text, self.f["small"], "mono", self.s["muted"])
