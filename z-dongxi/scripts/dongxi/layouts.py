"""过程类图型（13 种）。每个函数先排时间、再出图，返回 (svg 片段, 周期秒数)。

动画规则：全部共用周期 T；叙事元素按时间出场，周期末统一淡出再重播；
不开动画时（静态渲染、导出 PNG）看到的是完整终态。
所有坐标都从画笔 P 的画布（P.L / P.R / P.CW / P.CX）推出来，竖版横版都能排。
"""
import math

from .core import (anim, cubic, elbow, fit, motion, n, plen, poly_d, quad,
                   rect_edge_point, show_from, text_w, window, wrap)

HOLD = 2.6


def _g(inner, *anims, base_opacity=None):
    op = f' opacity="{base_opacity}"' if base_opacity is not None else ""
    return f"<g{op}>{''.join(anims)}{inner}</g>"


def _drawn(P, pts, color, sw, t0, t1, T, arrow=False, dash=None):
    """边线：普通风格从起点画到终点，手绘风格淡入。"""
    if P.rough or dash:
        body = P.edge(pts, color, arrow, dash, sw) if arrow else P.stroke_path(pts, color, sw, dash)
        return _g(body, anim("opacity", show_from(t0, T, t1 - t0), T))
    L = plen(pts) + 2
    path = (f'<path d="{poly_d(pts)}" fill="none" stroke="{color}" stroke-width="{n(sw)}" stroke-linecap="round"'
            f' stroke-linejoin="round" stroke-dasharray="{n(L)} {n(L)}">'
            + anim("stroke-dashoffset", [(0, L), (t0, L), (t1, 0), (T - .5, 0), (T - .15, L)], T) + "</path>")
    if P.s.get("glow"):
        path = (f'<path d="{poly_d(pts)}" fill="none" stroke="{color}" stroke-width="{n(sw * 4)}" opacity=".15"'
                f' stroke-dasharray="{n(L)} {n(L)}">'
                + anim("stroke-dashoffset", [(0, L), (t0, L), (t1, 0), (T - .5, 0), (T - .15, L)], T) + "</path>") + path
    if arrow:
        path += _g(P.arrowhead(pts[-2], pts[-1], color), anim("opacity", show_from(t1 - .05, T, .1), T))
    return path


def _travel(P, pts, legs, T, glyph=None, color=None):
    """一个物件沿 pts 走完 legs=[(秒, 进度)]。"""
    d = poly_d(pts)
    t_on, t_off = legs[0][0], legs[-1][0]
    return _g(P.token(glyph, color), motion(d, legs, T),
              anim("opacity", [(0, 0), (t_on, 0), (t_on + .12, 1), (t_off, 1), (t_off + .2, 0)], T), base_opacity=0)


def _lit(P, x, y, w, h, pts, color=None):
    return _g(P.lit(x, y, w, h, color), anim("opacity", pts, P.T), base_opacity=0)


def _shape_node(P, nd, x, y, w, h, role, tone=None):
    shp = nd.get("shape", "box")
    s = P.s
    if shp == "diamond":
        cx, cy = x + w / 2, y + h / 2
        pts = [(cx, y), (x + w, cy), (cx, y + h), (x, cy)]
        f, st, tc, _ = P.node_colors(role, tone)
        out = ""
        if s.get("shadow"):
            o = s["shadow"]
            out += f'<path d="{poly_d([(px + o, py + o) for px, py in pts], True)}" fill="{s.get("shadow_color", s["ink"])}"/>'
        if P.rough:
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" opacity=".45"/>' + P.stroke_path(pts, st, s["stroke"], closed=True)
        else:
            sw = s["stroke"] or 0
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" stroke="{st}" stroke-width="{n(max(sw, 1.5))}"/>'
        size = fit(nd["title"], 20, w * .62, 15)
        tl = wrap(nd["title"], size, w * .64, 2)
        out += P.lines(cx, cy - (len(tl) - 1) * size * .62 + size * .36, tl, size, size * 1.22, role="title", fill=tc, anchor="middle", weight=800)
        return out
    if shp == "db":
        f, st, tc, sc = P.node_colors(role, tone)
        ry = 13
        sw = s["stroke"] or 1.5
        out = ""
        if P.rough:
            out += f'<rect x="{n(x)}" y="{n(y + ry)}" width="{n(w)}" height="{n(h - 2 * ry)}" fill="{f}" opacity=".5"/>'
            out += P.stroke_path([(x, y + ry), (x, y + h - ry)], st, sw) + P.stroke_path([(x + w, y + ry), (x + w, y + h - ry)], st, sw)
            out += P.ellipse(x + w / 2, y + h - ry, w / 2, ry, f, st, sw) + P.ellipse(x + w / 2, y + ry, w / 2, ry, f, st, sw)
        else:
            out += (f'<path d="M{n(x)} {n(y + ry)} V{n(y + h - ry)} A{n(w / 2)} {ry} 0 0 0 {n(x + w)} {n(y + h - ry)} V{n(y + ry)}"'
                    f' fill="{f}" stroke="{st}" stroke-width="{n(sw)}"/>')
            out += P.ellipse(x + w / 2, y + ry, w / 2, ry, f, st, sw)
        tl = wrap(nd["title"], 21, w - 24, 2)
        sl = wrap(nd.get("sub"), 15, w - 24, 1)
        cy = y + h / 2 + 12
        y0 = cy - (len(tl) + len(sl) - 1) * 11 + 4
        out += P.lines(x + w / 2, y0, tl, 21, 25, role="title", fill=tc, anchor="middle", weight=800)
        if sl:
            out += P.text(x + w / 2, y0 + len(tl) * 25, sl[0], 15, "body", sc, "middle")
        return out
    return P.card(x, y, w, h, nd["title"], nd.get("sub"), role, tone)


def _horizontal(P, sp):
    d = (sp.get("direction") or ("LR" if P.land else "TB")).upper()
    return d in ("LR", "RL")


# ---------- 1. 动态流程图 ----------

