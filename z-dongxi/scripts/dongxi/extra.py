"""第三批图型（4 种）：层级状态机、等距堆叠、坡度图、气泡图。

规则同 layouts.py：共用周期 T，按时间出场，静态渲染即终态，坐标全部从画布推出。
"""
import math

from .core import anim, cubic, fit, motion, n, poly_d, shade, show_from, text_w, window, wrap
from .layouts import HOLD, _drawn, _g, _lit, _travel
from .charts import _legend, _num, pal


def _note(P, x, y, side, text, room, t0=None):
    """引线注解：状态边上一个小圆点，折线拉到页边，斜体小字。"""
    s = P.s
    size = 15
    tw = max(80, room - 34)
    tl = wrap(text, size, tw, 3)
    x1 = x + (24 if side > 0 else -24)
    out = P.circle(x, y, 3.2, s["ink"])
    out += f'<path d="M{n(x)} {n(y)}L{n(x1)} {n(y)}" stroke="{s["ink"]}" stroke-width="1" stroke-dasharray="2 3"/>'
    tx = x1 + (6 if side > 0 else -6)
    anc = "start" if side > 0 else "end"
    out += P.lines(tx, y + 5 - (len(tl) - 1) * 10, tl, size, 20, role="body", fill=s["muted"], anchor=anc, extra=' font-style="italic"')
    return _g(out, anim("opacity", show_from(t0, P.T, .3), P.T)) if t0 is not None else out


# ---------- 1. 层级状态机 ----------

