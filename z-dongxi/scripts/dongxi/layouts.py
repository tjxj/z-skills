"""十三种动态图型。每个函数先排时间、再出图，返回 (svg 片段, 周期秒数)。

动画规则：全部共用周期 T；叙事元素按时间出场，周期末统一淡出再重播；
不开动画时（静态渲染、导出 PNG）看到的是完整终态。
"""
import math

from .core import (W, Painter, anim, ambient, cubic, elbow, esc, motion, n, plen, poly_d, quad,
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
        f, st, tc = P.role_colors(role)
        if role == "node" and s.get("tones"):
            f = tone or P.tone()
        out = ""
        if s.get("shadow"):
            o = s["shadow"]
            out += f'<path d="{poly_d([(px + o, py + o) for px, py in pts], True)}" fill="{s["ink"]}"/>'
        if P.rough:
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" opacity=".45"/>' + P.stroke_path(pts, st, s["stroke"], closed=True)
        else:
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" stroke="{st}" stroke-width="{s["stroke"]}"/>'
        if role == "node" and s.get("tones"):
            tc = s["ink"]
        tl = wrap(nd["title"], 17, w * .62, 2)
        out += P.lines(cx, cy - (len(tl) - 1) * 11 + 6, tl, 17, 22, role="title", fill=tc, anchor="middle", weight=700)
        return out
    if shp == "db":
        f, st, tc = P.role_colors(role)
        if role == "node" and s.get("tones"):
            f = tone or P.tone()
            tc = s["ink"]
        ry = 12
        out = ""
        if P.rough:
            out += f'<rect x="{n(x)}" y="{n(y + ry)}" width="{n(w)}" height="{n(h - 2 * ry)}" fill="{f}" opacity=".5"/>'
            out += P.stroke_path([(x, y + ry), (x, y + h - ry)], st, s["stroke"]) + P.stroke_path([(x + w, y + ry), (x + w, y + h - ry)], st, s["stroke"])
            out += P.ellipse(x + w / 2, y + h - ry, w / 2, ry, f, st, s["stroke"]) + P.ellipse(x + w / 2, y + ry, w / 2, ry, f, st, s["stroke"])
        else:
            out += (f'<path d="M{n(x)} {n(y + ry)} V{n(y + h - ry)} A{n(w / 2)} {ry} 0 0 0 {n(x + w)} {n(y + h - ry)} V{n(y + ry)}"'
                    f' fill="{f}" stroke="{st}" stroke-width="{s["stroke"]}"/>')
            out += P.ellipse(x + w / 2, y + ry, w / 2, ry, f, st, s["stroke"])
        tl = wrap(nd["title"], 18, w - 24, 2)
        sl = wrap(nd.get("sub"), 14, w - 24, 1)
        cy = y + h / 2 + 10
        out += P.lines(x + w / 2, cy - (len(tl) + len(sl) - 1) * 10 + 4, tl, 18, 22, role="title", fill=tc, anchor="middle", weight=700)
        if sl:
            out += P.text(x + w / 2, cy - (len(tl) + len(sl) - 1) * 10 + 4 + len(tl) * 22, sl[0], 14, "body", s["muted"] if role == "node" else tc, "middle")
        return out
    return P.card(x, y, w, h, nd["title"], nd.get("sub"), role, tone)


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
        top += 36
    # 几何
    rh = (bot - top) / R
    geo = {}
    for r, row in enumerate(rows):
        k = len(row)
        slot = 670 / k
        for j, u in enumerate(row):
            d = nodes[u]
            w = min(slot - 24, 300, max(150, text_w(d["title"], 19) + 56, text_w(d.get("sub") or "", 15) + 40))
            h = P.card_h(d["title"], d.get("sub"), w)
            if d.get("shape") == "diamond":
                w, h = min(slot - 16, max(w + 60, 200)), max(h + 26, 96)
            if d.get("shape") == "db":
                h = max(h + 18, 84)
            cx = 40 + slot * (j + .5) if "x" not in d else 40 + 670 * d["x"]
            cy = top + rh * (r + .5)
            geo[u] = (cx - w / 2, cy - h / 2, w, h)

    def path_of(u, v):
        x1, y1, w1, h1 = geo[u]
        x2, y2, w2, h2 = geo[v]
        if (u, v) in back:
            right = max(x1 + w1, x2 + w2) + 26
            if right > 728:
                lx = min(x1, x2) - 26
                return [(x1, y1 + h1 / 2), (lx, y1 + h1 / 2), (lx, y2 + h2 / 2), (x2 - 6, y2 + h2 / 2)]
            return [(x1 + w1, y1 + h1 / 2), (right, y1 + h1 / 2), (right, y2 + h2 / 2), (x2 + w2 + 6, y2 + h2 / 2)]
        if rank[u] == rank[v]:
            if x2 > x1:
                return [(x1 + w1, y1 + h1 / 2), (x2 - 6, y2 + h2 / 2)]
            return [(x1, y1 + h1 / 2), (x2 + w2 + 6, y2 + h2 / 2)]
        p0 = (x1 + w1 / 2, y1 + h1)
        p3 = (x2 + w2 / 2, y2 - 6)
        dy = p3[1] - p0[1]
        return cubic(p0, (p0[0], p0[1] + dy * .5), (p3[0], p3[1] - dy * .5), p3)
    epaths = {(e["from"], e["to"]): path_of(e["from"], e["to"]) for e in edges}
    # 时间
    t = .6
    sched = []
    for pi, pl in enumerate(plays):
        path = pl["path"]
        arr = []
        for i, u in enumerate(path):
            arr.append(t)
            t += .5
            if i < len(path) - 1:
                t += .85
        sched.append((pl, arr, t))
        t += .5
    T = t + HOLD
    P.T = T
    # 出图
    out = ""
    for e in edges:
        pts = epaths[(e["from"], e["to"])]
        out += P.edge(pts, P.s["muted"] if (e["from"], e["to"]) in back else P.s["ink"], dash="6 6" if e.get("dashed") else None)
        if e.get("label"):
            m = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
            out += P.label_chip(m[0], m[1] + 5, e["label"])
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
            pts_op = show_from(arr[i], T) if last else window(arr[i], tend, T)
            out += _lit(P, x, y, w, h, pts_op, c)
        full, legs, acc = [], [], 0.0
        segs = []
        for i in range(len(path) - 1):
            seg = epaths.get((path[i], path[i + 1]))
            if not seg:
                a, b = geo[path[i]], geo[path[i + 1]]
                seg = [(a[0] + a[2] / 2, a[1] + a[3] / 2), (b[0] + b[2] / 2, b[1] + b[3] / 2)]
            segs.append(seg)
        if segs:
            for s in segs:
                full += s if not full else s[1:]
            total = plen(full)
            for i, s in enumerate(segs):
                legs.append((arr[i] + .5, acc / total))
                acc += plen(s)
                legs.append((arr[i + 1], acc / total))
            out += _travel(P, full, legs, T, pl.get("glyph"), c)
        if pl.get("note"):
            out += _g(P.label_chip(375, top - 14, pl["note"], 15, P.s["bg"], c),
                      anim("opacity", window(arr[0] - .3, tend, T) if not last else show_from(arr[0] - .3, T), T), base_opacity=0 if not last else None)
    return out, T


# ---------- 2. 动态时序图 ----------

def sequence(P, sp, top, bot):
    s = P.s
    actors = sp["actors"]
    msgs = sp["messages"]
    k = len(actors)
    slot = 670 / k
    xs = {a["id"]: 40 + slot * (i + .5) for i, a in enumerate(actors)}
    bw = min(150, slot - 14)
    ah = 58
    gap = min(104 if any(m.get("note") for m in msgs) else 92, (bot - top - ah - 40) / max(1, len(msgs)))
    ts = [.6 + i * 1.15 for i in range(len(msgs))]
    T = ts[-1] + 1.2 + HOLD
    P.T = T
    out = ""
    for a in actors:
        x = xs[a["id"]]
        out += P.stroke_path([(x, top + ah), (x, bot)], s["rule"], 2, dash="4 6")
        out += P.card(x - bw / 2, top, bw, ah, a["title"], None, a.get("role", "dark" if a is actors[0] else "node"), size=17)
    for i, m in enumerate(msgs):
        y = top + ah + 38 + i * gap
        x1, x2 = xs[m["from"]], xs[m["to"]]
        t0 = ts[i]
        c = s["accent"] if not m.get("reply") else s["muted"]
        g = ""
        if x1 == x2:
            pts = [(x1 + 4, y - 10), (x1 + 52, y - 10), (x1 + 52, y + 14), (x1 + 8, y + 14)]
            g += P.edge(pts, c)
            g += P.text(x1 + 60, y + 6, m["text"], 15, "body", s["ink"])
        else:
            sx = 1 if x2 > x1 else -1
            pts = [(x1 + sx * 6, y), (x2 - sx * 8, y)]
            span = abs(x2 - x1) - 20
            tl = wrap(m["text"], 15, max(span, 140), 2)
            mx = (x1 + x2) / 2
            g += P.lines(mx, y - 10 - (len(tl) - 1) * 19, tl, 15, 19, role="body", fill=s["ink"], anchor="middle", weight=600)
            if m.get("reply"):
                g += P.edge(pts, c, dash="7 6")
            else:
                g += _drawn(P, pts, c, s["stroke"] + .4, t0, t0 + .55, T, arrow=True)
            if m.get("note"):
                g += P.text(mx, y + 22, m["note"], 13, "mono", s["muted"], "middle")
            g += _travel(P, pts, [(t0, 0), (t0 + .55, 1)], T, m.get("glyph"), c)
        out += _g(g, anim("opacity", show_from(t0 - .05, T, .2), T))
        out += _g(f'<rect x="{n(x2 - 5)}" y="{n(y - 16)}" width="10" height="34" fill="{s["accent"]}" rx="2"/>',
                  anim("opacity", window(t0 + .5, (ts[i + 1] if i + 1 < len(ts) else T - .6), T, .15), T), base_opacity=0)
    return out, T


# ---------- 3. 状态机 ----------

def state(P, sp, top, bot):
    s = P.s
    sts = sp["states"]
    m = len(sts)
    cx, cy = 375, (top + bot) / 2
    rx, ry = 245, min(330, (bot - top) / 2 - 70)
    geo = {}
    for i, st in enumerate(sts):
        a = -math.pi / 2 + 2 * math.pi * i / m
        w = min(210, max(132, text_w(st["title"], 19) + 48))
        h = P.card_h(st["title"], st.get("sub"), w)
        px, py = (cx + rx * math.cos(a), cy + ry * math.sin(a)) if m > 2 else (cx + (i - .5) * 360, cy)
        if "pos" in st:
            px, py = 40 + 670 * st["pos"][0], top + (bot - top) * st["pos"][1]
        geo[st["id"]] = (px, py, w, h)
    trans = sp.get("transitions", [])

    def tpath(u, v, bend=26):
        x1, y1, w1, h1 = geo[u]
        x2, y2, w2, h2 = geo[v]
        if u == v:
            t = y1 - h1 / 2
            return cubic((x1 - 18, t), (x1 - 46, t - 58), (x1 + 46, t - 58), (x1 + 18, t - 4))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        c = (mx - dy / L * bend, my + dx / L * bend)
        p0 = rect_edge_point(x1, y1, w1, h1, c[0], c[1], 4)
        p1 = rect_edge_point(x2, y2, w2, h2, c[0], c[1], 9)
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
        out += P.edge(pts, s["ink"] if not tr.get("dashed") else s["muted"], dash="6 6" if tr.get("dashed") else None, sw=1.8)
        if tr.get("label"):
            mpt = pts[len(pts) // 2]
            out += P.label_chip(mpt[0], mpt[1] + 5, tr["label"], 13)
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
            out += _g(P.stroke_path(pts, s["accent"], s["stroke"] + 2), anim("opacity", window(t_end, t_end + .8, T, .1), T), base_opacity=0)
            out += _travel(P, pts, [(t_end, 0), (t_end + .8, 1)], T)
    if sp.get("center"):
        out += P.text(cx, cy, sp["center"], 16, "mono", s["muted"], "middle", 700)
    return out, T


# ---------- 4. 数据管线 ----------

def pipeline(P, sp, top, bot):
    s = P.s
    lanes = sp.get("lanes") or [{"name": sp.get("lane"), "stages": sp["stages"]}]
    L = len(lanes)
    colw = {1: 440, 2: 315, 3: 208}[min(L, 3)]
    gapx = (670 - colw * L) / max(1, L - 1) if L > 1 else 0
    x0s = [40 + i * (colw + gapx) for i in range(L)] if L > 1 else [155]
    has_name = any(l.get("name") for l in lanes)
    ytop = top + (34 if has_name else 0)
    for l in lanes:
        for i, st in enumerate(l["stages"]):
            st.setdefault("row", i)
    rows = max(st["row"] for l in lanes for st in l["stages"]) + 1
    rh = (bot - ytop) / rows
    geo, lane_of, order = {}, {}, []
    for li, l in enumerate(lanes):
        for st in l["stages"]:
            h = min(rh - 26, max(64, P.card_h(st["title"], st.get("sub"), colw - (70 if st.get("glyph") else 0))))
            cy = ytop + rh * (st["row"] + .5)
            geo[st["id"]] = (x0s[li], cy - h / 2, colw, h)
            lane_of[st["id"]] = li
            order.append(st)
    links = sp.get("links", [])
    preds = {st["id"]: [] for st in order}
    segs = []
    for l in lanes:
        for a, b in zip(l["stages"], l["stages"][1:]):
            x, y, w, h = geo[a["id"]]
            x2, y2, w2, h2 = geo[b["id"]]
            pts = [(x + w / 2, y + h), (x2 + w2 / 2, y2 - 6)]
            preds[b["id"]].append(a["id"])
            segs.append((a, b, pts))
    byid = {st["id"]: st for st in order}
    for lk in links:
        a, b = byid[lk["from"]], byid[lk["to"]]
        x, y, w, h = geo[a["id"]]
        x2, y2, w2, h2 = geo[b["id"]]
        if abs((y + h / 2) - (y2 + h2 / 2)) < 4:
            pts = [(x + w, y + h / 2), (x2 - 6, y2 + h2 / 2)] if x2 > x else [(x, y + h / 2), (x2 + w2 + 6, y2 + h2 / 2)]
        else:
            p0 = (x + w, y + h / 2) if x2 > x else (x, y + h / 2)
            p3 = (x2 - 6, y2 + h2 / 2) if x2 > x else (x2 + w2 + 6, y2 + h2 / 2)
            dx = (p3[0] - p0[0]) * .6
            pts = cubic(p0, (p0[0] + dx, p0[1]), (p3[0] - dx, p3[1]), p3)
        preds[b["id"]].append(a["id"])
        segs.append((a, b, pts, lk))
    # 时间
    reach, lane_end = {}, {}
    seq = sp.get("sequential", True)
    seg_t = {}
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
    for li, l in enumerate(lanes):
        if l.get("name"):
            out += P.text(x0s[li], top + 16, l["name"], 14, "mono", s["accent"] if li == 0 else s["accent2"] if s["accent2"] != s["ink"] else s["muted"], weight=700, ls=1.5)
    for sg in segs:
        pts = sg[2]
        lk = sg[3] if len(sg) > 3 else None
        out += P.edge(pts, s["ink"] if not lk else s["accent2"] if s["accent2"] != s["ink"] else s["ink"], dash="6 5" if lk and lk.get("dashed") else None)
        if lk and lk.get("label"):
            mpt = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[1][0]) / 2, pts[0][1])
            out += P.label_chip(mpt[0], mpt[1] - 8, lk["label"], 13)
    for st in order:
        x, y, w, h = geo[st["id"]]
        role = st.get("role", "node")
        gw = 0
        if st.get("glyph"):
            gw = max(44, text_w(st["glyph"], 13) + 18)
        out += P.box(x, y, w, h, role)
        _, _, tc = P.role_colors(role)
        if role == "node" and s.get("tones"):
            tc = s["ink"]
        tl = wrap(st["title"], 19, w - 32 - gw, 2)
        sl = wrap(st.get("sub"), 14, w - 32 - gw, 2)
        bh = len(tl) * 23 + (len(sl) * 18 + 4 if sl else 0)
        ty = y + (h - bh) / 2 + 18
        out += P.lines(x + 16, ty, tl, 19, 23, role="title", fill=tc, weight=800)
        if sl:
            out += P.lines(x + 16, ty + len(tl) * 23 + 2, sl, 14, 18, role="body", fill=s["muted"] if role == "node" else tc)
        if st.get("glyph"):
            out += (f'<rect x="{n(x + w - gw - 12)}" y="{n(y + h / 2 - 13)}" width="{n(gw)}" height="26" rx="5"'
                    f' fill="none" stroke="{s["muted"] if role == "node" else tc}" stroke-width="1.2" stroke-dasharray="3 3"/>')
            out += P.text(x + w - 12 - gw / 2, y + h / 2 + 5, st["glyph"], 13, "mono", s["muted"] if role == "node" else tc, "middle", 700)
        out += _lit(P, x, y, w, h, show_from(reach[st["id"]], T, .2))
    for sg in segs:
        a, b, pts = sg[0], sg[1], sg[2]
        t0, t1 = seg_t[(a["id"], b["id"])]
        c = s["accent"] if len(sg) < 4 else (s["accent2"] if s["accent2"] != s["ink"] else s["accent"])
        for k in range(3):
            dt = k * .2
            out += _travel(P, pts, [(t0 + dt, 0), (t1 - .4 + dt, 1)], T, a.get("glyph"), c)
    return out, T


