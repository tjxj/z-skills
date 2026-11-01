"""数据与结构类图型（18 种）：环形占比、四象限、甘特、桑基、分支图、用户旅程、看板、雷达、
韦恩、金字塔、ER、矩形树图、华夫格、数字看板、热力格、对比表、大号步骤、生态轨道。

规则同 layouts.py：共用周期 T，按时间出场，静态渲染即终态，坐标全部从画布推出。
"""
import math

from .core import _rgb, anim, cubic, fit, lum, motion, n, plen, poly_d, show_from, text_w, window, wrap
from .layouts import HOLD, _drawn, _g, _lit, _travel


def pal(P):
    """数据系列用色：先取风格自带的深描边色，再退到强调色组合。"""
    s = P.s
    if s.get("tone_strokes"):
        base = list(s["tone_strokes"])
    elif s.get("tones") and all(lum(c) < .75 for c in s["tones"]):
        base = list(s["tones"])
    else:
        base = [s["accent"], s["accent2"] if s["accent2"] != s["ink"] else s["ink"], s["good"], s["muted"], s["bad"]]
    out = []
    for c in base:
        if c not in out:
            out.append(c)
    return out


def mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round((x + (y - x) * t) * 255):02X}" for x, y in zip(ra, rb))


def _num(v):
    if isinstance(v, (int, float)):
        return f"{v:,}" if isinstance(v, int) else f"{v:g}"
    return str(v)