def statechart(P, sp, top, bot):
    """状态可以嵌套（parent），复合状态可以并行（parallel + region），转移带守卫条件。
    bug 字段画一条违反规则的路径并在终点盖章。"""
    s = P.s
    sts = {st["id"]: st for st in sp["states"]}
    order = [st["id"] for st in sp["states"]]
    kids = {}
    for st in sp["states"]:
        if st.get("parent"):
            kids.setdefault(st["parent"], []).append(st["id"])
    tops = [i for i in order if not sts[i].get("parent")]
    trans = sp.get("transitions", [])
    bug = sp.get("bug")
    if bug:
        bot -= 92

    def chain(i):
        out = [i]
        while sts[out[-1]].get("parent"):
            out.append(sts[out[-1]]["parent"])
        return out

    # 顶层排行：最长路径，忽略回边
    succ = {u: [] for u in tops}
    for t in trans:
        a, b = chain(t["from"])[-1], chain(t["to"])[-1]
        if a != b and b not in succ[a]:
            succ[a].append(b)
    seen, stack, back = set(), set(), set()

    def dfs(u):
        seen.add(u)
        stack.add(u)
        for v in succ[u]:
            if v in stack:
                back.add((u, v))
            elif v not in seen:
                dfs(v)
        stack.discard(u)
    dfs(chain(sp.get("initial") or tops[0])[-1])
    for u in tops:
        if u not in seen:
            dfs(u)
    rank = {u: 0 for u in tops}
    for _ in tops:
        for u in tops:
            for v in succ[u]:
                if (u, v) not in back and rank[v] < rank[u] + 1:
                    rank[v] = rank[u] + 1
    for u in tops:
        if "rank" in sts[u]:
            rank[u] = sts[u]["rank"]

    # 尺寸
    size = {}

    def leaf_size(i, maxw=270):
        st = sts[i]
        w = min(maxw, max(150, text_w(st["title"], P.f["node"]) + 56, text_w(st.get("sub") or "", P.f["sub"]) * .6 + 40))
        return w, P.card_h(st["title"], st.get("sub"), w)

    horiz = (sp.get("direction") or ("LR" if P.land else "TB")).upper() == "LR"
    vgap = 78 if any(t.get("guard") for t in trans) else 60
    inner = {}
    for u in tops:
        if u not in kids:
            size[u] = leaf_size(u)
            continue
        ch = kids[u]
        if sts[u].get("parallel"):
            regs = []
            for c in ch:
                r = sts[c].get("region", "")
                if r not in regs:
                    regs.append(r)
            fw = P.CW * (.5 if horiz else 1)
            cw = (fw - 28 * (len(regs) + 1)) / len(regs)
            cols, hmax = [], 0
            for r in regs:
                mem = [c for c in ch if sts[c].get("region", "") == r]
                hs = [leaf_size(c, cw - 20)[1] for c in mem]
                for c in mem:
                    size[c] = (min(cw - 20, leaf_size(c, cw - 20)[0]), leaf_size(c, cw - 20)[1])
                colh = sum(hs) + vgap * (len(mem) - 1)
                hmax = max(hmax, colh)
                cols.append((r, mem))
            inner[u] = ("par", cols, cw)
            size[u] = (fw, 58 + 40 + hmax + 26)
        else:
            for c in ch:
                size[c] = leaf_size(c, 210)
            rw = sum(size[c][0] for c in ch) + 54 * (len(ch) - 1)
            hmax = max(size[c][1] for c in ch)
            inner[u] = ("row", ch, None)
            size[u] = (min(P.CW, max(rw + 2 * 46, text_w(sts[u]["title"], 20) + 80)), 58 + hmax + 30)

    R = max(rank.values()) + 1
    rows = [[u for u in tops if rank[u] == r] for r in range(R)]
    row_h = [max(size[u][1] for u in row) if row else 0 for row in rows]
    lead = 46
    geo = {}
    if horiz:
        col_w = [max(size[u][0] for u in row) if row else 0 for row in rows]
        col_h = [sum(size[u][1] for u in row) + 50 * (len(row) - 1) for row in rows]
        avail = P.CW - 40
        gap = max(64, min(130, (avail - sum(col_w)) / max(1, R - 1)))
        used = sum(col_w) + gap * (R - 1)
        k_fit = min(1, avail / used, (bot - top - 40) / max(col_h))
        x = P.CX - used / 2 + 20
        for r, row in enumerate(rows):
            y = (top + bot) / 2 - col_h[r] / 2
            for u in row:
                w, h = size[u]
                geo[u] = (x + (col_w[r] - w) / 2, y, w, h)
                y += h + 50
            x += col_w[r] + gap
    else:
        avail = bot - top - lead
        gap = max(52, min(118, (avail - sum(row_h)) / max(1, R - 1)))
        used = sum(row_h) + gap * (R - 1)
        k_fit = min(1, avail / used)
        y = top + lead + max(0, (avail - used) / 2)
        for r, row in enumerate(rows):
            tw = sum(size[u][0] for u in row) + 44 * (len(row) - 1)
            x = P.CX - tw / 2
            for u in row:
                w, h = size[u]
                geo[u] = (x, y + (row_h[r] - h) / 2, w, h)
                x += w + 44
            y += row_h[r] + gap
    # 子状态位置
    for u, (mode, data, cw) in inner.items():
        fx, fy, fw, fh = geo[u]
        if mode == "row":
            tw = sum(size[c][0] for c in data) + 54 * (len(data) - 1)
            x = fx + (fw - tw) / 2 + 10
            for c in data:
                w, h = size[c]
                geo[c] = (x, fy + 58 + (fh - 88 - h) / 2, w, h)
                x += w + 54
        else:
            for k, (r, mem) in enumerate(data):
                cx = fx + 28 + k * (cw + 28) + cw / 2
                yy = fy + 58 + 40
                for c in mem:
                    w, h = size[c]
                    geo[c] = (cx - w / 2, yy, w, h)
                    yy += h + vgap

    def rect(i):
        x, y, w, h = geo[i]
        return x, y, w, h, x + w / 2, y + h / 2

    lanes = {"r": 0, "l": 0}

    def route(a, b, off=0):
        ax, ay, aw, ah, acx, acy = rect(a)
        bx, by, bw, bh, bcx, bcy = rect(b)
        if a == b:
            x0 = ax + aw
            return cubic((x0, acy - 12), (x0 + 58, acy - 40), (x0 + 58, acy + 40), (x0 + 2, acy + 12))
        if horiz and bx >= ax + aw + 8:
            p0, p1 = (ax + aw, acy + off), (bx - 2, bcy + off)
            k = (p1[0] - p0[0]) * .45
            return cubic(p0, (p0[0] + k, p0[1]), (p1[0] - k, p1[1]), p1)
        if horiz and bx + bw <= ax - 8:
            lanes["r"] += 1
            yl = min(bot + 30, max(ay + ah, by + bh) + 26 + 16 * lanes["r"])
            return [(acx, ay + ah), (acx, yl), (bcx, yl), (bcx, by + bh + 2)]
        if by >= ay + ah + 8:
            dx = max(-aw * .32, min(aw * .32, (bcx - acx) * .3))
            ex = max(-bw * .32, min(bw * .32, (acx - bcx) * .3))
            p0, p1 = (acx + dx + off, ay + ah), (bcx + ex + off, by - 2)
            k = (p1[1] - p0[1]) * .45
            return cubic(p0, (p0[0], p0[1] + k), (p1[0], p1[1] - k), p1)
        if by + bh <= ay - 8:
            side = 1 if max(ax + aw, bx + bw) + 40 <= P.R + 30 else -1
            key = "r" if side > 0 else "l"
            lanes[key] += 1
            if side > 0:
                xl = min(P.W - 14, max(ax + aw, bx + bw) + 22 + 16 * lanes[key])
                p0, p1 = (ax + aw, acy + off), (bx + bw + 2, bcy + off)
            else:
                xl = max(14, min(ax, bx) - 22 - 16 * lanes[key])
                p0, p1 = (ax, acy + off), (bx - 2, bcy + off)
            return [p0, (xl, p0[1]), (xl, p1[1]), p1]
        if bcx > acx:
            p0, p1 = (ax + aw, acy + off), (bx - 2, bcy + off)
        else:
            p0, p1 = (ax, acy + off), (bx + bw + 2, bcy + off)
        k = (p1[0] - p0[0]) * .4
        return cubic(p0, (p0[0] + k, p0[1]), (p1[0] - k, p1[1]), p1)

    pairs = {(t["from"], t["to"]) for t in trans}
    tp = {}
    for t in trans:
        u, v = t["from"], t["to"]
        off = 10 if (v, u) in pairs and u != v else 0
        tp[(u, v)] = route(u, v, off if u < v else -off)

    # 漫游路线
    def expand(i):
        if i in kids:
            if sts[i].get("parallel"):
                out = []
                for r, mem in inner[i][1]:
                    first = next((c for c in mem if sts[c].get("initial")), mem[0])
                    out += expand(first)
                return out
            first = next((c for c in kids[i] if sts[c].get("initial")), kids[i][0])
            return expand(first)
        return [i]
    walk = sp.get("walk")
    if not walk:
        cur, walk, used_t = sp.get("initial") or tops[0], [], set()
        walk.append(cur)
        for _ in range(7):
            nxt = next((t for t in trans if t["from"] in chain(expand(cur)[0]) and id(t) not in used_t and t["to"] != t["from"]), None)
            if not nxt:
                break
            used_t.add(id(nxt))
            cur = nxt["to"]
            walk.append(cur)
    steps = [sum((expand(i) for i in (w if isinstance(w, list) else [w])), []) for w in walk]

    t = .7
    arr = []
    for i in range(len(steps)):
        arr.append(t)
        t += .75 + (.85 if i < len(steps) - 1 else 0)
    t_bug = t + .3
    if bug:
        t += .9 * (len(bug.get("path", [])) - 1) + 1.6
    T = t + HOLD
    P.T = T

    out = ""
    # 复合状态外框
    for u in tops:
        if u not in kids:
            continue
        x, y, w, h = geo[u]
        st = sts[u]
        tone = s.get("tones", [s["panel2"]])[1 % len(s.get("tones", [s["panel2"]]))]
        if P.rough:
            pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            out += f'<path d="{P.shape_d(x, y, w, h)}" fill="{tone}" opacity=".32"/>' + P.stroke_path(pts, s["ink"], 1.5, closed=True)
        else:
            out += f'<path d="{P.shape_d(x, y, w, h, max(s["radius"], 6))}" fill="{s["panel2"]}" fill-opacity=".55" stroke="{s["ink"]}" stroke-width="1.6"/>'
        tl = fit(st["title"], 21, w - 120, 16)
        out += P.text(x + 20, y + 34, st["title"], tl, "title", s["ink"], weight=s["title_weight"] if s["title_weight"] < 900 else 800)
        tag = "∥ 并行" if st.get("parallel") else "复合"
        out += P.text(x + w - 18, y + 32, st.get("tag") or tag, P.f["small"], "mono", s["muted"], "end", 700)
        out += f'<path d="M{n(x + 14)} {n(y + 46)}H{n(x + w - 14)}" stroke="{s["rule"]}" stroke-width="1.2"/>'
        if inner[u][0] == "par":
            cw = inner[u][2]
            for k, (r, mem) in enumerate(inner[u][1]):
                cx = x + 28 + k * (cw + 28)
                out += P.text(cx + cw / 2, y + 76, r, P.f["mono"], "mono", s["accent2"] if k % 2 else s["accent"], "middle", 800, 2)
                if k:
                    out += f'<path d="M{n(cx - 14)} {n(y + 56)}V{n(y + h - 12)}" stroke="{s["muted"]}" stroke-width="1.4" stroke-dasharray="6 6"/>'
    # 转移线
    for tr in trans:
        pts = tp[(tr["from"], tr["to"])]
        out += P.edge(pts, s["muted"] if tr.get("dashed") else None, dash="7 6" if tr.get("dashed") else None, sw=1.9)
    # 状态卡
    tone_i = 0
    for i in order:
        if i in kids:
            continue
        x, y, w, h = geo[i]
        st = sts[i]
        role = st.get("role") or {"final": "dark", "end": "dark", "error": "accent"}.get(st.get("kind"), "node")
        out += P.card(x, y, w, h, st["title"], st.get("sub"), role, tone_i if role == "node" else None, size=22 if st.get("parent") else None)
        if role == "node":
            tone_i += 1
    # 初始点
    starts = [chain(sp.get("initial") or tops[0])[-1]]
    top0 = starts[0]
    for u in kids:
        if sts[u].get("parallel"):
            starts += [next((c for c in mem if sts[c].get("initial")), mem[0]) for r, mem in inner[u][1]]
        else:
            starts.append(next((c for c in kids[u] if sts[c].get("initial")), kids[u][0]))
    for i in starts:
        x, y, w, h, cx, cy = rect(i)
        par = sts[i].get("parent")
        if par or (horiz and i == top0):
            p0, p1 = (x - 30, cy), (x - 3, cy)
        else:
            p0, p1 = (cx, y - 30), (cx, y - 3)
        out += P.circle(p0[0], p0[1], 7, s["ink"]) + P.edge([p0, p1], s["ink"], sw=1.6)
    # 标签（压在线上面）
    for tr in trans:
        pts = tp[(tr["from"], tr["to"])]
        if tr["from"] == tr["to"]:
            mx, my = pts[len(pts) // 2][0] + 8, pts[len(pts) // 2][1] + 6
            anc_shift = text_w(tr.get("label", ""), 16) / 2 + 10
            mx += anc_shift
        elif len(pts) == 4 and abs(pts[1][1] - pts[2][1]) < 1:
            mx, my = (pts[1][0] + pts[2][0]) / 2, pts[1][1] + 6
        elif len(pts) == 4:
            side = 1 if pts[1][0] > pts[0][0] else -1
            mx, my = pts[1][0], (pts[1][1] + pts[2][1]) / 2
            lw = max(text_w(tr.get("label", ""), 17), text_w(tr.get("guard", ""), 15) + 16) + 12
            mx = mx - lw / 2 - 6 if side > 0 else mx + lw / 2 + 6
        else:
            mx, my = pts[len(pts) // 2]
            my += 6
            a, b = pts[0], pts[-1]
            if abs(b[1] - a[1]) > abs(b[0] - a[0]) * 1.2:
                lw = max(text_w(tr.get("label", ""), 17), text_w(tr.get("guard", ""), 15) + 16) + 12
                mx += lw / 2 + 8 if b[0] >= a[0] - 4 else -(lw / 2 + 8)
        if tr.get("label"):
            out += P.label_chip(mx, my - (9 if tr.get("guard") else 0), tr["label"])
        if tr.get("guard"):
            g = f"[{tr['guard']}]"
            out += P.text(mx, my + 13, g, 15, "mono", s["accent2"] if s["accent2"] != s["ink"] else s["accent"], "middle", 700)
    # 注解
    for i in order:
        note = sts[i].get("note")
        if not note or i in kids:
            continue
        x, y, w, h, cx, cy = rect(i)
        lr, rr = x - P.L + 30, P.R + 30 - (x + w)
        for j in order:
            if j == i or j in kids or sts[j].get("parent") == i:
                continue
            jx, jy, jw, jh = geo[j]
            if jy < y + h and jy + jh > y:
                if jx >= x + w:
                    rr = min(rr, jx - (x + w) - 10)
                elif jx + jw <= x:
                    lr = min(lr, x - (jx + jw) - 10)
        if max(lr, rr) < 120:
            continue
        side = 1 if rr >= lr else -1
        out += _note(P, x + w + 6 if side > 0 else x - 6, cy, side, note, max(lr, rr) - 20)
    # 动画：逐步点亮
    for k, leaves in enumerate(steps):
        t_end = arr[k] + .75
        last = k == len(steps) - 1
        lit_pts = window(arr[k], t_end, T, .15) if not last else show_from(arr[k], T, .15)
        for i in leaves:
            x, y, w, h = geo[i]
            out += _lit(P, x, y, w, h, lit_pts)
            par = sts[i].get("parent")
            if par:
                fx, fy, fw, fh = geo[par]
                out += _g(f'<path d="{P.shape_d(fx - 3, fy - 3, fw + 6, fh + 6, max(s["radius"], 6) + 3)}" fill="none" stroke="{s["accent"]}" stroke-width="2.4" stroke-dasharray="3 6"/>',
                          anim("opacity", lit_pts, T), base_opacity=0)
        if last:
            break
        prev, nxt = steps[k], steps[k + 1]
        for v in nxt:
            if v in prev:
                continue
            hit = None
            for u in prev:
                for tr in trans:
                    if tr["from"] in chain(u) and tr["to"] in chain(v):
                        hit = tr
                        break
                if hit:
                    break
            if hit:
                pts = tp[(hit["from"], hit["to"])]
                out += _g(P.stroke_path(pts, s["accent"], 4.2), anim("opacity", window(t_end, t_end + .85, T, .1), T), base_opacity=0)
                out += _travel(P, pts, [(t_end, 0), (t_end + .85, 1)], T)
    # 违规路径
    if bug:
        bc = s["bad"]
        path = bug.get("path", [])
        tb = t_bug
        for a, b in zip(path, path[1:]):
            pts = tp.get((a, b))
            if pts:
                out += _g(P.stroke_path(pts, bc, 5, "1 8") + P.stroke_path(pts, bc, 2), anim("opacity", show_from(tb, T, .4), T))
            tb += .9
        if path:
            x, y, w, h, cx, cy = rect(path[-1])
            stamp = bug.get("stamp", "BUG")
            sw_ = text_w(stamp, 20) + 26
            g = (f'<g transform="rotate(-9 {n(x + w - 10)} {n(y)})">'
                 f'<rect x="{n(x + w - sw_ + 14)}" y="{n(y - 22)}" width="{n(sw_)}" height="34" rx="3" fill="{s["bg"]}" fill-opacity=".85" stroke="{bc}" stroke-width="2.6"/>'
                 + P.text(x + w + 14 - sw_ / 2, y + 2, stamp, 20, "mono", bc, "middle", 800, 2) + "</g>")
            out += _g(g, anim("opacity", show_from(tb, T, .25), T))
            for i in path[:1]:
                pass
        rb = bot + 18
        rule = bug.get("rule", "")
        box = f'<rect x="{P.L}" y="{n(rb)}" width="{P.CW}" height="70" fill="{s["bg"]}" stroke="{bc}" stroke-width="1.6" stroke-dasharray="8 5"/>'
        box += P.text(P.L + 18, rb + 30, bug.get("title", "规则"), P.f["mono"], "mono", bc, weight=800, ls=2)
        rl = wrap(rule, 18, P.CW - 36, 2)
        box += P.lines(P.L + 18, rb + 30 + (24 if len(rl) == 1 else 22), rl, 18 if len(rl) == 1 else 16, 21, role="body", fill=s["ink"])
    if k_fit < 1:
        k = k_fit
        oy = (top + bot) / 2 if horiz else top
        out = f'<g transform="translate({n(P.CX * (1 - k))} {n(oy * (1 - k))}) scale({k:.3f})">{out}</g>'
    if bug:
        out += box
    return out, T


# ---------- 2. 等距堆叠 ----------

def iso(P, sp, top, bot):
    """等距视角的分层块，自下而上落位；一个小包裹从顶层穿到底层，每层右侧拉引线写说明。
    顶层上有个小人来回走。"""
    s = P.s
    lay = sp["layers"]
    m = len(lay)
    c30, s30 = math.cos(math.pi / 6), .5
    land = P.land
    left_w = P.CW * (.5 if land else .56)
    th = 22
    head = 70
    avail = bot - top - head - 10
    A = min(left_w / (2 * c30), 220, (avail - th - (m - 1) * (th + 16)) / (1 + .5 * (m - 1)))
    step = .5 * A + th + 16 if m > 1 else 0
    used = A + th + step * (m - 1)
    ox = P.L + left_w / 2 + (10 if not land else 30)
    oy = top + head + max(0, (avail - used) / 2)

    def pt(u, v, z, k):
        """u、v 是顶面坐标（0..A），z 是向下的厚度，k 是层号。"""
        return (ox + (u - v) * c30, oy + (u + v) * s30 + k * step + z)

    tones = s.get("tones") or [s["panel"], s["panel2"]]
    order = list(range(m))[::-1]
    t_drop = [.5 + j * .55 for j in range(m)]
    t_pk = t_drop[-1] + .9
    t_end_pk = t_pk + .5 * m + .6
    T = t_end_pk + HOLD
    P.T = T
    out = ""
    # 中轴虚线
    top_c, bot_c = pt(A / 2, A / 2, 0, 0), pt(A / 2, A / 2, th, m - 1)
    out += f'<path d="M{n(top_c[0])} {n(top_c[1] - 60)}V{n(bot_c[1] + 40)}" stroke="{s["muted"]}" stroke-width="1.2" stroke-dasharray="3 6"/>'
    cl = pal(P)
    for j, k in enumerate(order):
        L = lay[k]
        f = L.get("color") or (shade(s["accent"], s["panel"], .35) if L.get("highlight") else tones[k % len(tones)])
        if P.dark and not L.get("color") and not L.get("highlight"):
            f = shade(s["panel"], tones[k % len(tones)], .35)
        lf, rf = shade(f, s["ink"], .14), shade(f, s["ink"], .3)
        topf = [pt(0, 0, 0, k), pt(A, 0, 0, k), pt(A, A, 0, k), pt(0, A, 0, k)]
        lface = [pt(0, A, 0, k), pt(A, A, 0, k), pt(A, A, th, k), pt(0, A, th, k)]
        rface = [pt(A, 0, 0, k), pt(A, A, 0, k), pt(A, A, th, k), pt(A, 0, th, k)]
        st = s["ink"]
        g = ""
        for face, col in ((lface, lf), (rface, rf), (topf, f)):
            if P.rough:
                g += f'<path d="{poly_d(face, True)}" fill="{col}"/>' + P.stroke_path(face, st, 1.6, closed=True)
            else:
                g += f'<path d="{poly_d(face, True)}" fill="{col}" stroke="{st}" stroke-width="1.6" stroke-linejoin="round"/>'
        # 顶面网格：每层四等分，像地板砖
        gl = ""
        for q in (1, 2, 3):
            u = A * q / 4
            a, b = pt(u, 0, 0, k), pt(u, A, 0, k)
            c, d = pt(0, u, 0, k), pt(A, u, 0, k)
            gl += f"M{n(a[0])} {n(a[1])}L{n(b[0])} {n(b[1])}M{n(c[0])} {n(c[1])}L{n(d[0])} {n(d[1])}"
        g += f'<path d="{gl}" stroke="{st}" stroke-width=".8" opacity=".22"/>'
        # 左侧序号
        lp = pt(0, A, th / 2, k)
        num = L.get("tag") or f"L{m - k}"
        g += P.text(lp[0] - 14, lp[1] + 5, num, P.f["mono"], "mono", s["muted"], "end", 800)
        # 右侧引线 + 文字
        rp = pt(A, A / 2, th / 2, k)
        xr = P.R if not land else P.L + left_w + 60 + (P.CW - left_w - 60) * .1
        tx = max(rp[0] + 44, P.L + left_w + (36 if not land else 70))
        ty = rp[1]
        g += P.circle(rp[0], rp[1], 3.4, st)
        g += f'<path d="M{n(rp[0])} {n(rp[1])}L{n(tx - 8)} {n(ty)}" stroke="{st}" stroke-width="1.1"/>'
        room = P.R - tx
        tsz = fit(L["title"], 21, room, 15)
        g += P.text(tx, ty - 2, L["title"], tsz, "title", s["accent"] if L.get("highlight") else s["ink"], weight=s["title_weight"] if s["title_weight"] < 900 else 800)
        if L.get("sub"):
            sl = wrap(L["sub"], 15, room, 2)
            g += P.lines(tx, ty + 20, sl, 15, 19, role="body", fill=s["muted"], extra=' font-style="italic"' if s.get("label") == "italic" else "")
        drop = poly_d([(0, -46), (0, 0)])
        out += _g(g, motion(drop, [(0, 0), (t_drop[j], 0), (t_drop[j] + .45, 1)], T),
                  anim("opacity", show_from(t_drop[j], T, .3), T))
    # 包裹：从顶层上方落到底层
    pk = s["accent"]
    cube = (f'<path d="M0 -14L12 -7L0 0L-12 -7Z" fill="{pk}" stroke="{s["ink"]}" stroke-width="1.3"/>'
            f'<path d="M-12 -7L0 0V13L-12 6Z" fill="{shade(pk, s["ink"], .2)}" stroke="{s["ink"]}" stroke-width="1.3"/>'
            f'<path d="M12 -7L0 0V13L12 6Z" fill="{shade(pk, s["ink"], .38)}" stroke="{s["ink"]}" stroke-width="1.3"/>')
    pts = [(top_c[0], top_c[1] - 70)] + [pt(A / 2, A / 2, -8, k) for k in range(m)]
    legs = [(t_pk, 0)]
    seg = 1 / m
    for k in range(m):
        legs.append((t_pk + .5 * (k + 1), seg * (k + 1)))
    out += _g(cube, motion(poly_d(pts), legs, T),
              anim("opacity", [(0, 0), (t_pk, 0), (t_pk + .1, 1), (t_end_pk - .3, 1), (t_end_pk, 0)], T), base_opacity=0)
    # 每层被穿过时顶面闪一下
    for k in range(m):
        tf = t_pk + .5 * (k + 1)
        topf = [pt(0, 0, 0, k), pt(A, 0, 0, k), pt(A, A, 0, k), pt(0, A, 0, k)]
        out += _g(f'<path d="{poly_d(topf, True)}" fill="{s["accent"]}" fill-opacity=".22" stroke="{s["accent"]}" stroke-width="3"/>',
                  anim("opacity", window(tf - .15, tf + .2, T, .12), T), base_opacity=0)
    # 顶层小人
    if sp.get("walker", True):
        a, b = pt(A * .2, A * .78, 0, 0), pt(A * .78, A * .78, 0, 0)
        out += walker(P, [a, b, a], T, t_drop[-1] + .5)
    if sp.get("caption"):
        out += _note(P, top_c[0] + 18, top_c[1] - 58, 1, sp["caption"], P.R - top_c[0] - 30)
    return out, T


def walker(P, pts, T, t0=0, color=None):
    """几笔画成的小人，沿 pts 来回走；腿用 d 动画交替摆动。"""
    s = P.s
    c = color or s["ink"]
    leg_a = "M0 -16L-5 0M0 -16L5 0"
    leg_b = "M0 -16L4 0M0 -16L-3 0"
    body = (f'<path d="{leg_a}" stroke="{c}" stroke-width="2" stroke-linecap="round" fill="none">'
            f'<animate attributeName="d" values="{leg_a};{leg_b};{leg_a}" dur=".6s" repeatCount="indefinite"/></path>'
            f'<path d="M0 -16V-32M0 -28L-6 -20M0 -28L6 -21" stroke="{c}" stroke-width="2" stroke-linecap="round" fill="none"/>'
            + P.circle(0, -38, 5.5, s.get("tones", [s["panel"]])[0] if not P.dark else s["panel"], c, 1.8)
            + f'<path d="M-6 -40H6" stroke="{s["accent"]}" stroke-width="2.4" stroke-linecap="round"/>')
    legs = [(0, 0), (t0, 0), (t0 + (T - t0) * .5, .5), (T, 1)]
    x0, y0 = pts[0]
    rel = [(x - x0, y - y0) for x, y in pts]
    inner = _g(body, motion(poly_d(rel), legs, T))
    return _g(f'<g transform="translate({n(x0)} {n(y0)})">{inner}</g>', anim("opacity", show_from(t0, T, .3), T))


# ---------- 3. 坡度图 ----------

def slope(P, sp, top, bot):
    """两根竖轴，左边是之前、右边是之后，每个条目一根线。highlight 里的条目用强调色加粗。"""
    s = P.s
    items = sp["items"]
    hl = set(sp.get("highlight") or [])
    vals = [v for it in items for v in (it["a"], it["b"])]
    lo, hi = sp.get("min", min(vals)), sp.get("max", max(vals))
    span = (hi - lo) or 1
    unit = sp.get("unit", "")
    lab_w = max(text_w(it["name"], 18) for it in items) + 70
    x1 = P.L + min(lab_w, P.CW * .36)
    x2 = P.R - min(lab_w, P.CW * .36)
    y0, y1 = top + 70, bot - 30

    def Y(v):
        return y1 - (v - lo) / span * (y1 - y0)

    def spread(ys, gap=26):
        idx = sorted(range(len(ys)), key=lambda i: ys[i])
        out = list(ys)
        for a, b in zip(idx, idx[1:]):
            if out[b] - out[a] < gap:
                out[b] = out[a] + gap
        over = max(0, max(out) - (y1 + 10))
        return [v - over for v in out]
    la = spread([Y(it["a"]) for it in items])
    lb = spread([Y(it["b"]) for it in items])
    norm = [i for i, it in enumerate(items) if it["name"] not in hl]
    hot = [i for i, it in enumerate(items) if it["name"] in hl]
    seq = norm + hot
    tt = {}
    t = .6
    for i in seq:
        tt[i] = t
        t += .35 if items[i]["name"] not in hl else .9
    T = t + .8 + HOLD
    P.T = T
    out = ""
    for x, lab in ((x1, sp.get("left", "之前")), (x2, sp.get("right", "之后"))):
        out += f'<path d="M{n(x)} {n(y0 - 16)}V{n(y1 + 16)}" stroke="{s["ink"]}" stroke-width="2"/>'
        out += P.text(x, y0 - 34, lab, 22, "title", s["ink"], "middle", 800)
    cl = pal(P)
    for i in seq:
        it = items[i]
        h = it["name"] in hl
        up = it["b"] >= it["a"]
        c = it.get("color") or ((s["good"] if up else s["bad"]) if h and sp.get("updown") else s["accent"] if h else s["muted"])
        sw = 4.5 if h else 2
        a, b = (x1, Y(it["a"])), (x2, Y(it["b"]))
        t0 = tt[i]
        out += _g(P.circle(a[0], a[1], 6 if h else 4.5, c), anim("opacity", show_from(t0, T, .2), T))
        out += _drawn(P, [a, b], c, sw, t0 + .1, t0 + (.75 if h else .35), T)
        g = P.circle(b[0], b[1], 6 if h else 4.5, c)
        size = 18 if h else 16
        wt = 800 if h else 500
        tc = c if h else s["ink"]
        g2 = P.text(x1 - 14, la[i] + 6, f'{it["name"]}  {_num(it["a"])}{unit}', size, "body", tc, "end", wt)
        g += P.text(x2 + 14, lb[i] + 6, f'{_num(it["b"])}{unit}  {it["name"]}', size, "body", tc, "start", wt)
        out += _g(g2, anim("opacity", show_from(t0, T, .2), T))
        out += _g(g, anim("opacity", show_from(t0 + (.75 if h else .35), T, .2), T))
        if h and it.get("note"):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            out += _g(P.label_chip(mx, my - 12, it["note"], color=c), anim("opacity", show_from(t0 + .8, T, .2), T))
    return out, T


# ---------- 4. 气泡图 ----------

def bubble(P, sp, top, bot):
    """横纵两个指标加气泡大小三个维度。highlight 的气泡带一圈涟漪。"""
    s = P.s
    items = sp["items"]
    xa, ya = sp.get("x", {}), sp.get("y", {})
    xs = [it["x"] for it in items]
    ys = [it["y"] for it in items]
    zs = [it.get("size", 1) for it in items]
    xlo, xhi = xa.get("min", min(xs)), xa.get("max", max(xs))
    ylo, yhi = ya.get("min", min(ys)), ya.get("max", max(ys))
    groups = []
    for it in items:
        g = it.get("group")
        if g and g not in groups:
            groups.append(g)
    leg_h = 46 if groups else 0
    gx0, gx1 = P.L + 46, P.R - 14
    gy0, gy1 = top + 44, bot - 56 - leg_h
    rmax = min(62, (gx1 - gx0) / 9)
    zmax = max(zs) or 1

    def X(v):
        return gx0 + (v - xlo) / ((xhi - xlo) or 1) * (gx1 - gx0)

    def Y(v):
        return gy1 - (v - ylo) / ((yhi - ylo) or 1) * (gy1 - gy0)
    hl = set(sp.get("highlight") or [])
    order = sorted(range(len(items)), key=lambda i: -zs[i])
    ts = {i: .6 + k * .32 for k, i in enumerate(order)}
    t_last = max(ts.values()) + .8
    T = t_last + 1.2 + HOLD
    P.T = T
    out = ""
    for q in range(5):
        yy = gy0 + (gy1 - gy0) * q / 4
        xx = gx0 + (gx1 - gx0) * q / 4
        out += f'<path d="M{n(gx0)} {n(yy)}H{n(gx1)}M{n(xx)} {n(gy0)}V{n(gy1)}" stroke="{s["rule"]}" stroke-width="1" opacity=".8"/>'
        if q:
            out += P.text(xx, gy1 + 22, _num(round(xlo + (xhi - xlo) * q / 4, 1)), 14, "mono", s["muted"], "middle", 600)
        if q < 4:
            out += P.text(gx0 - 8, yy + 5, _num(round(yhi - (yhi - ylo) * q / 4, 1)), 14, "mono", s["muted"], "end", 600)
    out += f'<path d="M{n(gx0)} {n(gy0 - 10)}V{n(gy1)}H{n(gx1 + 10)}" fill="none" stroke="{s["ink"]}" stroke-width="2"/>'
    out += P.text(gx1, gy1 + 46, xa.get("label", "") + " →", 17, "body", s["muted"], "end", 600)
    out += P.text(gx0 - 8, gy0 - 22, "↑ " + ya.get("label", ""), 17, "body", s["muted"], "start", 600)
    for v, lab in ((xlo, xa.get("lo_label")), (xhi, xa.get("hi_label"))):
        if lab:
            out += P.text(X(v), gy1 + 34, lab, 15, "mono", s["muted"], "middle" if v == xlo else "end", 700)
    cl = [c for c in pal(P) if c != s["ink"]] or pal(P)
    if hl and len(cl) > 2:
        cl = cl[1:] + cl[:1]
    for i in order:
        it = items[i]
        r = max(10, rmax * math.sqrt(zs[i] / zmax))
        cx, cy = X(it["x"]), Y(it["y"])
        gi = groups.index(it["group"]) if it.get("group") in groups else i
        c = it.get("color") or (s["accent"] if it["name"] in hl else cl[gi % len(cl)])
        t0 = ts[i]
        circ = (f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{c}" fill-opacity="{.85 if it["name"] in hl else .5}" stroke="{c if not P.rough else s["ink"]}" stroke-width="2">'
                + anim("r", [(0, 0), (t0, 0), (t0 + .45, r * 1.1), (t0 + .6, r), (T - .5, r), (T - .15, 0)], T) + "</circle>")
        out += circ
        lab = it["name"]
        size = 16 if r < 30 else 18
        inside = text_w(lab, size) < r * 1.7
        ly = cy + 6 if inside else cy - r - 8
        tc = P.on(c) if inside and it["name"] in hl else s["ink"]
        out += _g(P.text(cx, ly, lab, size, "body", tc, "middle", 700), anim("opacity", show_from(t0 + .4, T, .2), T))
        if it["name"] in hl:
            ring = (f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="none" stroke="{c}" stroke-width="2">'
                    f'<animate attributeName="r" values="{n(r)};{n(r + 26)}" dur="1.6s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values=".9;0" dur="1.6s" repeatCount="indefinite"/></circle>')
            out += _g(ring, anim("opacity", show_from(t_last, T, .3), T), base_opacity=0)
            if it.get("note"):
                room = {1: gx1 - cx - r, -1: cx - r - gx0}
                for j, o in enumerate(items):
                    if j == i:
                        continue
                    ox_, oy_ = X(o["x"]), Y(o["y"])
                    orr = max(10, rmax * math.sqrt(zs[j] / zmax))
                    if abs(oy_ - cy) < orr + 34:
                        sd = 1 if ox_ > cx else -1
                        room[sd] = min(room[sd], abs(ox_ - cx) - r - orr - 16)
                side = 1 if room[1] >= room[-1] else -1
                out += _g(_note(P, cx + side * (r + 4), cy, side, it["note"], max(90, room[side])),
                          anim("opacity", show_from(t_last, T, .3), T))
    if groups:
        out += _legend(P, P.L + 20, bot - 8, groups, [cl[k % len(cl)] for k in range(len(groups))], P.CW - 40, 17, min(4, len(groups)))
    return out, T


EXTRA = dict(statechart=statechart, iso=iso, slope=slope, bubble=bubble)