# ---------- 5. 分层穿透 ----------

def layers(P, sp, top, bot):
    s = P.s
    ls = sp["layers"]
    k = len(ls)
    gap = 14
    bh = (bot - top - gap * (k - 1)) / k
    rail = 676
    bw = 590
    ys = [top + i * (bh + gap) for i in range(k)]
    stop = sp.get("stop")
    round_trip = sp.get("trace", "down") == "roundtrip" and stop is None
    last = stop if stop is not None else k - 1
    tin = [.6 + i * 1.0 for i in range(last + 1)]
    tout = [tin[-1] + .9 + (last - i) * .7 for i in range(last + 1)] if round_trip else []
    T = (tout[0] if tout else tin[-1]) + 1.0 + HOLD
    P.T = T
    out = P.stroke_path([(rail, top - 6), (rail, bot)], s["rule"], 3)
    for i, ly in enumerate(ls):
        y = ys[i]
        role = ly.get("role", "node")
        out += P.box(40, y, bw, bh, role)
        _, _, tc = P.role_colors(role)
        if role == "node" and s.get("tones"):
            tc = s["ink"]
        num = f"{i + 1:02d}"
        out += P.text(58, y + 30, num, 13, "mono", s["accent"] if role == "node" else tc, weight=700)
        tl = wrap(ly["title"], 20, 250, 1)
        out += P.text(92, y + 31, tl[0] if tl else "", 20, "title", tc, weight=800)
        sl = wrap(ly.get("sub"), 14, 250, 2 if bh > 90 else 1)
        out += P.lines(92, y + 54, sl, 14, 18, role="body", fill=s["muted"] if role == "node" else tc)
        cx = 360
        cy = y + 18
        for chip in ly.get("chips", [])[:6]:
            cw = text_w(chip, 13) + 18
            if cx + cw > 40 + bw - 14:
                cx = 360
                cy += 32
            if cy + 26 > y + bh - 4:
                break
            out += P.box(cx, cy, cw, 26, "soft", sw=1)
            out += P.text(cx + cw / 2, cy + 18, chip, 13, "mono", s["ink"], "middle")
            cx += cw + 8
        out += P.stroke_path([(40 + bw, y + bh / 2), (rail - 10, y + bh / 2)], s["rule"], 1.5, dash="3 4")
    glyph = sp.get("glyph", "请求")
    for i in range(last + 1):
        y = ys[i]
        is_stop = stop is not None and i == stop
        c = s["bad"] if is_stop else s["accent"]
        hold_to = tout[i] if round_trip else (T if True else tin[i] + 1)
        out += _lit(P, 40, y, bw, bh, show_from(tin[i] + .35, T, .2) if not round_trip else window(tin[i] + .35, hold_to, T, .2), c)
        out += _g(P.stroke_path([(40 + bw + 4, y + bh / 2), (rail - 10, y + bh / 2)], c, 3), anim("opacity", show_from(tin[i] + .3, T, .15), T), base_opacity=0)
        if is_stop:
            mk = sp.get("stop_label", "拦截")
            out += _g(P.label_chip(rail - 4, y + bh / 2 + 34, "✕ " + mk, 14, s["bad"], s["bg"]), anim("opacity", show_from(tin[i] + .4, T, .2), T))
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
        legs.append((tout[0] + .5, 1))
        back.append((rail, top - 10))
        legs[-1] = (tout[0] + .5, 1)
        out += _travel(P, back, legs, T, sp.get("back_glyph", "响应"), s["accent2"] if s["accent2"] != s["ink"] else s["good"])
    return out, T


