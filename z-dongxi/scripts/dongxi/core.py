"""绘制层：文字测量、时间轴、动画原语、按风格出图的画笔。

约束（公众号可用）：不用 id / defs / url(#) / <style> / <script>，动画只用 SMIL，
所有动画共用一个周期 T，靠 keyTimes 排队，不依赖事件触发。
"""
import html
import math
import random

W, H = 750, 1000


def esc(s):
    return html.escape(str(s), quote=True)


def n(v):
    """数字转短字符串。"""
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else str(v)


# ---------- 文字 ----------

NARROW = set("il.,:;|!'`()[]{} ")


def char_w(c):
    o = ord(c)
    if o >= 0x2E80 or c in "，。：；！？、（）《》“”‘’—…·×→←↑↓":
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


def elbow(p, q, r=14):
    """先竖后横再竖的折线，带圆角。"""
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
    def __init__(self, style, name="", seed=11):
        self.s = style
        self.name = name
        self.rng = random.Random(seed)
        self.tone_i = 0
        self.rough = style.get("shape") == "rough"

    # 颜色
    def tone(self, i=None):
        tones = self.s.get("tones")
        if not tones:
            return self.s["panel"]
        if i is None:
            i = self.tone_i
            self.tone_i += 1
        return tones[i % len(tones)]

    def role_colors(self, role):
        s = self.s
        return {
            "node": (s["panel"], s["ink"], s["ink"]),
            "soft": (s["panel2"], s["rule"], s["ink"]),
            "accent": (s["accent"], s["accent"] if s.get("shape") != "cut" else s["ink"], s["accent_ink"]),
            "accent2": (s["accent2"], s["accent2"], s["bg"] if s["accent2"] == s["ink"] else s["accent_ink"]),
            "dark": (s["ink"], s["ink"], s["bg"]),
            "ghost": ("none", s["rule"], s["muted"]),
        }[role]

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

    # 手绘笔触
    def _jit(self, a):
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
        """普通路径；手绘风格自动抖动并描两遍，霓虹风格叠三层光。"""
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

    def hachure(self, x, y, w, h, color, gap=7.5):
        segs = []
        c = x + y + gap
        while c < x + w + y + h:
            x0 = max(x, c - (y + h))
            x1 = min(x + w, c - y)
            if x1 - x0 > 2:
                segs.append(f"M{n(x0 + self._jit(1))} {n(c - x0)} L{n(x1)} {n(c - x1 + self._jit(1))}")
            c += gap
        return (f'<path d="{" ".join(segs)}" fill="none" stroke="{color}" stroke-width="1.7"'
                f' stroke-linecap="round" opacity=".9"/>')

    # 形状
    def box(self, x, y, w, h, role="node", tone=None, sw=None, dash=None, fill=None):
        s = self.s
        f, st, _ = self.role_colors(role)
        if fill:
            f = fill
        sw = sw or s["stroke"]
        if role == "node" and s.get("tones"):
            f = tone if tone else self.tone()
        out = ""
        shp = s.get("shape")
        if s.get("shadow") and role not in ("ghost",):
            o = s["shadow"]
            if shp == "cut":
                out += f'<path d="{self._cut_d(x + o, y + o, w, h)}" fill="{s["ink"]}"/>'
            else:
                out += f'<rect x="{n(x + o)}" y="{n(y + o)}" width="{n(w)}" height="{n(h)}" rx="{s["radius"]}" fill="{s["ink"]}" opacity=".9"/>'
        if s.get("misreg") and role != "ghost":
            out += (f'<rect x="{n(x + 5)}" y="{n(y + 5)}" width="{n(w)}" height="{n(h)}" rx="{s["radius"]}"'
                    f' fill="{s["accent"] if role != "accent" else s["accent2"]}" opacity=".55"/>')
            if role == "node":
                st = s["accent2"]
        if shp == "rough":
            if f != "none":
                if s.get("hachure") and role == "node":
                    out += f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{s["radius"]}" fill="{f}" opacity=".28"/>'
                    out += self.hachure(x + 3, y + 3, w - 6, h - 6, f)
                else:
                    out += f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{s["radius"]}" fill="{f}" opacity="{.92 if role != "node" else .55}"/>'
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            dpath = " ".join(self._rough_seg(corners[i], corners[(i + 1) % 4]) for i in range(4))
            dash_a = f' stroke-dasharray="{dash}"' if dash else ""
            out += f'<path d="{dpath}" fill="none" stroke="{st}" stroke-width="{n(sw)}" stroke-linecap="round"{dash_a}/>'
            if not dash:
                dpath2 = " ".join(self._rough_seg(corners[i], corners[(i + 1) % 4], 1.2, 1) for i in range(4))
                out += f'<path d="{dpath2}" fill="none" stroke="{st}" stroke-width="{n(sw * .6)}" stroke-linecap="round" opacity=".8"/>'
            return out
        dash_a = f' stroke-dasharray="{dash}"' if dash else ""
        if shp == "cut":
            out += f'<path d="{self._cut_d(x, y, w, h)}" fill="{f}" stroke="{st}" stroke-width="{n(sw)}"{dash_a}/>'
        else:
            out += (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{s["radius"]}" fill="{f}"'
                    f' stroke="{st}" stroke-width="{n(sw)}"{dash_a}/>')
        if s.get("glow") and role != "ghost":
            out += (f'<rect x="{n(x - 3)}" y="{n(y - 3)}" width="{n(w + 6)}" height="{n(h + 6)}" rx="{s["radius"] + 3}"'
                    f' fill="none" stroke="{st if role != "node" else s["accent"]}" stroke-width="5" opacity=".14"/>')
        if s.get("tape") and role in ("node", "accent"):
            cx = x + w / 2
            out += (f'<rect x="{n(cx - 30)}" y="{n(y - 9)}" width="60" height="18" fill="#FFFFFF" opacity=".55"'
                    f' transform="rotate({n(self._jit(5))} {n(cx)} {n(y)})"/>')
        return out

    def _cut_d(self, x, y, w, h, c=12):
        c = min(c, w / 4, h / 4)
        return poly_d([(x + c, y), (x + w, y), (x + w, y + h - c), (x + w - c, y + h), (x, y + h), (x, y + c)], True)

    def lit(self, x, y, w, h, color=None, pad=5):
        """高亮框：叠在卡片上，靠动画控制显隐。"""
        c = color or self.s["accent"]
        x, y, w, h = x - pad, y - pad, w + 2 * pad, h + 2 * pad
        r = self.s["radius"] + pad
        out = f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{r}" fill="{c}" opacity=".12"/>'
        if self.rough:
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            d = " ".join(self._rough_seg(corners[i], corners[(i + 1) % 4], 2, 3) for i in range(4))
            out += f'<path d="{d}" fill="none" stroke="{c}" stroke-width="3.2" stroke-linecap="round"/>'
        else:
            if self.s.get("glow"):
                out += f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{r}" fill="none" stroke="{c}" stroke-width="10" opacity=".22"/>'
            out += f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{r}" fill="none" stroke="{c}" stroke-width="3"/>'
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
        st = f' stroke="{stroke}" stroke-width="{n(sw)}"' if stroke != "none" else ""
        return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"{st}{extra}/>'

    def arrowhead(self, p_prev, p_end, color, size=10):
        ang = math.atan2(p_end[1] - p_prev[1], p_end[0] - p_prev[0])
        a1 = (p_end[0] - size * math.cos(ang - .45), p_end[1] - size * math.sin(ang - .45))
        a2 = (p_end[0] - size * math.cos(ang + .45), p_end[1] - size * math.sin(ang + .45))
        if self.rough:
            return self.stroke_path([a1, p_end, a2], color, self.s["stroke"])
        return f'<path d="{poly_d([a1, p_end, a2], True)}" fill="{color}"/>'

    def edge(self, pts, color=None, arrow=True, dash=None, sw=None):
        color = color or self.s["ink"]
        sw = sw or self.s["stroke"]
        out = self.stroke_path(pts, color, sw, dash)
        if arrow:
            out += self.arrowhead(pts[-2], pts[-1], color)
        return out

    def label_chip(self, x, y, s, size=13, fill=None, color=None, anchor="middle"):
        """线上标签：底色块 + 文字。"""
        w = text_w(s, size) + 14
        x0 = x - w / 2 if anchor == "middle" else x
        fill = fill or self.s["bg"]
        return (f'<rect x="{n(x0)}" y="{n(y - size - 3)}" width="{n(w)}" height="{n(size + 9)}" rx="4" fill="{fill}"/>'
                + self.text(x0 + w / 2, y, s, size, "mono", color or self.s["muted"], "middle"))

    def token(self, glyph=None, color=None, r=9, txt=None):
        """沿路径移动的小物件，画在原点，由 animateMotion 搬运。"""
        c = color or self.s["accent"]
        out = ""
        if self.s.get("glow"):
            out += self.circle(0, 0, r * 2.2, c, extra=' opacity=".18"')
        if glyph:
            w = max(26, text_w(glyph, 13) + 12)
            out += (f'<rect x="{n(-w / 2)}" y="-12" width="{n(w)}" height="24" rx="5" fill="{c}"'
                    f' stroke="{self.s["ink"]}" stroke-width="1.2"/>')
            out += self.text(0, 5, glyph, 13, "mono", txt or self.s["accent_ink"], "middle", 700)
        else:
            out += self.circle(0, 0, r, c, self.s["ink"] if self.rough else "none", 1.5)
        return out

    def card(self, x, y, w, h, title, sub=None, role="node", tone=None, size=19, sub_size=15, align="center", tag=None):
        s = self.s
        out = self.box(x, y, w, h, role, tone)
        _, _, tc = self.role_colors(role)
        if role == "node" and s.get("tones"):
            tc = s["ink"]
        sc = s["muted"] if role in ("node", "soft", "ghost") else tc
        tl = wrap(title, size, w - 28, 2)
        sl = wrap(sub, sub_size, w - 28, 2) if sub else []
        block = len(tl) * size * 1.25 + (len(sl) * sub_size * 1.35 + 6 if sl else 0)
        ty = y + (h - block) / 2 + size * .95
        ax = x + w / 2 if align == "center" else x + 16
        anchor = "middle" if align == "center" else "start"
        out += self.lines(ax, ty, tl, size, size * 1.25, role="title", fill=tc, anchor=anchor, weight=s["title_weight"] if s["title_weight"] < 900 else 800)
        if sl:
            out += self.lines(ax, ty + len(tl) * size * 1.25 + 4, sl, sub_size, sub_size * 1.35, role="body", fill=sc, anchor=anchor)
        if tag:
            out += self.text(x + w - 10, y + 18, tag, 12, "mono", sc, "end", 700)
        return out

    @staticmethod
    def card_h(title, sub, w, size=19, sub_size=15, pad=18):
        tl = len(wrap(title, size, w - 28, 2))
        sl = len(wrap(sub, sub_size, w - 28, 2)) if sub else 0
        return pad * 2 + tl * size * 1.25 + (sl * sub_size * 1.35 + 6 if sl else 0)

    # 画布
    def background(self):
        s = self.s
        out = f'<rect x="0" y="0" width="{W}" height="{H}" fill="{s["bg"]}"/>'
        tx = s.get("texture")
        if tx == "dots":
            d = "".join(f"M{x} {y}h0" for y in range(24, H, 24) for x in range(24, W, 24))
            out += f'<path d="{d}" stroke="{s["rule"]}" stroke-width="2.2" stroke-linecap="round" opacity=".7"/>'
        elif tx == "grid":
            minor = "".join(f"M{x} 0V{H}" for x in range(0, W + 1, 25)) + "".join(f"M0 {y}H{W}" for y in range(0, H + 1, 25))
            major = "".join(f"M{x} 0V{H}" for x in range(0, W + 1, 125)) + "".join(f"M0 {y}H{W}" for y in range(0, H + 1, 125))
            out += f'<path d="{minor}" stroke="{s["rule"]}" stroke-width=".6" opacity=".55"/>'
            out += f'<path d="{major}" stroke="{s["rule"]}" stroke-width="1.2" opacity=".9"/>'
        elif tx == "lines":
            d = "".join(f"M{x} 40V{H - 40}" for x in range(40, W, 112))
            out += f'<path d="{d}" stroke="{s["rule"]}" stroke-width=".7" opacity=".55"/>'
        elif tx == "grain":
            r = random.Random(3)
            d = "".join(f"M{r.randint(0, W)} {r.randint(0, H)}h0" for _ in range(1400))
            out += f'<path d="{d}" stroke="{s["ink"]}" stroke-width="1.3" stroke-linecap="round" opacity=".09"/>'
        elif tx == "scan":
            d = "".join(f"M0 {y}H{W}" for y in range(0, H, 4))
            out += f'<path d="{d}" stroke="{s["accent"]}" stroke-width="1" opacity=".05"/>'
        if s.get("frame"):
            fw = s["frame"]
            out += f'<rect x="{fw / 2}" y="{fw / 2}" width="{W - fw}" height="{H - fw}" rx="{s["radius"] + 2}" fill="none" stroke="{s["ink"]}" stroke-width="{fw}"/>'
        return out

    def header(self, kicker, title, subtitle=None, seal=None, T=None):
        """返回 (svg, 正文起始 y)。"""
        s = self.s
        name = self.name
        out, x = "", 40
        tsize = 34 if text_w(title, 34) <= 670 else 30
        tl = wrap(title, tsize, 670, 2)
        if name == "field":
            out += f'<rect x="40" y="38" width="10" height="{n(40 + len(tl) * tsize * 1.2)}" fill="{s["accent"]}"/>'
            x = 64
        if kicker:
            k = ("$ " + kicker) if name == "terminal" else kicker
            out += self.text(x, 62, k, 14, "mono", s["accent"], weight=700, ls=2)
        ty = 108
        if name == "riso":
            out += self.lines(x + 4, ty + 4, tl, tsize, tsize * 1.2, role="title", fill=s["accent"], weight=s["title_weight"], extra=' opacity=".7"')
        out += self.lines(x, ty, tl, tsize, tsize * 1.2, role="title", fill=s["ink"], weight=s["title_weight"])
        y = ty + (len(tl) - 1) * tsize * 1.2
        if name == "terminal" and T:
            cx = x + min(650, text_w(tl[-1], tsize) * 1.08) + 14
            out += (f'<rect x="{n(cx)}" y="{n(y - tsize * .8)}" width="14" height="{n(tsize * .9)}" fill="{s["accent"]}">'
                    f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" dur="1s" repeatCount="indefinite" calcMode="discrete"/></rect>')
        if subtitle:
            y += 36
            out += self.text(x, y, subtitle, 17, "body", s["muted"])
        y += 22
        if name == "sketch" or name == "chalk":
            out += self.stroke_path([(40, y), (240, y + 2), (420, y - 1)], s["accent"], 3)
        elif name == "editorial":
            out += f'<path d="M40 {n(y)}H710M40 {n(y + 5)}H710" stroke="{s["ink"]}" stroke-width="1"/>'
        elif name == "porcelain":
            out += f'<path d="M40 {n(y)}H710" stroke="{s["accent"]}" stroke-width="1.5"/><path d="M40 {n(y + 5)}H710" stroke="{s["accent2"]}" stroke-width=".8"/>'
        elif name not in ("inkwash",):
            out += f'<line x1="40" y1="{n(y)}" x2="710" y2="{n(y)}" stroke="{s["ink"]}" stroke-width="2.5"/>'
        if name == "inkwash":
            sl = seal or "动悉"
            out += f'<rect x="652" y="36" width="58" height="58" rx="4" fill="{s["accent"]}"/>'
            out += self.text(681, 60, sl[:2][0], 20, "title", s["accent_ink"], "middle", 700)
            out += self.text(681, 86, sl[:2][-1], 20, "title", s["accent_ink"], "middle", 700)
            out += self.stroke_path([(40, y), (300, y + 1)], s["ink"], 1.2)
        if name == "blueprint":
            out += f'<rect x="560" y="34" width="150" height="34" fill="none" stroke="{s["ink"]}" stroke-width="1"/>'
            out += self.text(635, 56, "DWG · " + (seal or "A-01"), 12, "mono", s["ink"], "middle", 700)
        return out, y + 26

    def foot(self, text):
        if not text:
            return ""
        return self.text(40, H - 28, text, 13, "mono", self.s["muted"])