def flow(P, sp, top, bot):
    nodes = {d["id"]: dict(d) for d in sp["nodes"]}
    order = [d["id"] for d in sp["nodes"]]
    edges = sp.get("edges", [])
    out_adj = {k: [] for k in nodes}
    for e in edges:
        out_adj[e["from"]].append(e["to"])
    color, back = {}, set()

    def dfs(u):
        color[u] = 1
        for v in out_adj[u]:
            if color.get(v) == 1:
                back.add((u, v))
            elif not color.get(v):
                dfs(v)
        color[u] = 2
    for u in order:
        if not color.get(u):
            dfs(u)
    rank = {u: 0 for u in order}
    for _ in range(len(order)):
        for e in edges:
            if (e["from"], e["to"]) not in back:
                rank[e["to"]] = max(rank[e["to"]], rank[e["from"]] + 1)
    for u, d in nodes.items():
        if "rank" in d:
            rank[u] = d["rank"]
    R = max(rank.values()) + 1
    rows = [[u for u in order if rank[u] == r] for r in range(R)]
    plays = sp.get("play")
    if not plays:
        indeg = {u: 0 for u in order}
        for e in edges:
            if (e["from"], e["to"]) not in back:
                indeg[e["to"]] += 1
        cur = next(u for u in order if indeg[u] == 0)
        path, seen = [cur], {cur}
        while True:
            nxt = [v for v in out_adj[cur] if (cur, v) not in back and v not in seen]
            if not nxt:
                break
            cur = nxt[0]
            path.append(cur)
            seen.add(cur)
        plays = [path]
    plays = [p if isinstance(p, dict) else {"path": p} for p in plays]
    if any(p.get("note") for p in plays):
        top += 40
    LR = _horizontal(P, sp)
    geo = {}
    if not LR:
        rh = (bot - top) / R
        for r, row in enumerate(rows):
            k = len(row)
            slot = P.CW / k
            for j, u in enumerate(row):
                d = nodes[u]
                w = min(slot - 26, 340, max(180, text_w(d["title"], P.f["node"]) + 60, text_w(d.get("sub") or "", P.f["sub"]) + 44))
                h = min(P.card_h(d["title"], d.get("sub"), w), rh - 34)
                if d.get("shape") == "diamond":
                    w, h = min(slot - 16, max(w + 70, 220)), min(max(h + 30, 100), rh - 20)
                if d.get("shape") == "db":
                    h = min(max(h + 22, 92), rh - 20)
                cx = P.L + slot * (j + .5) if "x" not in d else P.L + P.CW * d["x"]
                cy = top + rh * (r + .5)
                geo[u] = (cx - w / 2, cy - h / 2, w, h)
    else:
        cwid = P.CW / R
        for r, row in enumerate(rows):
            k = len(row)
            slot = (bot - top) / k
            for j, u in enumerate(row):
                d = nodes[u]
                w = min(cwid - 46, 300)
                h = min(P.card_h(d["title"], d.get("sub"), w), slot - 26)
                if d.get("shape") == "diamond":
                    w, h = min(cwid - 30, w + 40), min(max(h + 40, 110), slot - 16)
                if d.get("shape") == "db":
                    h = min(max(h + 22, 92), slot - 16)
                cx = P.L + cwid * (r + .5)
                cy = top + slot * (j + .5) if "x" not in d else top + (bot - top) * d["x"]
                geo[u] = (cx - w / 2, cy - h / 2, w, h)

    def path_of(u, v):
        x1, y1, w1, h1 = geo[u]
        x2, y2, w2, h2 = geo[v]
        if (u, v) in back:
            if LR:
                yy = max(y1 + h1, y2 + h2) + 28
                if yy > bot:
                    yy = min(y1, y2) - 28
                    return [(x1 + w1 / 2, y1), (x1 + w1 / 2, yy), (x2 + w2 / 2, yy), (x2 + w2 / 2, y2 - 6)]
                return [(x1 + w1 / 2, y1 + h1), (x1 + w1 / 2, yy), (x2 + w2 / 2, yy), (x2 + w2 / 2, y2 + h2 + 6)]
            right = max(x1 + w1, x2 + w2) + 28
            if right > P.W - 18:
                lx = min(x1, x2) - 28
                return [(x1, y1 + h1 / 2), (lx, y1 + h1 / 2), (lx, y2 + h2 / 2), (x2 - 6, y2 + h2 / 2)]
            return [(x1 + w1, y1 + h1 / 2), (right, y1 + h1 / 2), (right, y2 + h2 / 2), (x2 + w2 + 6, y2 + h2 / 2)]
        if rank[u] == rank[v]:
            if LR:
                return [(x1 + w1 / 2, y1 + h1), (x2 + w2 / 2, y2 - 6)] if y2 > y1 else [(x1 + w1 / 2, y1), (x2 + w2 / 2, y2 + h2 + 6)]
            if x2 > x1:
                return [(x1 + w1, y1 + h1 / 2), (x2 - 6, y2 + h2 / 2)]
            return [(x1, y1 + h1 / 2), (x2 + w2 + 6, y2 + h2 / 2)]
        if LR:
            p0, p3 = (x1 + w1, y1 + h1 / 2), (x2 - 6, y2 + h2 / 2)
            dx = p3[0] - p0[0]
            return cubic(p0, (p0[0] + dx * .5, p0[1]), (p3[0] - dx * .5, p3[1]), p3)
        p0 = (x1 + w1 / 2, y1 + h1)
        p3 = (x2 + w2 / 2, y2 - 6)
        dy = p3[1] - p0[1]
        return cubic(p0, (p0[0], p0[1] + dy * .5), (p3[0], p3[1] - dy * .5), p3)
    epaths = {(e["from"], e["to"]): path_of(e["from"], e["to"]) for e in edges}
    t = .6
    sched = []
    for pl in plays:
        arr = []
        for i, u in enumerate(pl["path"]):
            arr.append(t)
            t += .5
            if i < len(pl["path"]) - 1:
                t += .85
        sched.append((pl, arr, t))
        t += .5
    T = t + HOLD
    P.T = T
    out = ""
    for e in edges:
        pts = epaths[(e["from"], e["to"])]
        out += P.edge(pts, P.s["muted"] if (e["from"], e["to"]) in back else None, dash="7 6" if e.get("dashed") else None)
        if e.get("label"):
            m = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
            out += P.label_chip(m[0], m[1] + 6, e["label"])
    for u in order:
        x, y, w, h = geo[u]
        out += _shape_node(P, nodes[u], x, y, w, h, nodes[u].get("role", "node"))
    cols = [P.s["accent"], P.s["accent2"], P.s["good"], P.s["bad"]]
    for pi, (pl, arr, tend) in enumerate(sched):
        path = pl["path"]
        c = pl.get("color") and P.s.get(pl["color"], pl["color"]) or cols[pi % len(cols)]
        last = pi == len(sched) - 1
        for i, u in enumerate(path):
            x, y, w, h = geo[u]
            out += _lit(P, x, y, w, h, show_from(arr[i], T) if last else window(arr[i], tend, T), c)
        full, legs, acc, segs = [], [], 0.0, []
        for i in range(len(path) - 1):
            seg = epaths.get((path[i], path[i + 1]))
            if not seg:
                a, b = geo[path[i]], geo[path[i + 1]]
                seg = [(a[0] + a[2] / 2, a[1] + a[3] / 2), (b[0] + b[2] / 2, b[1] + b[3] / 2)]
            segs.append(seg)
        if segs:
            for sg in segs:
                full += sg if not full else sg[1:]
            total = plen(full)
            for i, sg in enumerate(segs):
                legs.append((arr[i] + .5, acc / total))
                acc += plen(sg)
                legs.append((arr[i + 1], acc / total))
            out += _travel(P, full, legs, T, pl.get("glyph"), c)
        if pl.get("note"):
            out += _g(P.label_chip(P.CX, top - 16, pl["note"], 17, c, P.on(c)),
                      anim("opacity", window(arr[0] - .3, tend, T) if not last else show_from(arr[0] - .3, T), T), base_opacity=0 if not last else None)
    return out, T


# ---------- 2. 动态时序图 ----------

def sequence(P, sp, top, bot):
    s = P.s
    actors = sp["actors"]
    msgs = sp["messages"]
    k = len(actors)
    slot = P.CW / k
    xs = {a["id"]: P.L + slot * (i + .5) for i, a in enumerate(actors)}
    bw = min(190, slot - 16)
    ah = 66
    y_first = top + ah + 74
    gap = min(150, (bot - y_first - 20) / max(1, len(msgs) - .4))
    ts = [.6 + i * 1.15 for i in range(len(msgs))]
    T = ts[-1] + 1.2 + HOLD
    P.T = T
    out = ""
    for a in actors:
        x = xs[a["id"]]
        out += P.stroke_path([(x, top + ah), (x, bot)], s["rule"], 2, dash="4 7")
        out += P.card(x - bw / 2, top, bw, ah, a["title"], None, a.get("role", "dark" if a is actors[0] else "node"), size=20)
    fs = P.f["label"] + 2
    for i, m in enumerate(msgs):
        y = y_first + i * gap
        x1, x2 = xs[m["from"]], xs[m["to"]]
        t0 = ts[i]
        c = s["accent"] if not m.get("reply") else s["muted"]
        g = ""
        if x1 == x2:
            pts = [(x1 + 4, y - 12), (x1 + 56, y - 12), (x1 + 56, y + 14), (x1 + 8, y + 14)]
            g += P.edge(pts, c)
            g += P.text(x1 + 66, y + 7, m["text"], fs, "body", s["ink"], weight=600)
        else:
            sx = 1 if x2 > x1 else -1
            pts = [(x1 + sx * 6, y), (x2 - sx * 8, y)]
            span = abs(x2 - x1) - 20
            tl = wrap(m["text"], fs, max(span, 150), 2)
            mx = (x1 + x2) / 2
            g += P.lines(mx, y - 11 - (len(tl) - 1) * (fs + 4), tl, fs, fs + 4, role="body", fill=s["ink"], anchor="middle", weight=700)
            if m.get("reply"):
                g += P.edge(pts, c, dash="8 6")
            else:
                g += _drawn(P, pts, c, s.get("edge_w", s["stroke"]) + .6, t0, t0 + .55, T, arrow=True)
            if m.get("note") and gap >= 80:
                g += P.text(mx, y + 25, m["note"], P.f["small"], "mono", s["muted"], "middle")
            g += _travel(P, pts, [(t0, 0), (t0 + .55, 1)], T, m.get("glyph"), c)
        out += _g(g, anim("opacity", show_from(t0 - .05, T, .2), T))
        out += _g(f'<rect x="{n(x2 - 6)}" y="{n(y - 18)}" width="12" height="38" fill="{s["accent"]}" rx="2"/>',
                  anim("opacity", window(t0 + .5, (ts[i + 1] if i + 1 < len(ts) else T - .6), T, .15), T), base_opacity=0)
    return out, T