# ---------- 6. 闭环飞轮 ----------

def cycle(P, sp, top, bot):
    s = P.s
    steps = sp["steps"]
    m = len(steps)
    cx, cy = 375, (top + bot) / 2
    R = min(250, (bot - top) / 2 - 64)
    vals = (sp.get("center") or {}).get("values") or []
    rounds = sp.get("rounds") or max(1, len(vals)) or 2
    per = m * .95
    t0 = .6
    T = t0 + rounds * per + HOLD
    P.T = T
    out = P.stroke_path([(cx + R * math.cos(a / 60 * 2 * math.pi), cy + R * math.sin(a / 60 * 2 * math.pi)) for a in range(61)], s["rule"], 3)
    for i in range(m):
        a = -math.pi / 2 + 2 * math.pi * (i + .5) / m
        p = (cx + R * math.cos(a), cy + R * math.sin(a))
        q = (cx + R * math.cos(a + .04), cy + R * math.sin(a + .04))
        out += P.arrowhead(p, q, s["muted"], 12)
    w = 168 if m <= 6 else 146
    geo = []
    for i, st in enumerate(steps):
        a = -math.pi / 2 + 2 * math.pi * i / m
        h = P.card_h(st["title"], st.get("sub"), w, 18, 14, 14)
        x, y = cx + R * math.cos(a) - w / 2, cy + R * math.sin(a) - h / 2
        geo.append((x, y, w, h))
        out += P.card(x, y, w, h, st["title"], st.get("sub"), st.get("role", "node"), size=18, sub_size=14)
        out += P.text(x + 10, y + 16, f"{i + 1:02d}", 12, "mono", s["accent"], weight=700)
    c = sp.get("center") or {}
    if c.get("title"):
        out += P.text(cx, cy - 6, c["title"], 24, "title", s["ink"], "middle", s["title_weight"])
    if c.get("sub"):
        out += P.text(cx, cy + 22, c["sub"], 14, "body", s["muted"], "middle")
    lab = c.get("counter", "第{n}轮")
    for r in range(rounds):
        ts, te = t0 + r * per, t0 + (r + 1) * per
        last = r == rounds - 1
        txt = vals[r] if r < len(vals) else lab.replace("{n}", str(r + 1))
        out += _g(P.text(cx, cy + 58, txt, 22 if vals else 15, "mono", s["accent"], "middle", 700),
                  anim("opacity", window(ts, te - .15, T, .12) if not last else show_from(ts, T, .12), T), base_opacity=0 if not last else None)
        for i in range(m):
            tt = ts + per * i / m
            x, y, w2, h = geo[i]
            out += _lit(P, x, y, w2, h, window(tt, tt + .55, T, .12))
    d = f"M{n(cx)} {n(cy - R)} A{n(R)} {n(R)} 0 1 1 {n(cx)} {n(cy + R)} A{n(R)} {n(R)} 0 1 1 {n(cx)} {n(cy - R)}"
    legs = []
    for r in range(rounds):
        legs += [(t0 + r * per, 0), (t0 + (r + 1) * per - .001, 1)]
    out += _g(P.token(None, s["accent"], 11), motion(d, legs, T),
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
    badge_h = 110 if sp.get("badge") else 0
    lh = min(150, (bot - top - badge_h - 40) / k)
    y0 = top + 40 + max(0, (bot - top - badge_h - 40 - lh * k) / 2)
    x0, x1 = 40, 600
    fin = [t0 + D * it["value"] / vmax for it in items]
    T = max(fin) + .8 + HOLD
    P.T = T
    out = ""
    unit = sp.get("unit", "")
    dark = s["bg"] < "#888888"
    for i, it in enumerate(items):
        y = y0 + i * lh
        win = it.get("hl", i == best)
        out += P.text(x0, y + 4, it["name"], 20, "title", s["ink"], weight=800)
        if it.get("note"):
            out += P.text(x0 + text_w(it["name"], 20) + 12, y + 4, it["note"], 14, "body", s["muted"])
        by = y + 20
        bh = min(34, lh - 56)
        r = min(s["radius"], 8)
        out += f'<rect x="{x0}" y="{n(by)}" width="{x1 - x0}" height="{n(bh)}" rx="{r}" fill="{s["panel2"]}"/>'
        wf = (x1 - x0) * it["value"] / vmax
        col = s["accent"] if win else s["muted"]
        out += (f'<rect x="{x0}" y="{n(by)}" width="{n(wf)}" height="{n(bh)}" rx="{r}" fill="{col}">'
                + anim("width", [(0, 0), (t0, 0), (fin[i], n(wf)), (T - .5, n(wf)), (T - .15, 0)], T) + "</rect>")
        if P.rough:
            out += P.stroke_path([(x0, by), (x0 + wf, by), (x0 + wf, by + bh), (x0, by + bh)], s["ink"], 1.6, closed=True)
        val = it.get("label") or f'{it["value"]:,}{unit}'
        out += _g(P.text(x0 + wf + bh / 2 + 14, by + bh / 2 + 7, val, 19, "mono", s["accent"] if win else s["ink"], weight=800),
                  anim("opacity", show_from(fin[i], T, .2), T))
        out += _g(P.circle(x0 + wf, by + bh / 2, bh / 2 + 3, col, s["bg"] if not dark else s["ink"], 2.5),
                  motion(f"M{n(-wf)} 0 L0 0", [(0, 0), (t0, 0), (fin[i], 1), (T - .5, 1), (T - .15, 0)], T))
    if sp.get("badge"):
        out += _g(P.text(375, bot - 30, sp["badge"], 44, "title", s["accent"], "middle", s["title_weight"]),
                  anim("opacity", show_from(max(fin) + .2, T, .3), T))
    if sp.get("clock", True):
        ticks = 10
        lab = sp.get("meter", "{v}")
        for j in range(ticks + 1):
            tt = t0 + D * j / ticks
            txt = lab.replace("{v}", f"{vmax * j / ticks:,.0f}{unit}")
            last = j == ticks
            out += _g(P.text(710, top + 8, txt, 16, "mono", s["muted"], "end", 700),
                      anim("opacity", window(tt, tt + D / ticks - .02, T, .01) if not last else show_from(tt, T, .01), T),
                      base_opacity=None if last else 0)
    return out, T


# ---------- 8. 时间线 ----------

def timeline(P, sp, top, bot):
    s = P.s
    ev = sp["events"]
    m = len(ev)
    ax = 168
    step = (bot - top) / m
    ts = [.6 + i * 1.0 for i in range(m)]
    T = ts[-1] + .8 + HOLD
    P.T = T
    out = P.stroke_path([(ax, top), (ax, bot)], s["rule"], 3)
    out += _drawn(P, [(ax, top), (ax, bot)], s["accent"], 3, ts[0], ts[-1] + .3, T)
    for i, e in enumerate(ev):
        cy = top + step * (i + .5)
        hl = e.get("hl")
        w = 710 - 196
        h = min(step - 18, P.card_h(e["title"], e.get("sub"), w, 18, 14, 14))
        g = P.card(196, cy - h / 2, w, h, e["title"], e.get("sub"), "accent" if hl else "node", size=18, sub_size=14, align="left")
        g += P.text(ax - 22, cy + 7, e["time"], 20 if len(e["time"]) <= 6 else 15, "mono", s["accent"] if hl else s["ink"], "end", 800)
        out += _g(g, anim("opacity", show_from(ts[i], T, .35), T))
        out += P.circle(ax, cy, 8, s["bg"], s["ink"], 2.5)
        out += _g(P.circle(ax, cy, 8, s["accent"]), anim("opacity", show_from(ts[i], T, .1), T), base_opacity=0)
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
    widths = [190 + (600 - 190) * (x["value"] / v0) ** .6 for x in st] + [150]
    cx = 340
    out = ""
    N = sp.get("particles", 18)
    cnt = [max(1, round(N * x["value"] / v0)) for x in st]
    t0 = .5
    sp_band = .55
    ends = []
    for j in range(N):
        last = max(i for i in range(k) if j < cnt[i]) if j < cnt[0] else 0
        ts = t0 + j * .2
        ends.append(ts + (last + 1) * sp_band + .6)
    T = max(ends) + HOLD
    P.T = T
    for i, x in enumerate(st):
        y = top + i * (bh + gap)
        wt, wb = widths[i], widths[i + 1] if i < k - 1 else widths[i] * .82
        pts = [(cx - wt / 2, y), (cx + wt / 2, y), (cx + wb / 2, y + bh), (cx - wb / 2, y + bh)]
        role = x.get("role", "accent" if i == k - 1 else "node")
        f, stc, tc = P.role_colors(role)
        if role == "node" and s.get("tones"):
            f, tc = P.tone(i), s["ink"]
        if s.get("shadow"):
            o = s["shadow"]
            out += f'<path d="{poly_d([(a + o, b + o) for a, b in pts], True)}" fill="{s["ink"]}"/>'
        if s.get("misreg"):
            out += f'<path d="{poly_d([(a + 5, b + 5) for a, b in pts], True)}" fill="{s["accent"] if role != "accent" else s["accent2"]}" opacity=".5"/>'
        if P.rough:
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" opacity=".5"/>' + P.stroke_path(pts, stc, s["stroke"], closed=True)
        else:
            out += f'<path d="{poly_d(pts, True)}" fill="{f}" stroke="{stc}" stroke-width="{s["stroke"]}" stroke-linejoin="round"/>'
        out += P.text(cx, y + bh / 2 - 4, x["title"], 18, "title", tc, "middle", 800)
        out += P.text(cx, y + bh / 2 + 22, x.get("label") or f'{x["value"]:,}{sp.get("unit", "")}', 17, "mono", tc if role != "node" else s["accent"], "middle", 800)
        if i > 0:
            rate = x["value"] / st[i - 1]["value"] * 100
            out += P.text(690, y + 8, f"↓ {rate:.0f}%" if rate >= 1 else f"↓ {rate:.1f}%", 16, "mono", s["muted"], "end", 700)
        if x.get("note"):
            out += P.text(690, y + 30, x["note"], 13, "body", s["muted"], "end")
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
        legs = [(ts, 0), (ts + dur, 1)]
        col = s["accent"] if survived else s["muted"]
        out += _g(P.circle(0, 0, 6, col, s["ink"] if P.rough else "none", 1), motion(poly_d(pts), legs, T),
                  anim("opacity", [(0, 0), (ts, 0), (ts + .1, 1), (ts + dur - (0 if survived else .35), 1), (ts + dur + .1, 0)] if not survived
                       else [(0, 0), (ts, 0), (ts + .1, 1), (T - .5, 1), (T - .15, 0)], T), base_opacity=0)
    return out, T


# ---------- 10. 逐层展开（思维导图） ----------

def tree(P, sp, top, bot):
    s = P.s
    root = sp["root"]
    kids = sp.get("children", [])
    k = len(kids)
    rw = min(420, max(240, text_w(root["title"], 21) + 60))
    rh = P.card_h(root["title"], root.get("sub"), rw, 21)
    out = ""
    rx = 375 - rw / 2
    t = .5
    gap = 14
    cw = (670 - gap * (k - 1)) / k
    h1 = max(P.card_h(c["title"], c.get("sub"), cw, 18, 14) for c in kids)
    m2 = max([len(c.get("children", [])) for c in kids] + [1])
    s2 = min(104, (bot - top - rh - 64 - h1 - 24) / m2)
    h2 = min(s2 - 16, 64)
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
    out += _g(P.card(rx, ry, rw, rh, root["title"], root.get("sub"), root.get("role", "dark"), size=21),
              anim("opacity", show_from(sched["root"], T), T))
    for i, c in enumerate(kids):
        x = 40 + i * (cw + gap)
        p, q = (375, ry + rh), (x + cw / 2, y1 - 4)
        tt = sched[("c", i)]
        out += _drawn(P, elbow(p, q), s["ink"], s["stroke"], tt - .3, tt, T, arrow=False)
        out += _g(P.card(x, y1, cw, h1, c["title"], c.get("sub"), c.get("role", "accent" if c.get("hl") else "node"), size=18, sub_size=14),
                  anim("opacity", show_from(tt, T), T))
        rail_x = x + 16
        for j, g in enumerate(c.get("children", [])):
            gy = y1 + h1 + 20 + j * s2
            tg = sched[("g", i, j)]
            pts = [(rail_x, y1 + h1 if j == 0 else y1 + h1 + 20 + (j - 1) * s2 + h2 / 2), (rail_x, gy + h2 / 2), (rail_x + 14, gy + h2 / 2)]
            out += _drawn(P, pts, s["muted"], 1.6, tg - .2, tg, T)
            gw = cw - 30
            out += _g(P.card(rail_x + 14, gy, gw, h2, g["title"], g.get("sub"), g.get("role", "soft"), size=17 if h2 > 52 else 15, sub_size=13),
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
    x0, x1 = 92, 710
    yb, yt = bot - 64, top + 46
    ah = yb - yt
    slot = (x1 - x0) / k
    unit = sp.get("unit", "")
    ts = [.5 + i * .38 for i in range(k)]
    T = ts[-1] + 1.2 + HOLD
    P.T = T
    out = ""
    for j in range(5):
        y = yb - ah * j / 4
        out += f'<path d="M{x0} {n(y)}H{x1}" stroke="{s["rule"]}" stroke-width="{1.6 if j == 0 else .8}"/>'
        v = vmax * j / 4
        out += P.text(x0 - 10, y + 5, f"{v:,.0f}" if vmax >= 10 else f"{v:.1f}", 13, "mono", s["muted"], "end")
    if sp.get("y_label"):
        out += P.text(40, yt - 22, sp["y_label"], 13, "mono", s["muted"], weight=700)
    hl = [i for i, x in enumerate(ser) if x.get("hl")] or [max(range(k), key=lambda i: ser[i]["value"])]
    pts = []
    for i, x in enumerate(ser):
        cx = x0 + slot * (i + .5)
        h = ah * x["value"] / vmax
        is_hl = i in hl
        lab = wrap(x["label"], 15, slot - 6, 2)
        out += P.lines(cx, yb + 24, lab, 15, 18, role="body", fill=s["ink"], anchor="middle")
        val = x.get("text") or (f'{x["value"]:,}' if isinstance(x["value"], int) else f'{x["value"]}') + unit
        if kind == "bar":
            bw = min(64, slot * .6)
            col = s["accent"] if is_hl else (s["panel2"] if s["bg"] > "#888888" else s["muted"])
            stroke = f' stroke="{s["ink"]}" stroke-width="1.5"' if not is_hl and s["bg"] > "#888888" else ""
            out += (f'<rect x="{n(cx - bw / 2)}" y="{n(yb - h)}" width="{n(bw)}" height="{n(h)}" fill="{col}"{stroke}>'
                    + anim("height", [(0, 0), (ts[i], 0), (ts[i] + .7, n(h)), (T - .5, n(h)), (T - .15, 0)], T)
                    + anim("y", [(0, n(yb)), (ts[i], n(yb)), (ts[i] + .7, n(yb - h)), (T - .5, n(yb - h)), (T - .15, n(yb))], T) + "</rect>")
            if P.rough:
                out += _g(P.stroke_path([(cx - bw / 2, yb), (cx - bw / 2, yb - h), (cx + bw / 2, yb - h), (cx + bw / 2, yb)], s["ink"], 1.8),
                          anim("opacity", show_from(ts[i] + .7, T, .2), T))
            out += _g(P.text(cx, yb - h - 10, val, 17 if is_hl else 15, "mono", s["accent"] if is_hl else s["ink"], "middle", 800),
                      anim("opacity", show_from(ts[i] + .6, T, .2), T))
        pts.append((cx, yb - h))
    if kind == "line":
        out += _drawn(P, pts, s["accent"], 3.2, ts[0], ts[-1] + .4, T)
        for i, (px, py) in enumerate(pts):
            is_hl = i in hl
            x = ser[i]
            val = x.get("text") or f'{x["value"]}{unit}'
            tt = ts[0] + (ts[-1] + .4 - ts[0]) * i / max(1, k - 1)
            out += _g(P.circle(px, py, 8 if is_hl else 5, s["accent"] if is_hl else s["bg"], s["accent"], 2.5)
                      + P.text(px, py - 16, val, 16 if is_hl else 14, "mono", s["accent"] if is_hl else s["ink"], "middle", 800),
                      anim("opacity", show_from(tt, T, .15), T))
    if sp.get("note"):
        i = hl[0]
        px, py = pts[i]
        nx = min(max(px - 160, 260), 520)
        out += _g(P.label_chip(nx, yt + 30, sp["note"], 15, s["accent"], s["accent_ink"]), anim("opacity", show_from(ts[-1] + .8, T, .3), T))
    return out, T


# ---------- 12. 网络扩散 ----------

def network(P, sp, top, bot):
    s = P.s
    waves = sp["waves"]
    K = len(waves)
    cx, cy = 375, (top + bot) / 2 + 10
    rxm, rym = 300, (bot - top) / 2 - 46
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
        out += f'<ellipse cx="{cx}" cy="{n(cy)}" rx="{n(rxm * k / (K - 1))}" ry="{n(rym * k / (K - 1))}" fill="none" stroke="{s["rule"]}" stroke-width="1" stroke-dasharray="3 6"/>'
    for k, a, b in edges:
        p, q = pos[a[0]][a[1]], pos[b[0]][b[1]]
        ra = 34 if a[0] == 0 else 20
        L = math.dist(p, q)
        u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
        pts = [(p[0] + u[0] * ra, p[1] + u[1] * ra), (q[0] - u[0] * 22, q[1] - u[1] * 22)]
        out += P.stroke_path(pts, s["rule"], 1.5)
        out += _drawn(P, pts, s["accent"], 2.2, tw[k] - .7, tw[k] - .1, T)
    for k in range(1, K):
        out += (f'<ellipse cx="{cx}" cy="{n(cy)}" rx="0" ry="0" fill="none" stroke="{s["accent"]}" stroke-width="3" opacity="0">'
                + anim("rx", [(0, 0), (tw[k] - .8, n(rxm * (k - 1) / (K - 1))), (tw[k], n(rxm * k / (K - 1)))], T)
                + anim("ry", [(0, 0), (tw[k] - .8, n(rym * (k - 1) / (K - 1))), (tw[k], n(rym * k / (K - 1)))], T)
                + anim("opacity", [(0, 0), (tw[k] - .8, 0), (tw[k] - .7, .7), (tw[k], 0)], T) + "</ellipse>")
    for k, wv in enumerate(waves):
        for j, lab in enumerate(wv):
            px, py = pos[k][j]
            r = 34 if k == 0 else 20
            out += P.circle(px, py, r, s["panel"], s["ink"], s["stroke"])
            out += _g(P.circle(px, py, r, s["accent"]) + (P.circle(px, py, r + 8, s["accent"], extra=' opacity=".2"') if s.get("glow") else ""),
                      anim("opacity", show_from(tw[k], T, .2), T))
            if k == 0:
                tl = wrap(lab, 15, 60, 2)
                out += P.lines(px, py + 6 - (len(tl) - 1) * 9, tl, 15, 18, role="title", fill=s["ink"], anchor="middle", weight=800)
                out += _g(P.lines(px, py + 6 - (len(tl) - 1) * 9, tl, 15, 18, role="title", fill=s["accent_ink"], anchor="middle", weight=800),
                          anim("opacity", show_from(tw[0], T, .2), T))
            else:
                tl = wrap(lab, 13, 96, 2)
                out += P.lines(px, py + r + 18, tl, 13, 16, role="body", fill=s["ink"], anchor="middle")
    counts = sp.get("counts")
    if counts:
        lab = sp.get("counter", "{v}")
        for k in range(K):
            last = k == K - 1
            out += _g(P.text(710, top + 4, lab.replace("{v}", str(counts[k])), 18, "mono", s["accent"], "end", 800),
                      anim("opacity", window(tw[k], tw[k + 1] - .05, T, .1) if not last else show_from(tw[k], T, .1), T), base_opacity=0 if not last else None)
    return out, T


# ---------- 13. 前后对比 ----------

def versus(P, sp, top, bot):
    s = P.s
    L, Rt = sp["left"], sp["right"]
    colw = 315
    xs = [40, 395]
    badge_h = 92 if sp.get("badge") else 0
    hh = 74
    steps_top = top + hh + 18
    steps_bot = bot - badge_h - 70
    m = max(len(L["steps"]), len(Rt["steps"]))
    sg = min(100, (steps_bot - steps_top) / m)
    sh = min(sg - 16, 68)
    slow = sp.get("slow_dur", 5.4)
    ratio = sp.get("speed_ratio", .3)
    t0 = .7
    dl = slow / len(L["steps"])
    dr = max(.35, slow * ratio / len(Rt["steps"]))
    end_l, end_r = t0 + dl * len(L["steps"]), t0 + dr * len(Rt["steps"])
    T = max(end_l, end_r) + 1.0 + HOLD
    P.T = T
    out = ""
    for side, (col, x, dt, tend) in enumerate(((L, xs[0], dl, end_l), (Rt, xs[1], dr, end_r))):
        role = "soft" if side == 0 else "accent"
        out += P.card(x, top, colw, hh, col["title"], col.get("sub"), role, size=21, sub_size=14)
        for i, stp in enumerate(col["steps"]):
            y = steps_top + i * sg
            out += P.card(x, y, colw, sh, stp, None, "node", size=16, align="left")
            tt = t0 + dt * (i + 1)
            out += _lit(P, x, y, colw, sh, show_from(tt - dt * .9, T, .15), s["accent"] if side else s["muted"])
            out += _g(P.text(x + colw - 16, y + sh / 2 + 7, "✓", 20, "mono", s["good"], "end", 800), anim("opacity", show_from(tt, T, .1), T))
        by = steps_bot + 14
        out += f'<rect x="{x}" y="{n(by)}" width="{colw}" height="10" rx="5" fill="{s["panel2"]}"/>'
        out += (f'<rect x="{x}" y="{n(by)}" width="{colw}" height="10" rx="5" fill="{s["accent"] if side else s["muted"]}">'
                + anim("width", [(0, 0), (t0, 0), (tend, colw), (T - .5, colw), (T - .15, 0)], T) + "</rect>")
        if col.get("total"):
            out += _g(P.text(x + colw / 2, by + 46, col["total"], 26, "mono", s["accent"] if side else s["ink"], "middle", 800),
                      anim("opacity", show_from(tend, T, .25), T))
    if sp.get("badge"):
        out += _g(P.text(375, bot - 20, sp["badge"], 42, "title", s["accent"], "middle", s["title_weight"]),
                  anim("opacity", show_from(max(end_l, end_r) + .3, T, .35), T))
    return out, T


LAYOUTS = dict(flow=flow, sequence=sequence, state=state, pipeline=pipeline, layers=layers, cycle=cycle,
               race=race, timeline=timeline, funnel=funnel, tree=tree, bars=bars, network=network, versus=versus)