def _legend(P, x, y, items, colors, w, size=17, cols=1, values=None):
    out = ""
    cw = w / cols
    rh = size + 20
    for i, it in enumerate(items):
        cx, cy = x + (i % cols) * cw, y + (i // cols) * rh
        out += f'<rect x="{n(cx)}" y="{n(cy - size + 2)}" width="{size}" height="{size}" rx="{min(4, P.s["radius"])}" fill="{colors[i % len(colors)]}"/>'
        lab = fit(it, size, cw - size - 90, 14)
        out += P.text(cx + size + 10, cy, it, lab, "body", P.s["ink"], weight=600)
        if values:
            out += P.text(cx + cw - 16, cy, values[i], size, "mono", P.s["muted"], "end", 800)
    return out


# ---------- 1. 环形占比 ----------

def donut(P, sp, top, bot):
    s = P.s
    items = sp["items"]
    tot = sum(i["value"] for i in items)
    cols = pal(P)
    k = len(items)
    leg_h = (k + 1) // 2 * 38 + 10
    if P.land:
        r = min((bot - top) / 2 - 20, P.CW * .22)
        cx, cy = P.L + r + 30, (top + bot) / 2
    else:
        r = min(P.CW / 2 - 40, (bot - top - leg_h) / 2 - 20)
        cx, cy = P.CX, top + (bot - top - leg_h) / 2
    sw = r * .38
    rr = r - sw / 2
    C = 2 * math.pi * rr
    ts, t = [], .5
    for it in items:
        d = .4 + 1.2 * it["value"] / tot
        ts.append((t, t + d))
        t += d + .15
    T = t + .8 + HOLD
    P.T = T
    out = P.circle(cx, cy, rr, "none", s["panel2"], sw)
    if s.get("shadow"):
        out = P.circle(cx + s["shadow"], cy + s["shadow"], r, s.get("shadow_color", s["ink"])) + P.circle(cx, cy, r, s["bg"]) + out
    acc = 0
    gap = 3 if not P.rough else 0
    for i, it in enumerate(items):
        seg = C * it["value"] / tot
        c = it.get("color") or (s["accent"] if it.get("hl") and cols[0] != s["accent"] else cols[i % len(cols)])
        a0, a1 = ts[i]
        L = max(.1, seg - gap)
        out += (f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(rr)}" fill="none" stroke="{c}" stroke-width="{n(sw)}"'
                f' stroke-dasharray="{n(L)} {n(C)}" stroke-dashoffset="{n(-acc)}" transform="rotate(-90 {n(cx)} {n(cy)})">'
                + anim("stroke-dasharray", [(0, f"0 {n(C)}"), (a0, f"0 {n(C)}"), (a1, f"{n(L)} {n(C)}"), (T - .5, f"{n(L)} {n(C)}"), (T - .15, f"0 {n(C)}")], T)
                + "</circle>")
        mid = -math.pi / 2 + 2 * math.pi * (acc + seg / 2) / C
        pct = it["value"] / tot * 100
        if pct >= 6:
            lx, ly = cx + rr * math.cos(mid), cy + rr * math.sin(mid)
            out += _g(P.text(lx, ly + 6, f"{pct:.0f}%", 17 if pct < 15 else 20, "mono", P.on(c), "middle", 800), anim("opacity", show_from(a1, T, .2), T))
        acc += seg
    if not P.rough and s["stroke"]:
        out += P.circle(cx, cy, r, "none", s["ink"] if s.get("shadow") or s.get("outline_ink") else "none", 2)
        out += P.circle(cx, cy, r - sw, "none", s["ink"] if s.get("shadow") or s.get("outline_ink") else "none", 2)
    c = sp.get("center") or {}
    hl = next((i for i, it in enumerate(items) if it.get("hl")), None)
    big = c.get("value") or (f'{items[hl]["value"] / tot * 100:.0f}%' if hl is not None else _num(tot) + sp.get("unit", ""))
    out += P.text(cx, cy + 14, big, fit(big, 54, rr * 1.3, 28), "title", s["accent"], "middle", 900)
    if c.get("title") or hl is not None:
        out += P.text(cx, cy - 34, c.get("title") or items[hl]["label"], fit(c.get("title") or items[hl]["label"], 18, rr * 1.3, 14), "body", s["muted"], "middle", 700)
    if c.get("sub"):
        out += P.text(cx, cy + 46, c["sub"], 15, "mono", s["muted"], "middle")
    labels = [it["label"] for it in items]
    vals = [it.get("text") or f'{_num(it["value"])}{sp.get("unit", "")}' for it in items]
    colors = [it.get("color") or cols[i % len(cols)] for i, it in enumerate(items)]
    if P.land:
        lx = cx + r + 70
        lw = P.R - lx
        rh = min(64, (bot - top) / k)
        ly = (top + bot) / 2 - rh * k / 2 + rh / 2
        for i, it in enumerate(items):
            y = ly + i * rh
            g = f'<rect x="{n(lx)}" y="{n(y - 16)}" width="22" height="22" rx="{min(5, s["radius"])}" fill="{colors[i]}"/>'
            g += P.text(lx + 36, y + 3, labels[i], fit(labels[i], 22, lw - 200, 15), "title", s["ink"], weight=700)
            g += P.text(P.R, y + 3, vals[i], 22, "mono", s["accent"] if it.get("hl") else s["ink"], "end", 800)
            g += f'<path d="M{n(lx)} {n(y + rh / 2 - 4)}H{n(P.R)}" stroke="{s["rule"]}" stroke-width="1"/>'
            out += _g(g, anim("opacity", show_from(ts[i][0], T, .25), T))
    else:
        ly = bot - leg_h + 30
        for i in range(k):
            out += _g(_legend(P, P.L + (i % 2) * (P.CW / 2), ly + (i // 2) * 38, [labels[i]], [colors[i]], P.CW / 2 - 10, 18, 1, [vals[i]]),
                      anim("opacity", show_from(ts[i][0], T, .25), T))
    return out, T


# ---------- 2. 四象限 ----------

def quadrant(P, sp, top, bot):
    s = P.s
    pts = sp["points"]
    ax = sp.get("axes", {})
    qs = sp.get("quadrants", ["", "", "", ""])
    sy = min(P.CW - 40, bot - top - 60)
    wide = P.land and not sp.get("notes")
    sx = min(P.CW - 80, sy * 1.7) if wide else sy
    x0 = P.CX - sx / 2 + 20 if not (P.land and sp.get("notes")) else P.L + 40
    y0 = top + 10
    hx, hy = sx / 2, sy / 2
    ts = [.9 + i * .55 for i in range(len(pts))]
    T = ts[-1] + 1 + HOLD
    P.T = T
    out = ""
    fills = [s["panel2"], s["panel"], s["panel"], s["panel2"]]
    if s.get("tones"):
        fills = [P.tone(i)[0] for i in range(4)]
    best = sp.get("best", 1)
    for q in range(4):
        qx, qy = x0 + (q % 2) * hx, y0 + (q // 2) * hy
        f = fills[q] if q != best else mix(s["accent"], s["bg"], .82)
        out += P.box(qx, qy, hx, hy, "node", None, fill=f, sw=s["stroke"] or 1.5)
        if qs[q]:
            out += P.text(qx + (18 if q % 2 == 0 else hx - 18), qy + (36 if q < 2 else hy - 18), qs[q], fit(qs[q], 22, hx - 36, 15),
                          "title", s["accent"] if q == best else s["muted"], "start" if q % 2 == 0 else "end", 800)
    out += P.stroke_path([(x0 - 6, y0 + sy), (x0 + sx + 16, y0 + sy)], s["ink"], 2.4)
    out += P.arrowhead((x0, y0 + sy), (x0 + sx + 18, y0 + sy), s["ink"])
    out += P.stroke_path([(x0, y0 + sy + 6), (x0, y0 - 16)], s["ink"], 2.4)
    out += P.arrowhead((x0, y0 + sy), (x0, y0 - 18), s["ink"])
    xl, yl = ax.get("x", ["", ""]), ax.get("y", ["", ""])
    out += P.text(x0 + 4, y0 + sy + 30, xl[0], 16, "mono", s["muted"], weight=700)
    out += P.text(x0 + sx, y0 + sy + 30, xl[1], 16, "mono", s["ink"], "end", 800)
    if ax.get("x_name"):
        out += P.text(x0 + hx, y0 + sy + 30, ax["x_name"], 16, "mono", s["muted"], "middle", 700)
    out += P.text(x0 - 12, y0 + sy - 6, yl[0], 16, "mono", s["muted"], "end", 700, extra=f' transform="rotate(-90 {n(x0 - 12)} {n(y0 + sy - 6)})"')
    out += P.text(x0 - 12, y0 + 4, yl[1], 16, "mono", s["ink"], "end", 800, extra=f' transform="rotate(-90 {n(x0 - 12)} {n(y0 + 4)})"')
    for i, p in enumerate(pts):
        px, py = x0 + sx * p["x"], y0 + sy * (1 - p["y"])
        hl = p.get("hl")
        c = s["accent"] if hl else (p.get("color") or s["ink"])
        r = 13 if hl else 9
        g = P.disc(px, py, r, c, s["ink"] if not P.dark else s["bg"], 2)
        lab = p["label"]
        tx = px + r + 8
        anchor = "start"
        if tx + text_w(lab, 17) > x0 + sx - 6:
            tx, anchor = px - r - 8, "end"
        g += P.label_chip(tx + (text_w(lab, 17) / 2 + 8) * (1 if anchor == "start" else -1), py + 6, lab, 17, s["bg"] if not hl else s["accent"],
                          s["ink"] if not hl else P.on(s["accent"]))
        out += _g(g, anim("opacity", show_from(ts[i], T, .25), T))
        if hl:
            out += (f'<circle cx="{n(px)}" cy="{n(py)}" r="{r}" fill="none" stroke="{c}" stroke-width="3" opacity="0">'
                    + anim("r", [(0, r), (ts[i], r), (ts[i] + .8, r + 26)], T) + anim("opacity", [(0, 0), (ts[i], .8), (ts[i] + .8, 0)], T) + "</circle>")
    if P.land and sp.get("notes"):
        nx = x0 + sx + 70
        for j, note in enumerate(sp["notes"]):
            out += _g(P.card(nx, top + 20 + j * 120, P.R - nx, 100, note.get("title", ""), note.get("sub"), note.get("role", "node"), size=21, sub_size=16, align="left"),
                      anim("opacity", show_from(ts[-1] + .3 + j * .3, T, .3), T))
    return out, T


# ---------- 3. 甘特图 ----------

def gantt(P, sp, top, bot):
    s = P.s
    tasks = sp["tasks"]
    k = len(tasks)
    t0v = min(t["start"] for t in tasks)
    t1v = sp.get("end") or max(t["end"] for t in tasks)
    labw = min(P.CW * (.3 if not P.land else .24), 260)
    x0, x1 = P.L + labw, P.R
    groups = []
    for t in tasks:
        g = t.get("group", "")
        if g not in groups:
            groups.append(g)
    room = (34 if sp.get("now") is not None else 0) + (40 if len(groups) > 1 else 0)
    rh = min(70, (bot - top - 46 - room) / k)
    y0 = top + 46
    cols = pal(P)
    span = t1v - t0v or 1
    X = lambda v: x0 + (x1 - x0) * (v - t0v) / span
    ts = [.5 + i * .45 for i in range(k)]
    T = ts[-1] + 1.4 + HOLD
    P.T = T
    out = ""
    ticks = sp.get("ticks") or list(range(int(t0v), int(t1v) + 1, max(1, int(span // 8) or 1)))
    unit = sp.get("unit", "")
    for v in ticks:
        x = X(v)
        out += f'<path d="M{n(x)} {n(y0 - 8)}V{n(y0 + rh * k)}" stroke="{s["rule"]}" stroke-width="1" stroke-dasharray="2 5"/>'
        lab = sp.get("tick_labels", {}).get(str(v)) if isinstance(sp.get("tick_labels"), dict) else None
        out += P.text(x, y0 - 16, lab or f"{v}{unit}", 15, "mono", s["muted"], "middle", 700)
    for i, t in enumerate(tasks):
        y = y0 + i * rh
        gi = groups.index(t.get("group", ""))
        c = s["accent"] if t.get("hl") else cols[gi % len(cols)]
        out += P.text(P.L, y + rh / 2 + 7, t["name"], fit(t["name"], 19, labw - 16, 14), "title", s["ink"], weight=700)
        if i % 2 == 0:
            out += f'<rect x="{n(P.L - 8)}" y="{n(y)}" width="{n(P.CW + 16)}" height="{n(rh)}" fill="{s["panel2"]}" opacity=".45"/>'
        bh = min(34, rh - 18)
        by = y + (rh - bh) / 2
        if t["end"] == t["start"]:
            cx = X(t["start"])
            d = poly_d([(cx, by - 4), (cx + bh / 2 + 4, by + bh / 2), (cx, by + bh + 4), (cx - bh / 2 - 4, by + bh / 2)], True)
            out += _g(f'<path d="{d}" fill="{c}" stroke="{s["ink"]}" stroke-width="2"/>'
                      + P.text(cx + bh / 2 + 10, by + bh / 2 + 6, t.get("label", ""), 15, "mono", s["ink"], weight=700),
                      anim("opacity", show_from(ts[i] + .3, T, .2), T))
            continue
        xa, xb = X(t["start"]), X(t["end"])
        w = xb - xa
        r = min(s["radius"], bh / 2)
        stroke = f' stroke="{s["ink"]}" stroke-width="2"' if s.get("shadow") or P.rough or s.get("outline_ink") else ""
        if s.get("shadow"):
            out += f'<rect x="{n(xa + 4)}" y="{n(by + 4)}" width="{n(w)}" height="{n(bh)}" rx="{n(r)}" fill="{s.get("shadow_color", s["ink"])}" opacity="0">' + anim("opacity", show_from(ts[i] + .7, T, .1), T) + "</rect>"
        out += (f'<rect x="{n(xa)}" y="{n(by)}" width="{n(w)}" height="{n(bh)}" rx="{n(r)}" fill="{c}"{stroke}>'
                + anim("width", [(0, 0), (ts[i], 0), (ts[i] + .7, n(w)), (T - .5, n(w)), (T - .15, 0)], T) + "</rect>")
        lab = t.get("label") or f'{_num(t["end"] - t["start"])}{unit}'
        inside = text_w(lab, 15) + 16 < w
        out += _g(P.text(xa + 10 if inside else xb + 8, by + bh / 2 + 5.5, lab, 15, "mono", P.on(c) if inside else s["ink"], weight=800),
                  anim("opacity", show_from(ts[i] + .6, T, .2), T))
        for dep in t.get("after", []) if isinstance(t.get("after"), list) else ([t["after"]] if t.get("after") is not None else []):
            j = dep if isinstance(dep, int) else next(q for q, tt in enumerate(tasks) if tt["name"] == dep)
            pa = (X(tasks[j]["end"]), y0 + j * rh + rh / 2 + bh / 2 - 2)
            pts = [pa, (pa[0], by + bh / 2), (xa - 6, by + bh / 2)]
            out += _drawn(P, pts, s["muted"], 1.6, ts[i] - .3, ts[i], T, arrow=True)
    if sp.get("now") is not None:
        x = X(sp["now"])
        out += _g(P.stroke_path([(x, y0 - 30), (x, y0 + rh * k + 6)], s["bad"], 2.4, dash="6 4")
                  + P.pill(x, y0 + rh * k + 10, sp.get("now_label", "今天"), s["bad"], size=14, anchor="middle")[0],
                  anim("opacity", show_from(ts[-1] + .8, T, .3), T))
    if len(groups) > 1:
        out += _legend(P, P.L, bot - 6, groups, cols, P.CW, 16, min(4, len(groups)))
    return out, T


# ---------- 4. 桑基流向 ----------

def sankey(P, sp, top, bot):
    s = P.s
    flows = sp["flows"]
    names = []
    for f in flows:
        for k in (f["from"], f["to"]):
            if k not in names:
                names.append(k)
    rank = {k: 0 for k in names}
    for _ in names:
        for f in flows:
            rank[f["to"]] = max(rank[f["to"]], rank[f["from"]] + 1)
    R = max(rank.values()) + 1
    cols = [[k for k in names if rank[k] == r] for r in range(R)]
    vin = {k: sum(f["value"] for f in flows if f["to"] == k) for k in names}
    vout = {k: sum(f["value"] for f in flows if f["from"] == k) for k in names}
    val = {k: max(vin[k], vout[k]) for k in names}
    gap = 26
    avail = bot - top - 20
    scale = min((avail - gap * (len(c) - 1)) / sum(val[k] for k in c) for c in cols)
    bw = 22
    xs = [P.L + (P.CW - bw) * r / (R - 1) for r in range(R)]
    geo = {}
    for r, c in enumerate(cols):
        hsum = sum(val[k] * scale for k in c) + gap * (len(c) - 1)
        y = top + 10 + (avail - hsum) / 2
        for k in c:
            h = val[k] * scale
            geo[k] = (xs[r], y, h)
            y += h + gap
    cl = pal(P)
    ncol = {k: (sp.get("colors", {}).get(k) or cl[i % len(cl)]) for i, k in enumerate(names)}
    tcol = [.5 + r * 1.3 for r in range(R)]
    T = tcol[-1] + 1 + HOLD
    P.T = T
    out = ""
    off_o = {k: 0 for k in names}
    off_i = {k: 0 for k in names}
    unit = sp.get("unit", "")
    for f in sorted(flows, key=lambda f: (rank[f["from"]], geo[f["from"]][1], geo[f["to"]][1])):
        a, b = f["from"], f["to"]
        xa, ya, _ = geo[a]
        xb, yb, _ = geo[b]
        h = f["value"] * scale
        y1, y2 = ya + off_o[a], yb + off_i[b]
        off_o[a] += h
        off_i[b] += h
        xa += bw
        mx = (xa + xb) / 2
        d = (f"M{n(xa)} {n(y1)}C{n(mx)} {n(y1)} {n(mx)} {n(y2)} {n(xb)} {n(y2)}V{n(y2 + h)}"
             f"C{n(mx)} {n(y2 + h)} {n(mx)} {n(y1 + h)} {n(xa)} {n(y1 + h)}Z")
        c = s["accent"] if f.get("hl") else ncol[a]
        op = .55 if f.get("hl") else .3
        t0 = tcol[rank[a]] + .3
        out += f'<path d="{d}" fill="{c}" opacity="{op}">' + anim("opacity", [(0, 0), (t0, 0), (t0 + .7, op), (T - .5, op), (T - .15, 0)], T) + "</path>"
        if h > 8:
            mid = cubic((xa, y1 + h / 2), (mx, y1 + h / 2), (mx, y2 + h / 2), (xb, y2 + h / 2), 20)
            for q in range(2):
                out += _travel(P, mid, [(t0 + q * .35, 0), (t0 + .9 + q * .35, 1)], T, None, c)
    for k in names:
        x, y, h = geo[k]
        r = rank[k]
        g = P.box(x, y, bw, max(h, 3), "node", None, fill=ncol[k], stroke=s["ink"] if not P.dark else ncol[k], sw=1.5)
        lab = k
        v = f"{_num(val[k])}{unit}"
        if r == R - 1:
            tx, anc = x - 10, "end"
        else:
            tx, anc = x + bw + 10, "start"
        size = 19 if h > 30 else 16
        cw = text_w(lab, size) + 18
        bx = tx - (cw if anc == "end" else 0)
        g += f'<rect x="{n(bx - 2)}" y="{n(y + h / 2 - size - 6)}" width="{n(max(cw, text_w(v, 15) + 18) + 4)}" height="{n(size + 26 if h > 44 else size + 12)}" rx="5" fill="{s["bg"]}" opacity=".88"/>'
        g += P.text(tx + (6 if anc == "start" else -6), y + h / 2 + (0 if h > 44 else 3), lab, size, "title", s["ink"], anc, 800)
        if h > 44:
            g += P.text(tx + (6 if anc == "start" else -6), y + h / 2 + 18, v, 15, "mono", s["muted"], anc, 700)
        out += _g(g, anim("opacity", show_from(tcol[r], T, .3), T))
    return out, T


# ---------- 5. 分支图（git） ----------

def gitgraph(P, sp, top, bot):
    s = P.s
    br = sp["branches"]
    names = [b["name"] for b in br]
    cm = sp["commits"]
    k = len(cm)
    lane = 58
    lx = {nm: P.L + 22 + i * lane for i, nm in enumerate(names)}
    tx = P.L + 22 + len(names) * lane + 10
    step = min(76, (bot - top - 60) / k)
    y0 = top + 40
    cl = pal(P)
    bc = {b["name"]: b.get("color") or cl[i % len(cl)] for i, b in enumerate(br)}
    ts = [.6 + i * .7 for i in range(k)]
    T = ts[-1] + 1 + HOLD
    P.T = T
    out = ""
    for nm in names:
        out += P.pill(lx[nm], top - 2, nm, bc[nm], size=14, anchor="middle")[0]
    last = {}
    pos = []
    for i, c in enumerate(cm):
        y = y0 + i * step
        x = lx[c["branch"]]
        pos.append((x, y))
        prev = last.get(c["branch"])
        col = bc[c["branch"]]
        if prev is not None:
            px, py = pos[prev]
            out += _drawn(P, [(px, py + 13), (x, y - 13)], col, 4, ts[i] - .45, ts[i], T)
        if c.get("merge"):
            m = c["merge"]
            if m in last:
                mx, my = pos[last[m]]
                pts = cubic((mx, my + 13), (mx, my + step * .8), (x, y - step * .6), (x, y - 13), 14)
                out += _drawn(P, pts, bc[m], 4, ts[i] - .45, ts[i], T)
        last[c["branch"]] = i
    for i, c in enumerate(cm):
        x, y = pos[i]
        col = bc[c["branch"]]
        hl = c.get("hl") or c.get("tag")
        g = P.circle(x, y, 13 if hl else 11, s["bg"], col, 4)
        g += _g(P.circle(x, y, 13 if hl else 11, col), anim("opacity", show_from(ts[i], T, .15), T), base_opacity=0)
        msg = c["msg"]
        size = 19 if hl else 18
        mw = P.R - tx - (text_w(c["tag"], 14) + 40 if c.get("tag") else 0)
        g2 = P.text(tx, y + 6, msg, fit(msg, size, mw, 14), "title" if hl else "body", s["ink"], weight=800 if hl else 600)
        if c.get("tag"):
            g2 += P.pill(P.R, y - 13, c["tag"], s["accent"], size=14, anchor="end")[0]
        out += g + _g(g2, anim("opacity", show_from(ts[i], T, .25), T))
        out += f'<path d="M{n(x + 16)} {n(y)}H{n(tx - 8)}" stroke="{s["rule"]}" stroke-width="1" stroke-dasharray="2 4"/>'
    for nm in names:
        firsts = [i for i, c in enumerate(cm) if c["branch"] == nm]
        frm = next((b.get("from") for b in br if b["name"] == nm), None)
        if firsts and frm:
            i = firsts[0]
            prior = [j for j in range(i) if cm[j]["branch"] == frm]
            if prior:
                px, py = pos[prior[-1]]
                x, y = pos[i]
                pts = cubic((px, py + 13), (px, py + step * .5), (x, y - step * .6), (x, y - 13), 14)
                out = _drawn(P, pts, bc[nm], 4, ts[i] - .45, ts[i], T) + out
    return out, T


# ---------- 6. 用户旅程 ----------

def journey(P, sp, top, bot):
    s = P.s
    st = sp["stages"]
    k = len(st)
    ts = [.6 + i * .8 for i in range(k)]
    T = ts[-1] + 1.2 + HOLD
    P.T = T
    out = ""
    faces = sp.get("scale", ["很糟", "不爽", "一般", "顺手", "惊喜"])
    good, bad = s["good"], s["bad"]
    colf = lambda v: bad if v <= 2 else (s["muted"] if v == 3 else good)
    if P.land:
        gy0, gy1 = top + 20, top + (bot - top) * .48
        step = P.CW / k
        Y = lambda v: gy1 - (gy1 - gy0) * (v - 1) / 4
        for v in range(1, 6):
            out += f'<path d="M{n(P.L)} {n(Y(v))}H{n(P.R)}" stroke="{s["rule"]}" stroke-width="1" stroke-dasharray="2 6"/>'
        pts = [(P.L + step * (i + .5), Y(x["score"])) for i, x in enumerate(st)]
        cw = step - 18
        for i, x in enumerate(st):
            cx = pts[i][0]
            h = bot - gy1 - 40
            g = P.card(cx - cw / 2, gy1 + 36, cw, h, x["title"], x.get("sub"), "accent" if x.get("hl") else "node", size=20, sub_size=15)
            out += _g(g, anim("opacity", show_from(ts[i], T, .3), T))
    else:
        gx0, gx1 = P.L + P.CW * .58, P.R - 10
        step = (bot - top - 40) / k
        X = lambda v: gx0 + (gx1 - gx0) * (v - 1) / 4
        for v in range(1, 6):
            out += f'<path d="M{n(X(v))} {n(top + 26)}V{n(bot)}" stroke="{s["rule"]}" stroke-width="1" stroke-dasharray="2 6"/>'
            if v in (1, 3, 5):
                out += P.text(X(v), top + 14, faces[v - 1], 14, "mono", colf(v), "middle", 800)
        pts = [(X(x["score"]), top + 40 + step * (i + .5)) for i, x in enumerate(st)]
        cw = gx0 - P.L - 30
        for i, x in enumerate(st):
            cy = pts[i][1]
            h = min(step - 14, P.card_h(x["title"], x.get("sub"), cw, 21, 15) + 4)
            g = P.card(P.L, cy - h / 2, cw, h, x["title"], x.get("sub"), "accent" if x.get("hl") else "node", size=21, sub_size=15, align="left")
            out += _g(g, anim("opacity", show_from(ts[i], T, .3), T))
    smooth = []
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        if P.land:
            mx = (p[0] + q[0]) / 2
            seg = cubic(p, (mx, p[1]), (mx, q[1]), q, 16)
        else:
            my = (p[1] + q[1]) / 2
            seg = cubic(p, (p[0], my), (q[0], my), q, 16)
        smooth += seg if not smooth else seg[1:]
    out += _drawn(P, smooth, s["accent"], 4.5, ts[0], ts[-1], T)
    for i, x in enumerate(st):
        px, py = pts[i]
        c = colf(x["score"])
        g = P.disc(px, py, 15, c, s["ink"] if not P.dark else s["bg"], 2.5)
        g += P.text(px, py + 6, str(x["score"]), 16, "mono", P.on(c), "middle", 800)
        if x.get("feel"):
            if P.land:
                g += P.label_chip(px, py - 26, x["feel"], 15, c, P.on(c))
            else:
                g += P.label_chip(px - 24 - text_w(x["feel"], 15) / 2 - 8, py + 6, x["feel"], 15, c, P.on(c))
        out += _g(g, anim("opacity", show_from(ts[i], T, .2), T))
    legs = [(ts[0], 0)]
    tot = plen(smooth)
    acc = 0
    seglens = [plen(smooth[i * 16:(i + 1) * 16 + 1]) for i in range(len(pts) - 1)]
    for i, L in enumerate(seglens):
        acc += L
        legs.append((ts[i + 1], acc / tot))
    if len(smooth) > 1:
        out += _travel(P, smooth, legs, T, None, s["accent"])
    return out, T


# ---------- 7. 看板 ----------

def kanban(P, sp, top, bot):
    s = P.s
    cols = sp["columns"]
    m = len(cols)
    gap = 14
    cw = (P.CW - gap * (m - 1)) / m
    mv = sp.get("move") or {}
    path = mv.get("path") or list(range(m))
    hh = 54
    if mv.get("note"):
        bot -= 48
    ch = min(78, (bot - top - hh - 40) / max(len(c.get("cards", [])) + 1 for c in cols) - 12)
    ts = [1.0 + i * 1.3 for i in range(len(path))]
    T = ts[-1] + 1 + HOLD
    P.T = T
    out = ""
    cl = pal(P)
    slots = []
    for j, c in enumerate(cols):
        x = P.L + j * (cw + gap)
        out += P.box(x, top, cw, bot - top, "soft", None, sw=1, fill=s["panel2"])
        out += P.text(x + 16, top + 34, c["name"], fit(c["name"], 21, cw - 70, 15), "title", P.on(s["panel2"]), weight=800)
        cnt = len(c.get("cards", [])) + (1 if j == path[-1] else 0)
        out += P.pill(x + cw - 12, top + 16, str(cnt), cl[j % len(cl)], size=14, anchor="end")[0]
        for i, cd in enumerate(c.get("cards", [])):
            y = top + hh + 10 + i * (ch + 12)
            txt = cd if isinstance(cd, str) else cd["title"]
            out += P.card(x + 10, y, cw - 20, ch, txt, None if isinstance(cd, str) else cd.get("sub"), "node", None, size=fit(txt, 17, cw - 56, 14), sub_size=14, align="left")
        slots.append((x + 10, top + hh + 10 + len(c.get("cards", [])) * (ch + 12)))
    title = mv.get("title", "新需求")
    cx0 = lambda j: (slots[j][0], slots[j][1])
    w = cw - 20
    card = P.card(0, 0, w, ch, title, mv.get("sub"), "accent", size=fit(title, 18, w - 36, 14), sub_size=14, align="left")
    for i in range(len(path)):
        j = path[i]
        x, y = cx0(j)
        last = i == len(path) - 1
        tin = ts[i]
        tout = ts[i + 1] - .55 if not last else T
        out += _g(f'<g transform="translate({n(x)} {n(y)})">{card}</g>',
                  anim("opacity", window(tin, tout, T, .1) if not last else show_from(tin, T, .1), T), base_opacity=0 if not last else None)
        if not last:
            nx, ny = cx0(path[i + 1])
            d = f"M{n(x)} {n(y)} C{n(x + 40)} {n(y - 60)} {n(nx - 40)} {n(ny - 60)} {n(nx)} {n(ny)}"
            out += _g(f'<g>{card}</g>', motion(d, [(tout, 0), (ts[i + 1], 1)], T),
                      anim("opacity", [(0, 0), (tout, 0), (tout + .02, 1), (ts[i + 1], 1), (ts[i + 1] + .05, 0)], T), base_opacity=0)
    if mv.get("note"):
        out += _g(P.label_chip(P.CX, bot + 30, mv["note"], 16, s["accent"], P.on(s["accent"])), anim("opacity", show_from(ts[-1] + .2, T, .3), T))
    return out, T


# ---------- 8. 雷达 ----------

def radar(P, sp, top, bot):
    s = P.s
    axes = sp["axes"]
    ser = sp["series"]
    k = len(axes)
    vmax = sp.get("max", 10)
    leg_h = 50 if len(ser) > 1 else 0
    R = min(P.CW / 2 - 110, (bot - top - leg_h) / 2 - 50)
    cx = P.CX if not P.land else P.L + P.CW * .38
    cy = top + (bot - top - leg_h) / 2 + 6
    ang = [-math.pi / 2 + 2 * math.pi * i / k for i in range(k)]
    ts = [.6 + i * 1.4 for i in range(len(ser))]
    T = ts[-1] + 1.6 + HOLD
    P.T = T
    out = ""
    for lv in range(1, 5):
        rr = R * lv / 4
        pts = [(cx + rr * math.cos(a), cy + rr * math.sin(a)) for a in ang]
        out += f'<path d="{poly_d(pts, True)}" fill="{s["panel2"] if lv % 2 == 0 else "none"}" fill-opacity=".5" stroke="{s["rule"]}" stroke-width="1.2"/>'
    for i, a in enumerate(ang):
        out += f'<path d="M{n(cx)} {n(cy)}L{n(cx + R * math.cos(a))} {n(cy + R * math.sin(a))}" stroke="{s["rule"]}" stroke-width="1.2"/>'
        lx, ly = cx + (R + 34) * math.cos(a), cy + (R + 34) * math.sin(a) + 7
        anc = "middle" if abs(math.cos(a)) < .3 else ("start" if math.cos(a) > 0 else "end")
        out += P.text(lx, ly, axes[i], 19, "title", s["ink"], anc, 800)
    cl = pal(P)
    for j, se in enumerate(ser):
        c = se.get("color") or (s["accent"] if j == 0 else cl[(j + 1) % len(cl)] if cl[0] == s["accent"] else cl[j % len(cl)])
        pts = [(cx + R * min(1, v / vmax) * math.cos(a), cy + R * min(1, v / vmax) * math.sin(a)) for v, a in zip(se["values"], ang)]
        d1 = poly_d(pts, True)
        d0 = poly_d([(cx, cy)] * k, True)
        t0 = ts[j]
        out += (f'<path d="{d1}" fill="{c}" fill-opacity=".22" stroke="{c}" stroke-width="3.5" stroke-linejoin="round">'
                + anim("d", [(0, d0), (t0, d0), (t0 + 1, d1), (T - .5, d1), (T - .15, d0)], T) + "</path>")
        for i, (px, py) in enumerate(pts):
            g = P.circle(px, py, 6, c, s["bg"], 2)
            if j == 0 and sp.get("show_values", True):
                g += P.text(px + 10 * math.cos(ang[i]), py + 10 * math.sin(ang[i]) - 8, _num(se["values"][i]), 15, "mono", c, "middle", 800)
            out += _g(g, anim("opacity", show_from(t0 + 1, T, .2), T))
    if len(ser) > 1:
        names = [x["name"] for x in ser]
        cs = [x.get("color") or (s["accent"] if j == 0 else cl[(j + 1) % len(cl)] if cl[0] == s["accent"] else cl[j % len(cl)]) for j, x in enumerate(ser)]
        if P.land:
            out += _legend(P, P.L + P.CW * .74, top + 60, names, cs, P.CW * .26, 19, 1)
        else:
            out += _legend(P, P.L + 40, bot - 12, names, cs, P.CW - 80, 18, len(ser))
    if P.land and sp.get("note"):
        out += _g(P.card(P.L + P.CW * .74, bot - 160, P.CW * .26, 140, sp["note"].get("title", ""), sp["note"].get("sub"), "accent", size=22, sub_size=16, align="left"),
                  anim("opacity", show_from(ts[-1] + 1.2, T, .3), T))
    return out, T


# ---------- 9. 韦恩 ----------

def venn(P, sp, top, bot):
    s = P.s
    sets = sp["sets"]
    k = len(sets)
    cl = pal(P)
    R = min(P.CW * (.29 if k == 2 else .27), (bot - top - 60) * (.42 if k == 2 else .3))
    cx, cy = P.CX, (top + bot) / 2 - (20 if k == 3 else 0)
    if k == 2:
        cs = [(cx - R * .62, cy), (cx + R * .62, cy)]
    else:
        cs = [(cx - R * .6, cy - R * .38), (cx + R * .6, cy - R * .38), (cx, cy + R * .62)]
    ts = [.5 + i * .6 for i in range(k)]
    tc = ts[-1] + 1.0
    T = tc + 1.2 + HOLD
    P.T = T
    out = ""
    for i, st in enumerate(sets):
        x, y = cs[i]
        c = st.get("color") or cl[i % len(cl)]
        dx = (x - cx) * 2.2
        dy = (y - cy) * 2.2
        out += (f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(R)}" fill="{c}" fill-opacity=".26" stroke="{c}" stroke-width="3.5">'
                + anim("cx", [(0, n(x + dx)), (ts[i], n(x + dx)), (ts[i] + .7, n(x)), (T - .5, n(x)), (T - .15, n(x + dx))], T)
                + anim("cy", [(0, n(y + dy)), (ts[i], n(y + dy)), (ts[i] + .7, n(y)), (T - .5, n(y)), (T - .15, n(y + dy))], T)
                + anim("opacity", [(0, 0), (ts[i], 0), (ts[i] + .3, 1), (T - .5, 1), (T - .15, 0)], T) + "</circle>")
        ox, oy = x + (x - cx) * .55, y + (y - cy) * .55
        if k == 2:
            ox = x + (x - cx) * .7
        g = P.text(ox, oy - 4, st["title"], fit(st["title"], 26, R * .9, 16), "title", s["ink"], "middle", 900)
        sl = wrap(st.get("sub"), 16, R * .85, 2)
        g += P.lines(ox, oy + 22, sl, 16, 20, role="body", fill=s["muted"], anchor="middle")
        out += _g(g, anim("opacity", show_from(ts[i] + .6, T, .25), T))
    for key, lab in (sp.get("overlaps") or {}).items():
        idx = [ord(ch) - 97 for ch in key]
        px = sum(cs[i][0] for i in idx) / len(idx)
        py = sum(cs[i][1] for i in idx) / len(idx)
        if len(idx) == 2 and k == 3:
            px, py = px + (px - cx) * .35, py + (py - cy) * .35
        out += _g(P.text(px, py + 6, lab, fit(lab, 17, R * .6, 13), "body", s["ink"], "middle", 700), anim("opacity", show_from(tc - .3, T, .25), T))
    if sp.get("center"):
        c = sp["center"]
        px = sum(x for x, _ in cs) / k
        py = sum(y for _, y in cs) / k + (0 if k == 3 else 0)
        chip = P.label_chip(px, py + 8, c, fit(c, 20, R * .9, 14), s["accent"], P.on(s["accent"]))
        out += _g(chip, anim("opacity", show_from(tc, T, .3), T))
        out += (f'<circle cx="{n(px)}" cy="{n(py)}" r="10" fill="none" stroke="{s["accent"]}" stroke-width="3" opacity="0">'
                + anim("r", [(0, 10), (tc, 10), (tc + .9, R * .7)], T) + anim("opacity", [(0, 0), (tc, .8), (tc + .9, 0)], T) + "</circle>")
    if sp.get("caption"):
        out += _g(P.text(P.CX, bot - 10, sp["caption"], fit(sp["caption"], 26, P.CW, 16), "title", s["accent"], "middle", s["title_weight"]),
                  anim("opacity", show_from(tc + .5, T, .3), T))
    return out, T


# ---------- 10. 金字塔 ----------

def pyramid(P, sp, top, bot):
    s = P.s
    lv = sp["levels"]
    k = len(lv)
    side_notes = any(x.get("note") for x in lv)
    pw = min(P.CW * (.62 if side_notes else .9), (bot - top) * 1.15)
    cx = P.L + pw / 2 if side_notes else P.CX
    gap = 8
    hh = (bot - top - 20 - gap * (k - 1)) / k
    ts = [.6 + (k - 1 - i) * .6 for i in range(k)]
    T = .6 + k * .6 + .8 + HOLD
    P.T = T
    out = ""
    H = hh * k + gap * (k - 1)
    W = lambda y: pw * (y - top) / H
    for i, x in enumerate(lv):
        ya, yb = top + i * (hh + gap), top + i * (hh + gap) + hh
        wa, wb = W(ya) if i else 0, W(yb)
        if i == 0:
            pts = [(cx, ya), (cx + wb / 2, yb), (cx - wb / 2, yb)]
        else:
            pts = [(cx - wa / 2, ya), (cx + wa / 2, ya), (cx + wb / 2, yb), (cx - wb / 2, yb)]
        role = x.get("role", "accent" if i == 0 else "node")
        tone = P.tone(i) if role == "node" and s.get("tones") else None
        f, stc, tc, sc = P.node_colors(role, tone)
        g = ""
        if s.get("shadow"):
            o = s["shadow"]
            g += f'<path d="{poly_d([(a + o, b + o) for a, b in pts], True)}" fill="{s.get("shadow_color", s["ink"])}"/>'
        if P.rough:
            g += f'<path d="{poly_d(pts, True)}" fill="{f}" opacity=".6"/>' + P.stroke_path(pts, stc, s["stroke"], closed=True)
        else:
            g += f'<path d="{poly_d(pts, True)}" fill="{f}" stroke="{stc}" stroke-width="{n(max(s["stroke"], 1.5))}" stroke-linejoin="round"/>'
        tw_ = (wa + wb) / 2 * .8 if i else wb * .45
        ty = (ya + yb) / 2 + (12 if i == 0 else 4)
        g += P.text(cx, ty, x["title"], fit(x["title"], 24, tw_, 14), "title", tc, "middle", 800)
        if x.get("sub") and i and hh > 64:
            g += P.text(cx, ty + 24, x["sub"], fit(x["sub"], 15, tw_, 13), "body", sc, "middle")
        if x.get("note"):
            g += P.stroke_path([(cx + (wa + wb) / 4 + 8, (ya + yb) / 2), (P.L + pw + 16, (ya + yb) / 2)], s["rule"], 1.5, dash="3 4")
            nl = wrap(x["note"], 17, P.R - P.L - pw - 30, 2)
            g += P.lines(P.L + pw + 26, (ya + yb) / 2 + 6 - (len(nl) - 1) * 11, nl, 17, 22, role="body", fill=s["ink"], weight=600)
        out += _g(g, anim("opacity", show_from(ts[i], T, .35), T))
    return out, T


# ---------- 11. ER 实体关系 ----------

def er(P, sp, top, bot):
    s = P.s
    ents = sp["entities"]
    rels = sp.get("relations", [])
    k = len(ents)
    ncol = sp.get("cols") or (3 if P.land and k > 4 else 2 if k > 1 else 1)
    nrow = math.ceil(k / ncol)
    gx = 70 if ncol > 1 else 0
    w = (P.CW - gx * (ncol - 1)) / ncol
    rowh = (bot - top) / nrow
    geo = {}
    rh = 30
    for i, e in enumerate(ents):
        c, r = e.get("pos", (i % ncol, i // ncol))
        h = 50 + rh * len(e["fields"]) + 8
        x = P.L + c * (w + gx)
        y = top + r * rowh + (rowh - h) / 2
        geo[e["id"]] = (x, y, w, h)
    ts = [.5 + i * .45 for i in range(k)]
    tr = [ts[-1] + .6 + j * .8 for j in range(len(rels))]
    T = (tr[-1] if tr else ts[-1]) + 1.2 + HOLD
    P.T = T
    out = ""
    paths = []
    for rl in rels:
        x1, y1, w1, h1 = geo[rl["from"]]
        x2, y2, w2, h2 = geo[rl["to"]]
        if abs((y1 + h1 / 2) - (y2 + h2 / 2)) < max(h1, h2) / 2 and x1 != x2:
            a = (x1 + w1, y1 + h1 / 2) if x2 > x1 else (x1, y1 + h1 / 2)
            b = (x2, y2 + h2 / 2) if x2 > x1 else (x2 + w2, y2 + h2 / 2)
            mx = (a[0] + b[0]) / 2
            pts = [a, (mx, a[1]), (mx, b[1]), b]
        else:
            a = (x1 + w1 / 2, y1 + h1) if y2 > y1 else (x1 + w1 / 2, y1)
            b = (x2 + w2 / 2, y2) if y2 > y1 else (x2 + w2 / 2, y2 + h2)
            my = (a[1] + b[1]) / 2
            pts = [a, (a[0], my), (b[0], my), b]
        paths.append(pts)
        out += P.stroke_path(pts, s["rule"], 2.4)
    for i, e in enumerate(ents):
        x, y, w_, h = geo[e["id"]]
        role = e.get("role", "node")
        g = P.box(x, y, w_, h, "soft" if role == "node" else role, None, fill=s["panel"])
        hc = s["accent"] if e.get("hl") else (s["ink"] if not s.get("tones") else P.tone(i)[1] if s.get("tone_strokes") else s["ink"])
        r = s["radius"]
        g += f'<path d="{P.shape_d(x, y, w_, 46, r)}" fill="{hc}"/>'
        if r and P.s.get("shape") not in ("cut", "pixel"):
            g += f'<rect x="{n(x)}" y="{n(y + 46 - r)}" width="{n(w_)}" height="{n(r)}" fill="{hc}"/>'
        g += P.text(x + 16, y + 31, e["title"], fit(e["title"], 21, w_ - 32, 15), "title", P.on(hc), weight=800)
        for j, fd in enumerate(e["fields"]):
            fy = y + 50 + j * rh + 21
            key = " PK" in fd or " FK" in fd
            name, _, tag = fd.partition(" ")
            g += P.text(x + 16, fy, name, 16, "mono", s["ink"], weight=800 if key else 500)
            if tag:
                g += P.text(x + w_ - 14, fy, tag, 14, "mono", s["accent"] if "PK" in tag else s["muted"], "end", 800)
            if j < len(e["fields"]) - 1:
                g += f'<path d="M{n(x + 10)} {n(fy + 9)}H{n(x + w_ - 10)}" stroke="{s["rule"]}" stroke-width="1"/>'
        out += _g(g, anim("opacity", show_from(ts[i], T, .3), T))
    for j, rl in enumerate(rels):
        pts = paths[j]
        out += _drawn(P, pts, s["accent"], 3, tr[j], tr[j] + .5, T)
        card = rl.get("card", "1:N").split(":")
        for end, lab in ((0, card[0]), (-1, card[-1])):
            p = pts[end]
            q = pts[1] if end == 0 else pts[-2]
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy) or 1
            ox, oy = p[0] + dx / L * 18, p[1] + dy / L * 18
            out += _g(P.label_chip(ox + (dy / L) * 14, oy + 6 - (dx / L) * 14, lab, 15, s["accent"], P.on(s["accent"])), anim("opacity", show_from(tr[j] + .4, T, .2), T))
        if rl.get("label"):
            m = ((pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2)
            out += _g(P.label_chip(m[0], m[1] + 6, rl["label"], 15), anim("opacity", show_from(tr[j] + .4, T, .2), T))
        out += _travel(P, pts, [(tr[j] + .5, 0), (tr[j] + 1.1, 1)], T, None, s["accent"])
    return out, T


# ---------- 12. 矩形树图 ----------

def _squarify(vals, x, y, w, h):
    out = []
    vals = list(vals)
    while vals:
        tot = sum(v for _, v in vals)
        short = min(w, h)
        row, best = [], 1e9
        for i in range(len(vals)):
            cand = vals[:i + 1]
            s = sum(v for _, v in cand)
            side = s / tot * (w * h) / short
            worst = max(max(side * side / (v / tot * w * h), (v / tot * w * h) / (side * side)) for _, v in cand)
            if worst > best:
                break
            best, row = worst, cand
        s = sum(v for _, v in row)
        side = s / tot * (w * h) / short
        off = 0
        for k, v in row:
            ln = (v / s) * short
            if w >= h:
                out.append((k, x, y + off, side, ln))
            else:
                out.append((k, x + off, y, ln, side))
            off += ln
        if w >= h:
            x, w = x + side, w - side
        else:
            y, h = y + side, h - side
        vals = vals[len(row):]
    return out


def treemap(P, sp, top, bot):
    s = P.s
    items = sorted(enumerate(sp["items"]), key=lambda p: -p[1]["value"])
    tot = sum(it["value"] for _, it in items)
    rects = _squarify([(i, it["value"]) for i, it in items], P.L, top + 6, P.CW, bot - top - 6)
    cl = pal(P)
    ts = {}
    for j, (i, _) in enumerate(items):
        ts[i] = .5 + j * .3
    T = .5 + len(items) * .3 + 1 + HOLD
    P.T = T
    out = ""
    unit = sp.get("unit", "")
    for i, x, y, w, h in rects:
        it = sp["items"][i]
        g4 = 4
        rk = [q for q, _ in items].index(i)
        rest = [c for c in cl if c != s["accent"]] or cl
        c = s["accent"] if it.get("hl") else (it.get("color") or rest[rk % len(rest)])
        if not s.get("tones") and not it.get("hl") and not it.get("color"):
            c = mix(rest[rk % len(rest)], s["bg"], .1 + .14 * (rk // len(rest) + rk % 2))
        g = P.box(x + g4 / 2, y + g4 / 2, w - g4, h - g4, "node", None, fill=c, stroke=s["ink"] if (s.get("shadow") or P.rough or s.get("outline_ink")) else c, sw=2)
        tc = P.on(c)
        if w > 70 and h > 46:
            size = max(14, min(30, int(min(w, h * 1.6) / 7)))
            g += P.text(x + 14, y + 14 + size, it["label"], fit(it["label"], size, w - 28, 13), "title", tc, weight=800)
            if h > size + 50:
                pct = it["value"] / tot * 100
                g += P.text(x + 14, y + 14 + size + size * .9 + 6, it.get("text") or f"{_num(it['value'])}{unit} · {pct:.0f}%", max(13, size * .62), "mono", tc, weight=700)
        out += _g(g, anim("opacity", show_from(ts[i], T, .3), T))
    return out, T


# ---------- 13. 华夫格 ----------

def _wcol(P, j):
    """第一份用强调色，其余用由深到浅的灰，让主角一眼跳出来。"""
    s = P.s
    return s["accent"] if j == 0 else mix(s["muted"], s["bg"], (j - 1) * .45)


def waffle(P, sp, top, bot):
    s = P.s
    parts = sp.get("parts") or [{"label": sp.get("label", ""), "value": sp["value"]}]
    cl = pal(P)
    N = 10
    if P.land:
        side = min(bot - top - 20, P.CW * .5)
        x0, y0 = P.L, top + (bot - top - side) / 2
    else:
        side = min(P.CW, bot - top - 150)
        x0, y0 = P.CX - side / 2, top + 4
    cell = side / N
    pad = max(3, cell * .1)
    order = [(r, c) for r in range(N - 1, -1, -1) for c in range(N)]
    owner = []
    for j, p in enumerate(parts):
        owner += [j] * round(p["value"])
    owner = owner[:100]
    dur = 3.2
    t0 = .6
    T = t0 + dur + 1.2 + HOLD
    P.T = T
    out = ""
    r_ = min(s["radius"], cell * .3)
    for idx, (r, c) in enumerate(order):
        x, y = x0 + c * cell + pad / 2, y0 + r * cell + pad / 2
        out += f'<rect x="{n(x)}" y="{n(y)}" width="{n(cell - pad)}" height="{n(cell - pad)}" rx="{n(r_)}" fill="{s["panel2"]}"/>'
        if idx < len(owner):
            j = owner[idx]
            col = parts[j].get("color") or _wcol(P, j)
            tt = t0 + dur * idx / max(1, len(owner))
            out += (f'<rect x="{n(x)}" y="{n(y)}" width="{n(cell - pad)}" height="{n(cell - pad)}" rx="{n(r_)}" fill="{col}">'
                    + anim("opacity", show_from(tt, T, .12), T) + "</rect>")
    big = sp.get("big") or f'{parts[0]["value"]:g}%'
    if P.land:
        bx = x0 + side + 60
        out += _g(P.text(bx, top + (bot - top) * .38, big, 120, "title", s["accent"], weight=900), anim("opacity", show_from(t0 + dur, T, .3), T))
        bl = wrap(sp.get("caption", ""), 26, P.R - bx, 3)
        out += P.lines(bx, top + (bot - top) * .38 + 56, bl, 26, 34, role="title", fill=s["ink"], weight=700)
        ly = top + (bot - top) * .38 + 56 + len(bl) * 34 + 30
        cols_ = [p.get("color") or _wcol(P, j) for j, p in enumerate(parts)]
        out += _legend(P, bx, ly, [p["label"] for p in parts], cols_, P.R - bx, 18, 1, [f'{p["value"]:g}%' for p in parts])
    else:
        by = y0 + side + 82
        out += _g(P.text(P.L, by, big, 76, "title", s["accent"], weight=900), anim("opacity", show_from(t0 + dur, T, .3), T))
        bw = text_w(big, 76) + 24
        bl = wrap(sp.get("caption", ""), 22, P.CW - bw, 2)
        out += P.lines(P.L + bw, by - 30 - (len(bl) - 1) * 14 + 20, bl, 22, 28, role="title", fill=s["ink"], weight=700)
        if len(parts) > 1:
            cols_ = [p.get("color") or _wcol(P, j) for j, p in enumerate(parts)]
            out += _legend(P, P.L, by + 44, [p["label"] for p in parts], cols_, P.CW, 17, min(3, len(parts)))
    return out, T


# ---------- 14. 数字看板 ----------

def _countup(v, steps=8):
    """把 '98.7%' '1,200 万' '+35%' 拆成数字部分，生成递增的中间值。"""
    import re
    m = re.search(r"[\d,]+(\.\d+)?", v)
    if not m:
        return [v]
    num = float(m.group(0).replace(",", ""))
    dec = len(m.group(1)) - 1 if m.group(1) else 0
    comma = "," in m.group(0)
    out = []
    for i in range(1, steps + 1):
        x = num * (1 - (1 - i / steps) ** 2.2)
        sx = f"{x:,.{dec}f}" if comma else f"{x:.{dec}f}"
        out.append(v[:m.start()] + sx + v[m.end():])
    out[-1] = v
    return out


def stat(P, sp, top, bot):
    s = P.s
    items = sp["items"]
    k = len(items)
    ncol = sp.get("cols") or (min(k, 4) if P.land and k <= 4 else 3 if P.land else 2 if k > 1 else 1)
    if k == 3 and not P.land:
        ncol = 1
    nrow = math.ceil(k / ncol)
    gap = 18
    w = (P.CW - gap * (ncol - 1)) / ncol
    h = (bot - top - gap * (nrow - 1)) / nrow
    ts = [.5 + i * .5 for i in range(k)]
    D = 1.4
    T = ts[-1] + D + .6 + HOLD
    P.T = T
    out = ""
    cl = pal(P)
    for i, it in enumerate(items):
        x = P.L + (i % ncol) * (w + gap)
        y = top + (i // ncol) * (h + gap)
        hl = it.get("hl")
        role = "accent" if hl else "node"
        tone = None if hl else (P.tone(i) if s.get("tones") else None)
        out += P.box(x, y, w, h, role, tone)
        f, _, tc, sc = P.node_colors(role, tone)
        big = fit(str(it["value"]), min(96, h * .38), w - 44, 24)
        lab = it["label"]
        out += P.text(x + 22, y + 40, lab, fit(lab, 20, w - 44, 14), "title", tc, weight=800)
        vy = y + 40 + big + 14 if h > 200 else y + h / 2 + big * .36 + 10
        seq = _countup(str(it["value"]))
        for j, txt in enumerate(seq):
            tt = ts[i] + D * j / len(seq)
            last = j == len(seq) - 1
            nxt = ts[i] + D * (j + 1) / len(seq)
            out += _g(P.text(x + 20, vy, txt, big, "title", s["accent"] if not hl and not s.get("tones") else tc, weight=900),
                      anim("opacity", [(0, 0), (tt, 0), (tt + .01, 1), (nxt, 1), (nxt + .01, 0)] if not last else show_from(tt, T, .01), T),
                      base_opacity=0 if not last else None)
        if it.get("delta"):
            d = it["delta"]
            up = not d.startswith("-") and not d.startswith("↓")
            c = s["good"] if up != bool(it.get("lower_better")) else s["bad"]
            out += _g(P.pill(x + w - 18, y + 20, ("▲ " if up else "▼ ") + d.lstrip("+-↑↓"), c, size=15, anchor="end")[0], anim("opacity", show_from(ts[i] + D, T, .2), T))
        if it.get("sub") and h > 160:
            out += P.text(x + 22, y + h - 22, it["sub"], fit(it["sub"], 16, w - 44, 13), "body", sc)
        if it.get("spark") and h > 180:
            sv = it["spark"]
            sx0, sx1 = x + 22, x + w - 22
            sy1 = y + h - (52 if it.get("sub") else 26)
            sy0 = sy1 - min(70, h * .22)
            lo, hi = min(sv), max(sv)
            pts = [(sx0 + (sx1 - sx0) * q / (len(sv) - 1), sy1 - (sy1 - sy0) * (v - lo) / ((hi - lo) or 1)) for q, v in enumerate(sv)]
            c = cl[i % len(cl)] if not hl else tc
            out += _drawn(P, pts, c if not hl else tc, 3.2, ts[i], ts[i] + D, T)
            out += _g(P.circle(pts[-1][0], pts[-1][1], 6, c if not hl else tc), anim("opacity", show_from(ts[i] + D, T, .2), T))
    return out, T


# ---------- 15. 热力格 ----------

def heatmap(P, sp, top, bot):
    s = P.s
    rows, cols, vals = sp["rows"], sp["cols"], sp["values"]
    nr, nc = len(rows), len(cols)
    labw = min(160, max(text_w(r, 17) for r in rows) + 20)
    head = 44
    cw = (P.CW - labw) / nc
    chh = min(cw * 1.1, (bot - top - head - 50) / nr)
    x0, y0 = P.L + labw, top + head
    flat = [v for r in vals for v in r]
    lo, hi = sp.get("min", min(flat)), sp.get("max", max(flat))
    base = s["panel2"]
    hot = s["accent"]
    T = .5 + (nr + nc) * .18 + 1.2 + HOLD
    P.T = T
    out = ""
    for j, c in enumerate(cols):
        out += P.text(x0 + cw * (j + .5), y0 - 14, c, fit(c, 16, cw - 4, 12), "mono", s["muted"], "middle", 800)
    best = max(((i, j) for i in range(nr) for j in range(nc)), key=lambda p: vals[p[0]][p[1]])
    for i, r in enumerate(rows):
        out += P.text(x0 - 14, y0 + chh * (i + .5) + 6, r, fit(r, 17, labw - 18, 13), "title", s["ink"], "end", 700)
        for j in range(nc):
            v = vals[i][j]
            t = (v - lo) / ((hi - lo) or 1)
            c = mix(base, hot, .08 + .92 * t)
            x, y = x0 + cw * j + 2, y0 + chh * i + 2
            tt = .5 + (i + j) * .18
            g = f'<rect x="{n(x)}" y="{n(y)}" width="{n(cw - 4)}" height="{n(chh - 4)}" rx="{min(s["radius"], 6)}" fill="{c}"/>'
            if sp.get("show_values", True) and cw > 40 and chh > 28:
                g += P.text(x + (cw - 4) / 2, y + (chh - 4) / 2 + 6, _num(v), 16 if cw > 60 else 14, "mono", P.on(c), "middle", 700)
            out += _g(g, anim("opacity", show_from(tt, T, .25), T))
    i, j = best
    tb = .5 + (nr + nc) * .18 + .3
    out += _g(P.stroke_path([(x0 + cw * j, y0 + chh * i), (x0 + cw * (j + 1), y0 + chh * i), (x0 + cw * (j + 1), y0 + chh * (i + 1)), (x0 + cw * j, y0 + chh * (i + 1))], s["ink"], 3.5, closed=True),
              anim("opacity", show_from(tb, T, .2), T))
    gy = y0 + chh * nr + 34
    gw = min(320, P.CW * .5)
    for q in range(10):
        out += f'<rect x="{n(P.R - gw + gw * q / 10)}" y="{n(gy - 14)}" width="{n(gw / 10 + .5)}" height="16" fill="{mix(base, hot, .08 + .92 * q / 9)}"/>'
    out += P.text(P.R - gw - 10, gy, _num(lo), 14, "mono", s["muted"], "end", 700)
    out += P.text(P.R - gw - 10 - text_w(_num(lo), 14) - 14, gy, sp.get("legend", ""), 15, "body", s["muted"], "end", 700)
    out += P.text(P.R, gy + 24, _num(hi), 14, "mono", s["muted"], "end", 700)
    if sp.get("note"):
        out += _g(P.text(P.L, gy, sp["note"], fit(sp["note"], 18, P.CW - gw - 120, 13), "title", s["accent"], weight=800), anim("opacity", show_from(tb, T, .3), T))
    return out, T


# ---------- 16. 对比表 ----------

def table(P, sp, top, bot):
    s = P.s
    cols = sp["columns"]
    rows = sp["rows"]
    nc, nr = len(cols), len(rows)
    labw = min(P.CW * .32, 240)
    cw = (P.CW - labw) / nc
    hh = 66
    if sp.get("caption"):
        bot -= 56
    rh = min(88, (bot - top - hh - 10) / nr)
    hl = sp.get("hl")
    ts = [.6 + i * .45 for i in range(nr)]
    T = ts[-1] + 1 + HOLD
    P.T = T
    out = ""
    if hl is not None:
        x = P.L + labw + cw * hl
        out += P.box(x + 4, top, cw - 8, hh + rh * nr + 8, "accent", None, fill=mix(s["accent"], s["bg"], .86), stroke=s["accent"], sw=2.5)
    for j, c in enumerate(cols):
        x = P.L + labw + cw * j
        is_hl = j == hl
        cn = c if isinstance(c, str) else c["name"]
        out += P.text(x + cw / 2, top + 40, cn, fit(cn, 22, cw - 16, 14), "title", s["accent"] if is_hl else s["ink"], "middle", 900 if is_hl else 800)
        if is_hl and sp.get("hl_tag"):
            out += P.pill(x + cw / 2, top - 16, sp["hl_tag"], s["accent"], size=13, anchor="middle")[0]
    out += f'<path d="M{n(P.L)} {n(top + hh)}H{n(P.R)}" stroke="{s["ink"]}" stroke-width="2.5"/>'
    for i, r in enumerate(rows):
        y = top + hh + i * rh
        g = P.text(P.L, y + rh / 2 + 7, r["label"], fit(r["label"], 19, labw - 12, 13), "title", s["ink"], weight=700)
        for j, v in enumerate(r["cells"]):
            cx = P.L + labw + cw * (j + .5)
            v = str(v)
            if v in ("✓", "Y", "yes", "1", "true"):
                g += P.circle(cx, y + rh / 2, 15, s["good"]) + P.text(cx, y + rh / 2 + 7, "✓", 19, "mono", P.on(s["good"]), "middle", 900)
            elif v in ("✕", "✗", "N", "no", "0", "false"):
                g += P.text(cx, y + rh / 2 + 8, "✕", 22, "mono", s["bad"], "middle", 900)
            elif v in ("~", "部分", "半"):
                g += P.circle(cx, y + rh / 2, 14, "none", s["muted"], 3) + P.text(cx, y + rh / 2 + 6, "半" if v != "部分" else "~", 15, "mono", s["muted"], "middle", 800)
            else:
                g += P.text(cx, y + rh / 2 + 7, v, fit(v, 18, cw - 12, 12), "mono", s["accent"] if j == hl else s["ink"], "middle", 800)
        g += f'<path d="M{n(P.L)} {n(y + rh)}H{n(P.R)}" stroke="{s["rule"]}" stroke-width="1.2"/>'
        out += _g(g, anim("opacity", show_from(ts[i], T, .3), T))
        out += _g(f'<rect x="{n(P.L - 8)}" y="{n(y + 2)}" width="{n(P.CW + 16)}" height="{n(rh - 4)}" rx="{min(6, s["radius"])}" fill="{s["accent"]}" opacity=".12"/>',
                  anim("opacity", window(ts[i], ts[i] + .45, T, .1), T), base_opacity=0)
    if sp.get("caption"):
        out += _g(P.text(P.CX, top + hh + rh * nr + 58, sp["caption"], fit(sp["caption"], 28, P.CW, 16), "title", s["accent"], "middle", s["title_weight"]),
                  anim("opacity", show_from(ts[-1] + .5, T, .3), T))
    return out, T


# ---------- 17. 大号步骤 ----------

def steps(P, sp, top, bot):
    s = P.s
    st = sp["steps"]
    k = len(st)
    ts = [.6 + i * .8 for i in range(k)]
    T = ts[-1] + 1 + HOLD
    P.T = T
    out = ""
    if P.land and k <= 5:
        gap = 20
        w = (P.CW - gap * (k - 1)) / k
        for i, x in enumerate(st):
            bx = P.L + i * (w + gap)
            hl = x.get("hl")
            g = P.box(bx, top + 10, w, bot - top - 10, "accent" if hl else "node", None if hl else (P.tone(i) if s.get("tones") else None))
            f, _, tc, sc = P.node_colors("accent" if hl else "node", None if hl else (P.tone(i) if s.get("tones") else None))
            g += P.text(bx + 20, top + 120, f"{i + 1:02d}", 96, "title", s["accent"] if not hl and not s.get("tones") else tc, weight=900)
            tl = wrap(x["title"], 26, w - 40, 3)
            g += P.lines(bx + 20, top + 178, tl, 26, 32, role="title", fill=tc, weight=800)
            sl = wrap(x.get("sub"), 17, w - 40, 6)
            g += P.lines(bx + 20, top + 190 + len(tl) * 32, sl, 17, 24, role="body", fill=sc)
            out += _g(g, anim("opacity", show_from(ts[i], T, .35), T))
            if i < k - 1:
                out += _g(P.text(bx + w + gap / 2, (top + bot) / 2, "→", 26, "mono", s["muted"], "middle", 900), anim("opacity", show_from(ts[i] + .5, T, .2), T))
        return out, T
    rh = (bot - top) / k
    nw = 128
    for i, x in enumerate(st):
        y = top + i * rh
        hl = x.get("hl")
        big = min(104, rh * .82)
        g = P.text(P.L + (nw if k < 10 else nw + 20), y + rh / 2 + big * .36, f"{i + 1:02d}", big, "title",
                   s["accent"] if hl or i == 0 else (s["muted"] if not s.get("tones") else P.tone(i)[1] if s.get("tone_strokes") else s["ink"]), "end", 900)
        tx = P.L + nw + 28
        tl = wrap(x["title"], 26, P.R - tx, 2)
        sl = wrap(x.get("sub"), 17, P.R - tx, 2 if rh > 120 else 1)
        bh = len(tl) * 31 + len(sl) * 23
        ty = y + (rh - bh) / 2 + 24
        g += P.lines(tx, ty, tl, 26, 31, role="title", fill=s["accent"] if hl else s["ink"], weight=800)
        g += P.lines(tx, ty + len(tl) * 31 + 2, sl, 17, 23, role="body", fill=s["muted"])
        if i < k - 1:
            g += f'<path d="M{n(tx)} {n(y + rh)}H{n(P.R)}" stroke="{s["rule"]}" stroke-width="1.5"/>'
        out += _g(g, anim("opacity", show_from(ts[i], T, .35), T))
    out += P.stroke_path([(P.L + nw + 12, top + 10), (P.L + nw + 12, bot - 10)], s["rule"], 3)
    out += _drawn(P, [(P.L + nw + 12, top + 10), (P.L + nw + 12, bot - 10)], s["accent"], 3, ts[0], ts[-1] + .5, T)
    return out, T


# ---------- 18. 生态轨道 ----------

def orbit(P, sp, top, bot):
    s = P.s
    rings = sp["rings"]
    K = len(rings)
    cx, cy = P.CX, (top + bot) / 2
    RY = (bot - top) / 2 - 36
    RX = min(P.CW / 2 - 60, RY * (1.75 if P.land else 1))
    c = sp["center"]
    cr = min(84, RY * .26)
    tr = [1.2 + j * 1.4 for j in range(K)]
    T = tr[-1] + 2.2 + HOLD
    P.T = T
    out = ""
    cl = pal(P)
    for j in range(K):
        rx = cr + (RX - cr) * (j + 1) / K
        ry = cr + (RY - cr) * (j + 1) / K
        out += f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" fill="none" stroke="{s["rule"]}" stroke-width="2" stroke-dasharray="{"6 6" if j else "0"}"/>'
        if rings[j].get("name"):
            out += P.label_chip(cx, cy - ry + 6, rings[j]["name"], 14)
    out += P.disc(cx, cy, cr, s["accent"])
    tl = wrap(c if isinstance(c, str) else c["title"], 22, cr * 1.6, 2)
    out += P.lines(cx, cy + 8 - (len(tl) - 1) * 13, tl, 22, 26, role="title", fill=P.on(s["accent"]), anchor="middle", weight=900)
    out += (f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(cr)}" fill="none" stroke="{s["accent"]}" stroke-width="3">'
            + anim("r", [(0, cr), (.3, cr), (1.1, cr + 40)], T) + anim("opacity", [(0, 0), (.3, .8), (1.1, 0)], T) + "</circle>")
    for j, rg in enumerate(rings):
        rx = cr + (RX - cr) * (j + 1) / K
        ry = cr + (RY - cr) * (j + 1) / K
        items = rg["items"]
        m = len(items)
        col = rg.get("color") or cl[(j + (1 if cl[0] == s["accent"] else 0)) % len(cl)]
        off = j * .5
        for i, lab in enumerate(items):
            a = -math.pi / 2 + off + 2 * math.pi * i / m
            px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
            tt = tr[j] + 1.2 * i / m
            w = text_w(lab, 17) + 26
            g = P.box(px - w / 2, py - 18, w, 36, "node", None, fill=s["panel"], stroke=col, sw=2.5)
            g += P.text(px, py + 6, lab, 17, "title", s["ink"], "middle", 800)
            out += _g(g, anim("opacity", show_from(tt, T, .25), T))
            out += _g(P.circle(px, py, 30, col, extra=' opacity=".25"'), anim("opacity", window(tt, tt + .4, T, .15), T), base_opacity=0)
        d = (f"M{n(cx)} {n(cy - ry)} A{n(rx)} {n(ry)} 0 1 1 {n(cx)} {n(cy + ry)} A{n(rx)} {n(ry)} 0 1 1 {n(cx)} {n(cy - ry)}")
        out += _g(P.token(None, col, 9), motion(d, [(tr[j], 0), (tr[j] + 1.2, 1)], T),
                  anim("opacity", [(0, 0), (tr[j], 0), (tr[j] + .1, 1), (tr[j] + 1.2, 1), (tr[j] + 1.4, 0)], T), base_opacity=0)
    return out, T


CHARTS = dict(donut=donut, quadrant=quadrant, gantt=gantt, sankey=sankey, gitgraph=gitgraph, journey=journey,
              kanban=kanban, radar=radar, venn=venn, pyramid=pyramid, er=er, treemap=treemap, waffle=waffle,
              stat=stat, heatmap=heatmap, table=table, steps=steps, orbit=orbit)