# ---------- 3. 状态机 ----------

def state(P, sp, top, bot):
    s = P.s
    sts = sp["states"]
    m = len(sts)
    cx, cy = P.CX, (top + bot) / 2
    rx, ry = P.CW / 2 - 118, min(340, (bot - top) / 2 - 64)
    geo = {}
    for i, st in enumerate(sts):
        a = -math.pi / 2 + 2 * math.pi * i / m
        w = min(230, max(140, text_w(st["title"], P.f["node"]) + 52))
        h = P.card_h(st["title"], st.get("sub"), w)
        px, py = (cx + rx * math.cos(a), cy + ry * math.sin(a)) if m > 2 else (cx + (i - .5) * P.CW * .55, cy)
        if "pos" in st:
            px, py = P.L + P.CW * st["pos"][0], top + (bot - top) * st["pos"][1]
        geo[st["id"]] = (px, py, w, h)
    trans = sp.get("transitions", [])

    def tpath(u, v, bend=28):
        x1, y1, w1, h1 = geo[u]
        x2, y2, w2, h2 = geo[v]
        if u == v:
            t = y1 - h1 / 2
            return cubic((x1 - 18, t), (x1 - 48, t - 60), (x1 + 48, t - 60), (x1 + 18, t - 4))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        c = (mx - dy / L * bend, my + dx / L * bend)
        p0 = rect_edge_point(x1, y1, w1, h1, c[0], c[1], 4)
        p1 = rect_edge_point(x2, y2, w2, h2, c[0], c[1], 10)
        return quad(p0, c, p1)
    tp = {(t["from"], t["to"]): tpath(t["from"], t["to"]) for t in trans}
    walk = sp.get("walk") or [sts[0]["id"]] + [t["to"] for t in trans[:m]]
    t = .6
    arr = []
    for i in range(len(walk)):
        arr.append(t)
        t += .75 + (.8 if i < len(walk) - 1 else 0)
    T = t + HOLD
    P.T = T
    out = ""
    for tr in trans:
        pts = tp[(tr["from"], tr["to"])]
        out += P.edge(pts, None if not tr.get("dashed") else s["muted"], dash="7 6" if tr.get("dashed") else None, sw=2)
        if tr.get("label"):
            mpt = pts[len(pts) // 2]
            out += P.label_chip(mpt[0], mpt[1] + 6, tr["label"])
    for st in sts:
        px, py, w, h = geo[st["id"]]
        role = st.get("role") or {"start": "dark", "end": "accent"}.get(st.get("kind"), "node")
        out += P.card(px - w / 2, py - h / 2, w, h, st["title"], st.get("sub"), role)
    for i, u in enumerate(walk):
        px, py, w, h = geo[u]
        t_end = arr[i] + .75
        out += _lit(P, px - w / 2, py - h / 2, w, h, window(arr[i], t_end, T, .15) if i < len(walk) - 1 else show_from(arr[i], T, .15))
        if i < len(walk) - 1:
            v = walk[i + 1]
            pts = tp.get((u, v)) or [(px, py), geo[v][:2]]
            out += _g(P.stroke_path(pts, s["accent"], 4.5), anim("opacity", window(t_end, t_end + .8, T, .1), T), base_opacity=0)
            out += _travel(P, pts, [(t_end, 0), (t_end + .8, 1)], T)
    if sp.get("center"):
        out += P.text(cx, cy + 6, sp["center"], 18, "mono", s["muted"], "middle", 700)
    return out, T


# ---------- 4. 数据管线 ----------

def pipeline(P, sp, top, bot):
    s = P.s
    lanes = sp.get("lanes") or [{"name": sp.get("lane"), "stages": sp["stages"]}]
    L = len(lanes)
    LR = _horizontal(P, sp)
    has_name = any(l.get("name") for l in lanes)
    for l in lanes:
        for i, st in enumerate(l["stages"]):
            st.setdefault("row", i)
    rows = max(st["row"] for l in lanes for st in l["stages"]) + 1
    geo, order = {}, []
    if not LR:
        colw = {1: min(500, P.CW * .7), 2: (P.CW - 56) / 2, 3: (P.CW - 70) / 3}[min(L, 3)]
        gapx = (P.CW - colw * L) / max(1, L - 1) if L > 1 else 0
        x0s = [P.L + i * (colw + gapx) for i in range(L)] if L > 1 else [P.CX - colw / 2]
        ytop = top + (38 if has_name else 0)
        rh = (bot - ytop) / rows
        for li, l in enumerate(lanes):
            for st in l["stages"]:
                h = min(rh - 28, max(70, P.card_h(st["title"], st.get("sub"), colw - (80 if st.get("glyph") else 0))))
                cy = ytop + rh * (st["row"] + .5)
                geo[st["id"]] = (x0s[li], cy - h / 2, colw, h)
                order.append(st)
        name_xy = [(x0s[li], top + 18) for li in range(L)]
    else:
        snake = L == 1 and len(lanes[0]["stages"]) > 4
        if snake:
            per = math.ceil(len(lanes[0]["stages"]) / 2)
            cell = {st["id"]: divmod(i, per) for i, st in enumerate(lanes[0]["stages"])}
            nb, ncol = 2, per
        else:
            cell = {st["id"]: (li, st["row"]) for li, l in enumerate(lanes) for st in l["stages"]}
            nb, ncol = L, rows
        band = (bot - top) / nb
        cw = P.CW / ncol
        for l in lanes:
            for st in l["stages"]:
                bi, ci = cell[st["id"]]
                w = cw - 50
                h = min(band - (58 if has_name else 36), max(120, P.card_h(st["title"], st.get("sub"), w, 21, 15) + (34 if st.get("glyph") else 0)))
                cx = P.L + cw * (ci + .5)
                cy = top + band * bi + (band + (30 if has_name else 0)) / 2
                geo[st["id"]] = (cx - w / 2, cy - h / 2, w, h)
                order.append(st)
        name_xy = [(P.L, top + band * li + 20) for li in range(L)]
    links = sp.get("links", [])
    preds = {st["id"]: [] for st in order}
    segs = []
    for l in lanes:
        for a, b in zip(l["stages"], l["stages"][1:]):
            x, y, w, h = geo[a["id"]]
            x2, y2, w2, h2 = geo[b["id"]]
            if LR and abs(y2 - y) > 4:
                my = (y + h + y2) / 2
                pts = [(x + w / 2, y + h), (x + w / 2, my), (x2 + w2 / 2, my), (x2 + w2 / 2, y2 - 7)]
            elif LR:
                pts = [(x + w, y + h / 2), (x2 - 7, y2 + h2 / 2)]
            else:
                pts = [(x + w / 2, y + h), (x2 + w2 / 2, y2 - 7)]
            preds[b["id"]].append(a["id"])
            segs.append((a, b, pts))
    byid = {st["id"]: st for st in order}
    for lk in links:
        a, b = byid[lk["from"]], byid[lk["to"]]
        x, y, w, h = geo[a["id"]]
        x2, y2, w2, h2 = geo[b["id"]]
        if LR:
            p0 = (x + w / 2, y + h) if y2 > y else (x + w / 2, y)
            p3 = (x2 + w2 / 2, y2 - 7) if y2 > y else (x2 + w2 / 2, y2 + h2 + 7)
            dy = (p3[1] - p0[1]) * .6
            pts = cubic(p0, (p0[0], p0[1] + dy), (p3[0], p3[1] - dy), p3)
        elif abs((y + h / 2) - (y2 + h2 / 2)) < 4:
            pts = [(x + w, y + h / 2), (x2 - 7, y2 + h2 / 2)] if x2 > x else [(x, y + h / 2), (x2 + w2 + 7, y2 + h2 / 2)]
        else:
            p0 = (x + w, y + h / 2) if x2 > x else (x, y + h / 2)
            p3 = (x2 - 7, y2 + h2 / 2) if x2 > x else (x2 + w2 + 7, y2 + h2 / 2)
            dx = (p3[0] - p0[0]) * .6
            pts = cubic(p0, (p0[0] + dx, p0[1]), (p3[0] - dx, p3[1]), p3)
        preds[b["id"]].append(a["id"])
        segs.append((a, b, pts, lk))
    reach, lane_end, seg_t = {}, {}, {}
    seq = sp.get("sequential", True)
    for li, l in enumerate(lanes):
        start = (max(lane_end.values()) + .4) if (seq and lane_end) else .6
        for st in l["stages"]:
            ps = [p for p in preds[st["id"]] if p in reach]
            if not ps:
                reach[st["id"]] = start
            else:
                best = 0
                for p in ps:
                    pts = next(sg[2] for sg in segs if sg[0]["id"] == p and sg[1]["id"] == st["id"])
                    dur = .55 + plen(pts) / 420
                    seg_t[(p, st["id"])] = (reach[p] + .45, reach[p] + .45 + dur)
                    best = max(best, reach[p] + .45 + dur)
                reach[st["id"]] = best
        lane_end[li] = max(reach[st["id"]] for st in l["stages"])
    T = max(reach.values()) + .6 + HOLD
    P.T = T
    out = ""
    a2 = s["accent2"] if s["accent2"] != s["ink"] else s["muted"]
    for li, l in enumerate(lanes):
        if l.get("name"):
            out += P.text(name_xy[li][0], name_xy[li][1], l["name"], P.f["label"], "mono", s["accent"] if li == 0 else a2, weight=800, ls=1.5)
    for sg in segs:
        pts = sg[2]
        lk = sg[3] if len(sg) > 3 else None
        out += P.edge(pts, None if not lk else (s["accent2"] if s["accent2"] != s["ink"] else None), dash="7 6" if lk and lk.get("dashed") else None)
        if lk and lk.get("label"):
            mpt = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[1][0]) / 2, pts[0][1])
            out += P.label_chip(mpt[0], mpt[1] - 8, lk["label"])
    for st in order:
        x, y, w, h = geo[st["id"]]
        role = st.get("role", "node")
        tone = P.tone() if role == "node" and s.get("tones") else None
        gw = max(48, text_w(st["glyph"], 15) + 20) if st.get("glyph") else 0
        out += P.box(x, y, w, h, role, tone)
        f, _, tc, sc = P.node_colors(role, tone)
        if LR:
            tl = wrap(st["title"], 21, w - 28, 2)
            sl = wrap(st.get("sub"), 15, w - 28, 2)
            out += P.lines(x + 14, y + 32, tl, 21, 25, role="title", fill=tc, weight=800)
            if sl:
                out += P.lines(x + 14, y + 32 + len(tl) * 25 + 2, sl, 15, 20, role="body", fill=sc)
            if st.get("glyph"):
                out += P.text(x + w - 14, y + h - 14, st["glyph"], 15, "mono", sc, "end", 800)
        else:
            tsz = 22
            tl = wrap(st["title"], tsz, w - 36 - gw, 2)
            sl = wrap(st.get("sub"), 16, w - 36 - gw, 2)
            while sl and len(tl) * 27 + len(sl) * 21 + 4 > h - 14:
                sl = sl[:-1]
            bh = len(tl) * 27 + (len(sl) * 21 + 4 if sl else 0)
            ty = y + (h - bh) / 2 + 21
            out += P.lines(x + 18, ty, tl, tsz, 27, role="title", fill=tc, weight=800)
            if sl:
                out += P.lines(x + 18, ty + len(tl) * 27 + 3, sl, 16, 21, role="body", fill=sc)
            if st.get("glyph"):
                out += (f'<rect x="{n(x + w - gw - 14)}" y="{n(y + h / 2 - 15)}" width="{n(gw)}" height="30" rx="6"'
                        f' fill="none" stroke="{sc}" stroke-width="1.4" stroke-dasharray="4 3"/>')
                out += P.text(x + w - 14 - gw / 2, y + h / 2 + 5.5, st["glyph"], 15, "mono", sc, "middle", 800)
        out += _lit(P, x, y, w, h, show_from(reach[st["id"]], T, .2))
    for sg in segs:
        a, b, pts = sg[0], sg[1], sg[2]
        t0, t1 = seg_t[(a["id"], b["id"])]
        c = s["accent"] if len(sg) < 4 else (s["accent2"] if s["accent2"] != s["ink"] else s["accent"])
        for k in range(3):
            dt = k * .2
            out += _travel(P, pts, [(t0 + dt, 0), (t1 - .4 + dt, 1)], T, a.get("glyph") if k == 0 else None, c)
    return out, T


# ---------- 5. 分层穿透 ----------

def layers(P, sp, top, bot):
    s = P.s
    ls = sp["layers"]
    k = len(ls)
    gap = 14
    bh = (bot - top - gap * (k - 1)) / k
    bw = P.CW - 86
    rail = P.L + bw + 52
    ys = [top + i * (bh + gap) for i in range(k)]
    stop = sp.get("stop")
    round_trip = sp.get("trace", "down") == "roundtrip" and stop is None
    last = stop if stop is not None else k - 1
    tin = [.6 + i * 1.0 for i in range(last + 1)]
    tout = [tin[-1] + .9 + (last - i) * .7 for i in range(last + 1)] if round_trip else []
    T = (tout[0] if tout else tin[-1]) + 1.0 + HOLD
    P.T = T
    out = P.stroke_path([(rail, top - 6), (rail, bot)], s["rule"], 3)
    split = P.L + min(330, bw * .46)
    for i, ly in enumerate(ls):
        y = ys[i]
        role = ly.get("role", "node")
        tone = P.tone() if role == "node" and s.get("tones") else None
        out += P.box(P.L, y, bw, bh, role, tone)
        f, _, tc, sc = P.node_colors(role, tone)
        out += P.text(P.L + 18, y + 34, f"{i + 1:02d}", 15, "mono", s["accent"] if role == "node" and not s.get("tones") else tc, weight=800)
        tw_ = split - P.L - 70
        tl = wrap(ly["title"], 23, tw_, 1)
        out += P.text(P.L + 56, y + 35, tl[0] if tl else "", fit(ly["title"], 23, tw_, 17), "title", tc, weight=800)
        sl = wrap(ly.get("sub"), 16, tw_, 2 if bh > 96 else 1)
        out += P.lines(P.L + 56, y + 61, sl, 16, 21, role="body", fill=sc)
        cx, cy = split, y + 18
        for chip in ly.get("chips", [])[:6]:
            cw = text_w(chip, 15) + 22
            if cx + cw > P.L + bw - 14:
                cx, cy = split, cy + 36
            if cy + 30 > y + bh - 4:
                break
            out += P.box(cx, cy, cw, 30, "soft", sw=1)
            out += P.text(cx + cw / 2, cy + 20.5, chip, 15, "mono", P.on(s["panel2"]), "middle", 600)
            cx += cw + 8
        out += P.stroke_path([(P.L + bw, y + bh / 2), (rail - 10, y + bh / 2)], s["rule"], 1.6, dash="3 4")
    glyph = sp.get("glyph", "请求")
    for i in range(last + 1):
        y = ys[i]
        is_stop = stop is not None and i == stop
        c = s["bad"] if is_stop else s["accent"]
        hold_to = tout[i] if round_trip else T
        out += _lit(P, P.L, y, bw, bh, show_from(tin[i] + .35, T, .2) if not round_trip else window(tin[i] + .35, hold_to, T, .2), c)
        out += _g(P.stroke_path([(P.L + bw + 4, y + bh / 2), (rail - 10, y + bh / 2)], c, 3.4), anim("opacity", show_from(tin[i] + .3, T, .15), T), base_opacity=0)
        if is_stop:
            mk = sp.get("stop_label", "拦截")
            out += _g(P.label_chip(rail - 20, y + bh / 2 + 40, "✕ " + mk, 16, s["bad"], P.on(s["bad"])), anim("opacity", show_from(tin[i] + .4, T, .2), T))
    ypts = [(rail, top - 10)] + [(rail, ys[i] + bh / 2) for i in range(last + 1)]
    total = plen(ypts)
    legs, acc = [(tin[0] - .5, 0)], 0
    for i in range(last + 1):
        acc += plen(ypts[i:i + 2])
        legs.append((tin[i] + .3, acc / total))
        legs.append((tin[i] + .6, acc / total))
    out += _travel(P, ypts, legs, T, glyph, s["accent"])
    if round_trip:
        back = list(reversed(ypts[1:]))
        bt = plen(back)
        legs, acc = [], 0
        for j, i in enumerate(range(last, -1, -1)):
            if j:
                acc += plen(back[j - 1:j + 1])
            legs.append((tout[i], acc / bt))
        back.append((rail, top - 10))
        legs.append((tout[0] + .5, 1))
        out += _travel(P, back, legs, T, sp.get("back_glyph", "响应"), s["accent2"] if s["accent2"] != s["ink"] else s["good"])
    return out, T


# ---------- 6. 闭环飞轮 ----------

def cycle(P, sp, top, bot):
    s = P.s
    steps = sp["steps"]
    m = len(steps)
    cx, cy = P.CX, (top + bot) / 2
    w = 210 if m <= 5 else 180
    RY = min((bot - top) / 2 - 62, 330)
    RX = min(P.CW / 2 - w / 2 - 10, RY * 1.9 if P.land else RY)
    R = RY
    vals = (sp.get("center") or {}).get("values") or []
    rounds = sp.get("rounds") or max(1, len(vals)) or 2
    per = m * .95
    t0 = .6
    T = t0 + rounds * per + HOLD
    P.T = T
    out = P.stroke_path([(cx + RX * math.cos(a / 60 * 2 * math.pi), cy + RY * math.sin(a / 60 * 2 * math.pi)) for a in range(61)], s["rule"], 4)
    for i in range(m):
        a = -math.pi / 2 + 2 * math.pi * (i + .5) / m
        p = (cx + RX * math.cos(a), cy + RY * math.sin(a))
        q = (cx + RX * math.cos(a + .04), cy + RY * math.sin(a + .04))
        out += P.arrowhead(p, q, s["muted"], 14)
    geo = []
    for i, st in enumerate(steps):
        a = -math.pi / 2 + 2 * math.pi * i / m
        h = P.card_h(st["title"], st.get("sub"), w, 22, 16, 18) + 8
        x, y = cx + RX * math.cos(a) - w / 2, cy + RY * math.sin(a) - h / 2
        geo.append((x, y, w, h))
        out += P.card(x, y + 4, w, h - 4, st["title"], st.get("sub"), st.get("role", "node"), size=22, sub_size=16)
        out += P.pill(x + 10, y - 10, f"{i + 1:02d}", s["accent"], size=13)[0]
    c = sp.get("center") or {}
    if c.get("title"):
        out += P.text(cx, cy - 8, c["title"], fit(c["title"], 40, RX * 1.2, 22), "title", s["ink"], "middle", s["title_weight"])
    if c.get("sub"):
        out += P.text(cx, cy + 22, c["sub"], 16, "body", s["muted"], "middle")
    lab = c.get("counter", "第{n}轮")
    for r in range(rounds):
        ts, te = t0 + r * per, t0 + (r + 1) * per
        last = r == rounds - 1
        txt = vals[r] if r < len(vals) else lab.replace("{n}", str(r + 1))
        out += _g(P.text(cx, cy + 64, txt, 24 if vals else 18, "mono", s["accent"], "middle", 800),
                  anim("opacity", window(ts, te - .15, T, .12) if not last else show_from(ts, T, .12), T), base_opacity=0 if not last else None)
        for i in range(m):
            tt = ts + per * i / m
            x, y, w2, h = geo[i]
            out += _lit(P, x, y + 4, w2, h - 4, window(tt, tt + .55, T, .12))
    d = f"M{n(cx)} {n(cy - RY)} A{n(RX)} {n(RY)} 0 1 1 {n(cx)} {n(cy + RY)} A{n(RX)} {n(RY)} 0 1 1 {n(cx)} {n(cy - RY)}"
    legs = []
    for r in range(rounds):
        legs += [(t0 + r * per, 0), (t0 + (r + 1) * per - .001, 1)]
    out += _g(P.token(None, s["accent"], 13), motion(d, legs, T),
              anim("opacity", [(0, 0), (t0, 0), (t0 + .1, 1), (t0 + rounds * per, 1), (t0 + rounds * per + .3, 0)], T), base_opacity=0)
    return out, T


# ---------- 7. 对比赛跑 ----------

def race(P, sp, top, bot):
    """所有条同时起跑，按数值匀速生长；better=lower 时数值小的先停（省钱/省时），higher 时数值大的胜。"""
    s = P.s
    items = sp["items"]
    k = len(items)
    lower = sp.get("better", "lower") == "lower"
    vmax = max(i["value"] for i in items)
    best = (min if lower else max)(range(k), key=lambda i: items[i]["value"])
    D = sp.get("race_dur", 5.0)
    t0 = .6
    badge_h = 120 if sp.get("badge") else 0
    lh = min(160, (bot - top - badge_h - 44) / k)
    y0 = top + 44 + max(0, (bot - top - badge_h - 44 - lh * k) / 2)
    x0, x1 = P.L, P.R - 150
    fin = [t0 + D * it["value"] / vmax for it in items]
    T = max(fin) + .8 + HOLD
    P.T = T
    out = ""
    unit = sp.get("unit", "")
    for i, it in enumerate(items):
        y = y0 + i * lh
        win = it.get("hl", i == best)
        out += P.text(x0, y + 6, it["name"], 24, "title", s["ink"], weight=800)
        if it.get("note"):
            out += P.text(x0 + text_w(it["name"], 24) * 1.15 + 14, y + 6, it["note"], 16, "body", s["muted"])
        by = y + 24
        bh = min(40, lh - 60)
        r = min(s["radius"], 10)
        out += f'<rect x="{x0}" y="{n(by)}" width="{n(x1 - x0)}" height="{n(bh)}" rx="{r}" fill="{s["panel2"]}"/>'
        wf = (x1 - x0) * it["value"] / vmax
        col = s["accent"] if win else s["muted"]
        out += (f'<rect x="{x0}" y="{n(by)}" width="{n(wf)}" height="{n(bh)}" rx="{r}" fill="{col}">'
                + anim("width", [(0, 0), (t0, 0), (fin[i], n(wf)), (T - .5, n(wf)), (T - .15, 0)], T) + "</rect>")
        if P.rough or s.get("shadow"):
            out += P.stroke_path([(x0, by), (x0 + wf, by), (x0 + wf, by + bh), (x0, by + bh)], s["ink"], 2, closed=True)
        val = it.get("label") or f'{it["value"]:,}{unit}'
        out += _g(P.text(x0 + wf + bh / 2 + 16, by + bh / 2 + 8, val, 22, "mono", s["accent"] if win else s["ink"], weight=800),
                  anim("opacity", show_from(fin[i], T, .2), T))
        out += _g(P.circle(x0 + wf, by + bh / 2, bh / 2 + 4, col, s["ink"] if not P.dark else s["bg"], 3),
                  motion(f"M{n(-wf)} 0 L0 0", [(0, 0), (t0, 0), (fin[i], 1), (T - .5, 1), (T - .15, 0)], T))
    if sp.get("badge"):
        out += _g(P.text(P.CX, bot - 34, sp["badge"], fit(sp["badge"], 50, P.CW, 30), "title", s["accent"], "middle", s["title_weight"]),
                  anim("opacity", show_from(max(fin) + .2, T, .3), T))
    if sp.get("clock", True):
        ticks = 10
        lab = sp.get("meter", "{v}")
        for j in range(ticks + 1):
            tt = t0 + D * j / ticks
            txt = lab.replace("{v}", f"{vmax * j / ticks:,.0f}{unit}")
            last = j == ticks
            out += _g(P.text(P.R, top + 10, txt, 18, "mono", s["muted"], "end", 800),
                      anim("opacity", window(tt, tt + D / ticks - .02, T, .01) if not last else show_from(tt, T, .01), T),
                      base_opacity=None if last else 0)
    return out, T


# ---------- 8. 时间线 ----------

def timeline(P, sp, top, bot):
    s = P.s
    ev = sp["events"]
    m = len(ev)
    ts = [.6 + i * 1.0 for i in range(m)]
    T = ts[-1] + .8 + HOLD
    P.T = T
    if _horizontal(P, sp):
        ay = (top + bot) / 2
        step = P.CW / m
        out = P.stroke_path([(P.L, ay), (P.R, ay)], s["rule"], 4)
        out += _drawn(P, [(P.L, ay), (P.R, ay)], s["accent"], 4, ts[0], ts[-1] + .3, T)
        w = min(2 * step - 24, 300)
        for i, e in enumerate(ev):
            cx = P.L + step * (i + .5)
            up = i % 2 == 0
            hl = e.get("hl")
            h = min((bot - top) / 2 - 76, P.card_h(e["title"], e.get("sub"), w, 20, 15, 14))
            y = ay - 64 - h if up else ay + 64
            bx = max(P.L, min(P.R - w, cx - w / 2))
            g = P.card(bx, y, w, h, e["title"], e.get("sub"), "accent" if hl else "node", size=20, sub_size=15)
            g += P.stroke_path([(cx, ay - 12 if up else ay + 12), (cx, ay - 64 if up else ay + 64)], s["rule"], 2)
            tsz = 22 if len(e["time"]) <= 6 else 17
            g += P.text(cx, ay + (38 if up else -24), e["time"], tsz, "mono", s["accent"] if hl else s["ink"], "middle", 800)
            out += _g(g, anim("opacity", show_from(ts[i], T, .35), T))
            out += P.circle(cx, ay, 10, s["bg"], s["ink"], 3)
            out += _g(P.circle(cx, ay, 10, s["accent"]), anim("opacity", show_from(ts[i], T, .1), T), base_opacity=0)
        pts = [(P.L, ay)] + [(P.L + step * (i + .5), ay) for i in range(m)]
    else:
        ax = P.L + 128
        step = (bot - top) / m
        out = P.stroke_path([(ax, top), (ax, bot)], s["rule"], 4)
        out += _drawn(P, [(ax, top), (ax, bot)], s["accent"], 4, ts[0], ts[-1] + .3, T)
        cxl = ax + 30
        for i, e in enumerate(ev):
            cy = top + step * (i + .5)
            hl = e.get("hl")
            w = P.R - cxl
            h = min(step - 16, P.card_h(e["title"], e.get("sub"), w, 21, 15, 14))
            g = P.card(cxl, cy - h / 2, w, h, e["title"], e.get("sub"), "accent" if hl else "node", size=21, sub_size=15, align="left")
            tsz = fit(e["time"], 24, 104, 15)
            g += P.text(ax - 24, cy + 8, e["time"], tsz, "mono", s["accent"] if hl else s["ink"], "end", 800)
            out += _g(g, anim("opacity", show_from(ts[i], T, .35), T))
            out += P.circle(ax, cy, 10, s["bg"], s["ink"], 3)
            out += _g(P.circle(ax, cy, 10, s["accent"]), anim("opacity", show_from(ts[i], T, .1), T), base_opacity=0)
        pts = [(ax, top)] + [(ax, top + step * (i + .5)) for i in range(m)]
    legs = [(ts[0] - .4, 0)]
    for i in range(m):
        f = plen(pts[:i + 2]) / plen(pts)
        legs += [(ts[i], f), (ts[i] + .6, f)]
    out += _travel(P, pts, legs, T, None, s["accent"])
    return out, T


# ---------- 9. 漏斗筛选 ----------

def funnel(P, sp, top, bot):
    s = P.s
    st = sp["stages"]
    k = len(st)
    v0 = st[0]["value"]
    gap = 10
    bh = (bot - top - 40 - gap * (k - 1)) / k
    maxw = min(P.CW * .84, 640)
    minw = maxw * .32
    widths = [minw + (maxw - minw) * (x["value"] / v0) ** .6 for x in st]
    cx = P.L + maxw / 2 + 6 if not P.land else P.L + P.CW * .38
    rx = min(P.R, cx + maxw / 2 + 170)
    out = ""
    N = sp.get("particles", 18)
    cnt = [max(1, round(N * x["value"] / v0)) for x in st]
    t0, sp_band = .5, .55
    ends = []
    for j in range(N):
        last = max(i for i in range(k) if j < cnt[i]) if j < cnt[0] else 0
        ends.append(t0 + j * .2 + (last + 1) * sp_band + .6)
    T = max(ends) + HOLD
    P.T = T
    for i, x in enumerate(st):
        y = top + i * (bh + gap)
        wt, wb = widths[i], widths[i + 1] if i < k - 1 else widths[i] * .82
        pts = [(cx - wt / 2, y), (cx + wt / 2, y), (cx + wb / 2, y + bh), (cx - wb / 2, y + bh)]
        role = x.get("role", "accent" if i == k - 1 else "node")
        tone = P.tone(i) if role == "node" and s.get("tones") else None
        f, stc, tc, sc = P.node_colors(role, tone)
        if s.get("shadow"):
            o = s["shadow"]
            out += f'<path d="{poly_d([(a + o, b + o) for a, b in pts], True)}" fill="{s.get("shadow_color", s["ink"])}"/>'
        if s.get("misreg"):
            out += f'<path d="{poly_d([(a + 5, b + 5) for a, b in pts], True)}" fill="{s["accent"] if role != "accent" else s["accent2"]}" opacity=".5"/>'
        if P.rough:
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" opacity=".55"/>' + P.stroke_path(pts, stc, s["stroke"], closed=True)
        else:
            sw = s["stroke"] or 0
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" stroke="{stc}" stroke-width="{n(sw)}" stroke-linejoin="round"/>'
        out += P.text(cx, y + bh / 2 - 4, x["title"], fit(x["title"], 22, wb * .9, 15), "title", tc, "middle", 800)
        out += P.text(cx, y + bh / 2 + 24, x.get("label") or f'{x["value"]:,}{sp.get("unit", "")}', 19, "mono", tc if (role != "node" or s.get("tones")) else s["accent"], "middle", 800)
        if i > 0:
            rate = x["value"] / st[i - 1]["value"] * 100
            out += P.text(rx, y + 10, f"↓ {rate:.0f}%" if rate >= 1 else f"↓ {rate:.1f}%", 19, "mono", s["accent"], "end", 800)
        if x.get("note"):
            out += P.text(rx, y + 34, x["note"], 15, "body", s["muted"], "end")
    rng = P.rng
    for j in range(N):
        last = max(i for i in range(k) if j < cnt[i])
        ts = t0 + j * .2
        xx = cx + rng.uniform(-.38, .38) * widths[0] * .7
        ybot = top + last * (bh + gap) + bh * .8
        pts = [(xx, top - 22)]
        for i in range(last + 1):
            wlim = (widths[i + 1] if i < k - 1 else widths[i] * .8) * .35
            xx = cx + max(-wlim, min(wlim, (xx - cx) * .8))
            pts.append((xx, top + i * (bh + gap) + bh * .8))
        survived = last == k - 1
        if survived:
            pts.append((cx + rng.uniform(-30, 30), bot - 4))
        else:
            side = -1 if xx < cx else 1
            pts += [(cx + side * (widths[last] / 2 + 40), ybot + 12), (cx + side * (widths[last] / 2 + 70), ybot + 40)]
        dur = (last + 1) * sp_band + .6
        col = s["accent"] if survived else s["muted"]
        out += _g(P.circle(0, 0, 7, col, s["ink"] if P.rough else "none", 1), motion(poly_d(pts), [(ts, 0), (ts + dur, 1)], T),
                  anim("opacity", [(0, 0), (ts, 0), (ts + .1, 1), (ts + dur - .35, 1), (ts + dur + .1, 0)] if not survived
                       else [(0, 0), (ts, 0), (ts + .1, 1), (T - .5, 1), (T - .15, 0)], T), base_opacity=0)
    return out, T


# ---------- 10. 逐层展开（思维导图） ----------

def tree(P, sp, top, bot):
    s = P.s
    root = sp["root"]
    kids = sp.get("children", [])
    k = len(kids)
    rw = min(460, max(260, text_w(root["title"], 26) + 70))
    rh = P.card_h(root["title"], root.get("sub"), rw, 26)
    out = ""
    rx = P.CX - rw / 2
    t = .5
    gap = 16
    cw = (P.CW - gap * (k - 1)) / k
    h1 = max(P.card_h(c["title"], c.get("sub"), cw, 21, 15) for c in kids)
    m2 = max([len(c.get("children", [])) for c in kids] + [1])
    s2 = min(108, (bot - top - rh - 64 - h1 - 24) / m2)
    h2 = min(s2 - 14, 68)
    used = rh + 64 + h1 + 20 + m2 * s2
    ry = top + max(0, (bot - top - used) / 2)
    y1 = ry + rh + 64
    sched = {"root": t}
    t += .5
    for i in range(k):
        sched[("c", i)] = t
        t += .35
    t += .2
    for i, c in enumerate(kids):
        for j in range(len(c.get("children", []))):
            sched[("g", i, j)] = t
            t += .2
    T = t + .4 + HOLD
    P.T = T
    out += _g(P.card(rx, ry, rw, rh, root["title"], root.get("sub"), root.get("role", "dark"), size=26),
              anim("opacity", show_from(sched["root"], T), T))
    for i, c in enumerate(kids):
        x = P.L + i * (cw + gap)
        p, q = (P.CX, ry + rh), (x + cw / 2, y1 - 4)
        tt = sched[("c", i)]
        out += _drawn(P, elbow(p, q), s.get("edge", s["ink"]), s.get("edge_w", s["stroke"]) or 2, tt - .3, tt, T, arrow=False)
        role = c.get("role", "accent" if c.get("hl") else "node")
        tone = P.tone(i) if role == "node" and s.get("tones") else None
        out += _g(P.card(x, y1, cw, h1, c["title"], c.get("sub"), role, tone, size=21, sub_size=15),
                  anim("opacity", show_from(tt, T), T))
        rail_x = x + 16
        for j, g in enumerate(c.get("children", [])):
            gy = y1 + h1 + 20 + j * s2
            tg = sched[("g", i, j)]
            pts = [(rail_x, y1 + h1 if j == 0 else y1 + h1 + 20 + (j - 1) * s2 + h2 / 2), (rail_x, gy + h2 / 2), (rail_x + 14, gy + h2 / 2)]
            out += _drawn(P, pts, s["muted"], 1.8, tg - .2, tg, T)
            gw = cw - 30
            out += _g(P.card(rail_x + 14, gy, gw, h2, g["title"], g.get("sub"), g.get("role", "soft"), size=fit(g["title"], 18, gw - 30, 15), sub_size=14),
                      anim("opacity", show_from(tg, T, .2), T))
    return out, T


# ---------- 11. 柱线增长 ----------

def _nice(v):
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * e >= v:
            return m * e
    return 10 * e


def bars(P, sp, top, bot):
    s = P.s
    ser = sp["series"]
    k = len(ser)
    kind = sp.get("kind", "bar")
    vmax = sp.get("max") or _nice(max(x["value"] for x in ser) * 1.08)
    x0, x1 = P.L + 56, P.R
    yb, yt = bot - 70, top + 52
    ah = yb - yt
    slot = (x1 - x0) / k
    unit = sp.get("unit", "")
    ts = [.5 + i * .38 for i in range(k)]
    T = ts[-1] + 1.2 + HOLD
    P.T = T
    out = ""
    for j in range(5):
        y = yb - ah * j / 4
        out += f'<path d="M{x0} {n(y)}H{x1}" stroke="{s["rule"] if j else s["ink"]}" stroke-width="{2 if j == 0 else 1}"/>'
        v = vmax * j / 4
        out += P.text(x0 - 10, y + 5, f"{v:,.0f}" if vmax >= 10 else f"{v:.1f}", 14, "mono", s["muted"], "end")
    if sp.get("y_label"):
        out += P.text(P.L, yt - 26, sp["y_label"], 15, "mono", s["muted"], weight=700)
    hl = [i for i, x in enumerate(ser) if x.get("hl")] or [max(range(k), key=lambda i: ser[i]["value"])]
    pts = []
    for i, x in enumerate(ser):
        cx = x0 + slot * (i + .5)
        h = ah * x["value"] / vmax
        is_hl = i in hl
        lab = wrap(x["label"], 16, slot - 6, 2)
        out += P.lines(cx, yb + 26, lab, 16, 20, role="body", fill=s["ink"], anchor="middle", weight=600)
        val = x.get("text") or (f'{x["value"]:,}' if isinstance(x["value"], int) else f'{x["value"]}') + unit
        if kind == "bar":
            bw = min(72, slot * .62)
            col = s["accent"] if is_hl else (s["panel2"] if not P.dark else s["muted"])
            stroke = f' stroke="{s["ink"]}" stroke-width="2"' if (not is_hl and not P.dark) or s.get("shadow") else ""
            out += (f'<rect x="{n(cx - bw / 2)}" y="{n(yb - h)}" width="{n(bw)}" height="{n(h)}" fill="{col}"{stroke}>'
                    + anim("height", [(0, 0), (ts[i], 0), (ts[i] + .7, n(h)), (T - .5, n(h)), (T - .15, 0)], T)
                    + anim("y", [(0, n(yb)), (ts[i], n(yb)), (ts[i] + .7, n(yb - h)), (T - .5, n(yb - h)), (T - .15, n(yb))], T) + "</rect>")
            if P.rough:
                out += _g(P.stroke_path([(cx - bw / 2, yb), (cx - bw / 2, yb - h), (cx + bw / 2, yb - h), (cx + bw / 2, yb)], s["ink"], 2),
                          anim("opacity", show_from(ts[i] + .7, T, .2), T))
            vs = fit(val, 19 if is_hl else 16, slot - 4, 14)
            out += _g(P.text(cx, yb - h - 12, val, vs, "mono", s["accent"] if is_hl else s["ink"], "middle", 800),
                      anim("opacity", show_from(ts[i] + .6, T, .2), T))
        pts.append((cx, yb - h))
    if kind == "line":
        out += _drawn(P, pts, s["accent"], 4, ts[0], ts[-1] + .4, T)
        for i, (px, py) in enumerate(pts):
            is_hl = i in hl
            x = ser[i]
            val = x.get("text") or f'{x["value"]}{unit}'
            tt = ts[0] + (ts[-1] + .4 - ts[0]) * i / max(1, k - 1)
            out += _g(P.circle(px, py, 9 if is_hl else 6, s["accent"] if is_hl else s["bg"], s["accent"], 3)
                      + P.text(px, py - 18, val, 18 if is_hl else 15, "mono", s["accent"] if is_hl else s["ink"], "middle", 800),
                      anim("opacity", show_from(tt, T, .15), T))
    if sp.get("note"):
        out += _g(P.label_chip(P.L + P.CW * .42, yt + 30, sp["note"], 17, s["accent"], P.on(s["accent"])), anim("opacity", show_from(ts[-1] + .8, T, .3), T))
    return out, T


# ---------- 12. 网络扩散 ----------

def network(P, sp, top, bot):
    s = P.s
    waves = sp["waves"]
    K = len(waves)
    cx, cy = P.CX, (top + bot) / 2 + 10
    rxm, rym = min(P.CW / 2 - 64, 520), (bot - top) / 2 - 50
    pos = []
    for k, wv in enumerate(waves):
        row = []
        for j, lab in enumerate(wv):
            if k == 0:
                row.append((cx, cy))
                continue
            a = -math.pi / 2 + 2 * math.pi * (j + (.5 if k % 2 == 0 else 0)) / len(wv) + k * .35
            row.append((cx + rxm * k / (K - 1) * math.cos(a), cy + rym * k / (K - 1) * math.sin(a)))
        pos.append(row)
    edges = []
    for k in range(1, K):
        for j, p in enumerate(pos[k]):
            ang = math.atan2(p[1] - cy, p[0] - cx)
            best = min(range(len(pos[k - 1])), key=lambda i: abs(math.atan2(pos[k - 1][i][1] - cy + .001, pos[k - 1][i][0] - cx) - ang) if k > 1 else 0)
            edges.append((k, (k - 1, best), (k, j)))
    tw = [.6 + k * 1.3 for k in range(K)]
    T = tw[-1] + 1.0 + HOLD
    P.T = T
    out = ""
    for k in range(1, K):
        out += f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rxm * k / (K - 1))}" ry="{n(rym * k / (K - 1))}" fill="none" stroke="{s["rule"]}" stroke-width="1.2" stroke-dasharray="3 6"/>'
    for k, a, b in edges:
        p, q = pos[a[0]][a[1]], pos[b[0]][b[1]]
        ra = 40 if a[0] == 0 else 22
        L = math.dist(p, q)
        u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
        pts = [(p[0] + u[0] * ra, p[1] + u[1] * ra), (q[0] - u[0] * 24, q[1] - u[1] * 24)]
        out += P.stroke_path(pts, s["rule"], 1.8)
        out += _drawn(P, pts, s["accent"], 2.6, tw[k] - .7, tw[k] - .1, T)
    for k in range(1, K):
        out += (f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="0" ry="0" fill="none" stroke="{s["accent"]}" stroke-width="3" opacity="0">'
                + anim("rx", [(0, 0), (tw[k] - .8, n(rxm * (k - 1) / (K - 1))), (tw[k], n(rxm * k / (K - 1)))], T)
                + anim("ry", [(0, 0), (tw[k] - .8, n(rym * (k - 1) / (K - 1))), (tw[k], n(rym * k / (K - 1)))], T)
                + anim("opacity", [(0, 0), (tw[k] - .8, 0), (tw[k] - .7, .7), (tw[k], 0)], T) + "</ellipse>")
    for k, wv in enumerate(waves):
        for j, lab in enumerate(wv):
            px, py = pos[k][j]
            r = 40 if k == 0 else 22
            out += P.disc(px, py, r, s["panel"], None, 2)
            out += _g(P.circle(px, py, r, s["accent"]) + (P.circle(px, py, r + 8, s["accent"], extra=' opacity=".2"') if s.get("glow") else ""),
                      anim("opacity", show_from(tw[k], T, .2), T))
            if k == 0:
                tl = wrap(lab, 17, 66, 2)
                out += P.lines(px, py + 6 - (len(tl) - 1) * 10, tl, 17, 20, role="title", fill=s["ink"], anchor="middle", weight=800)
                out += _g(P.lines(px, py + 6 - (len(tl) - 1) * 10, tl, 17, 20, role="title", fill=P.on(s["accent"]), anchor="middle", weight=800),
                          anim("opacity", show_from(tw[0], T, .2), T))
            else:
                tl = wrap(lab, 15, 110, 2)
                out += P.lines(px, py + r + 20, tl, 15, 18, role="body", fill=s["ink"], anchor="middle", weight=600)
    counts = sp.get("counts")
    if counts:
        lab = sp.get("counter", "{v}")
        for k in range(K):
            last = k == K - 1
            out += _g(P.text(P.R, top + 6, lab.replace("{v}", str(counts[k])), 22, "mono", s["accent"], "end", 800),
                      anim("opacity", window(tw[k], tw[k + 1] - .05, T, .1) if not last else show_from(tw[k], T, .1), T), base_opacity=0 if not last else None)
    return out, T


# ---------- 13. 前后对比 ----------

def versus(P, sp, top, bot):
    s = P.s
    L, Rt = sp["left"], sp["right"]
    gapc = 36
    side = 340 if P.land else 0
    colw = (P.CW - gapc - side - (gapc if side else 0)) / 2
    xs = [P.L, P.L + colw + gapc]
    badge_h = 96 if sp.get("badge") and not side else 0
    hh = 84
    steps_top = top + hh + 20
    steps_bot = bot - badge_h - (30 if side else 76)
    m = max(len(L["steps"]), len(Rt["steps"]))
    sg = min(104, (steps_bot - steps_top) / m)
    sh = min(sg - 14, 72)
    slow = sp.get("slow_dur", 5.4)
    ratio = sp.get("speed_ratio", .3)
    t0 = .7
    dl = slow / len(L["steps"])
    dr = max(.35, slow * ratio / len(Rt["steps"]))
    end_l, end_r = t0 + dl * len(L["steps"]), t0 + dr * len(Rt["steps"])
    T = max(end_l, end_r) + 1.0 + HOLD
    P.T = T
    out = ""
    for side_i, (col, x, dt, tend) in enumerate(((L, xs[0], dl, end_l), (Rt, xs[1], dr, end_r))):
        role = "soft" if side_i == 0 else "accent"
        out += P.card(x, top, colw, hh, col["title"], col.get("sub"), role, size=24, sub_size=15)
        for i, stp in enumerate(col["steps"]):
            y = steps_top + i * sg
            out += P.card(x, y, colw, sh, stp, None, "node", P.s["panel"] if s.get("tones") else None, size=19, align="left")
            tt = t0 + dt * (i + 1)
            out += _lit(P, x, y, colw, sh, show_from(tt - dt * .9, T, .15), s["accent"] if side_i else s["muted"])
            out += _g(P.text(x + colw - 18, y + sh / 2 + 8, "✓", 22, "mono", s["good"], "end", 800), anim("opacity", show_from(tt, T, .1), T))
        by = steps_bot + 16
        out += f'<rect x="{n(x)}" y="{n(by)}" width="{n(colw)}" height="12" rx="6" fill="{s["panel2"]}"/>'
        out += (f'<rect x="{n(x)}" y="{n(by)}" width="{n(colw)}" height="12" rx="6" fill="{s["accent"] if side_i else s["muted"]}">'
                + anim("width", [(0, 0), (t0, 0), (tend, n(colw)), (T - .5, n(colw)), (T - .15, 0)], T) + "</rect>")
        if col.get("total") and not side:
            out += _g(P.text(x + colw / 2, by + 50, col["total"], 30, "mono", s["accent"] if side_i else s["ink"], "middle", 800),
                      anim("opacity", show_from(tend, T, .25), T))
        elif col.get("total"):
            sx = P.R - side / 2
            sy = top + 70 + side_i * 130
            out += P.text(sx, sy - 30, col["title"], 18, "body", s["muted"], "middle", 700)
            out += _g(P.text(sx, sy + 26, col["total"], 52, "mono", s["accent"] if side_i else s["ink"], "middle", 800),
                      anim("opacity", show_from(tend, T, .25), T))
    if side:
        sx = P.R - side / 2
        out += P.stroke_path([(P.R - side + 10, top + 4), (P.R - side + 10, bot - 10)], s["rule"], 2)
        if sp.get("badge"):
            bl = wrap(sp["badge"], 38, side - 30, 3)
            out += _g(P.lines(sx, bot - 40 - (len(bl) - 1) * 46, bl, 38, 46, role="title", fill=s["accent"], anchor="middle", weight=s["title_weight"]),
                      anim("opacity", show_from(max(end_l, end_r) + .3, T, .35), T))
    elif sp.get("badge"):
        out += _g(P.text(P.CX, bot - 22, sp["badge"], fit(sp["badge"], 46, P.CW, 28), "title", s["accent"], "middle", s["title_weight"]),
                  anim("opacity", show_from(max(end_l, end_r) + .3, T, .35), T))
    return out, T


LAYOUTS = dict(flow=flow, sequence=sequence, state=state, pipeline=pipeline, layers=layers, cycle=cycle,
               race=race, timeline=timeline, funnel=funnel, tree=tree, bars=bars, network=network, versus=versus)
