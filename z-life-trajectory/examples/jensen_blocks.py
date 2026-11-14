"""黄仁勋示例专用的插画块：演示怎么给某个人物写定制插画。

在 spec 里写 "plugins": ["jensen_blocks.py"]，然后就能用 {"type": "pingpong"} 这类块。
每个块函数签名都是 fn(c, top, b) -> 高度：c 是画笔（见 lifeline.Ctx），top 是这块的顶边，b 是 JSON 里的这一项。
坐标系：整张图宽 750，c.TX=118 是正文左边，c.RX=702 是正文右边，c.SPINE=78 是左侧主线。
"""
import math


def apple2(c, top, b):
    """Apple II：绿屏里跑一条贪吃蛇，右侧是文字。"""
    T, AY = c.T, top
    INK = T['INK']
    c.card(c.TX, AY, c.RX - c.TX, 262)
    c.add(f'<rect x="138" y="{AY + 22}" width="240" height="172" rx="12" fill="#E9DFC9" stroke="{INK}" stroke-width="3"/>')
    c.add(f'<rect x="154" y="{AY + 36}" width="208" height="140" rx="6" fill="#0F2418"/>')
    c.add(c.text(162, AY + 53, 'SCORE 07', 13, '#7CE38B', family=c.MONO, ls=1))
    pts = [(170, AY + 70), (346, AY + 70), (346, AY + 100), (194, AY + 100), (194, AY + 130), (346, AY + 130),
           (346, AY + 160), (170, AY + 160), (170, AY + 70)]
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    d = 'M' + ' L'.join(f'{x},{y}' for (x, y) in pts)
    c.add(f'<path d="{d}" fill="none" stroke="#1D3A27" stroke-width="2" stroke-dasharray="2 6"/>')
    c.add(f'<rect x="282" y="{AY + 126}" width="8" height="8" fill="#F2C14E"><animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite"/></rect>')
    c.add(f'<path d="{d}" fill="none" stroke="#7CE38B" stroke-width="9" stroke-linecap="square" stroke-linejoin="miter" stroke-dasharray="64 {L - 64:.0f}">'
          f'<animate attributeName="stroke-dashoffset" values="0;-{L:.0f}" dur="7s" repeatCount="indefinite"/></path>')
    c.add(f'<rect x="132" y="{AY + 204}" width="252" height="40" rx="8" fill="#E9DFC9" stroke="{INK}" stroke-width="3"/>')
    for r in range(2):
        for k in range(11):
            c.add(f'<rect x="{146 + k * 21}" y="{AY + 212 + r * 13}" width="15" height="8" rx="2" fill="#CDBF9F"/>')
    c.stub(AY + 131)
    c.add(c.text(410, AY + 66, b.get('year', ''), 23, c.acc, 800, ls=1))
    c.add(c.text(410, AY + 106, b.get('title', ''), 25, c.fg, 800))
    for i, s in enumerate(b.get('lines', [])[:2]):
        c.add(c.text(410, AY + 150 + 32 * i, s, 19, c.muted))
    if b.get('note'):
        c.add(c.text(410, AY + 226, b['note'], 17, c.faint, 600))
    return 262


def pingpong(c, top, b):
    """乒乓球台：球在两名选手之间来回。"""
    T, PY = c.T, top
    INK = T['INK']
    c.card(c.TX, PY, c.RX - c.TX, 146)
    c.add(f'<line x1="236" y1="{PY + 112}" x2="584" y2="{PY + 112}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>')
    c.add(f'<line x1="410" y1="{PY + 112}" x2="410" y2="{PY + 88}" stroke="{INK}" stroke-width="3"/>')
    for x in (262, 558):
        c.add(f'<line x1="{x}" y1="{PY + 112}" x2="{x}" y2="{PY + 136}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    c.add(f'<ellipse cx="196" cy="{PY + 62}" rx="12" ry="16" fill="{T["ACCENT"]}"/><line x1="194" y1="{PY + 76}" x2="189" y2="{PY + 94}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    c.add(f'<ellipse cx="624" cy="{PY + 62}" rx="12" ry="16" fill="{T["SECOND"]}"/><line x1="626" y1="{PY + 76}" x2="631" y2="{PY + 94}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    ball = (f'M212,{PY + 60} Q356,{PY - 2} 500,{PY + 106} Q560,{PY + 40} 608,{PY + 60} '
            f'Q464,{PY - 2} 320,{PY + 106} Q260,{PY + 40} 212,{PY + 60}')
    c.add(f'<path d="{ball}" fill="none" stroke="{T["RULE2"]}" stroke-width="1.5" stroke-dasharray="2 7"/>')
    c.add(f'<circle r="7" fill="#E9A23B" stroke="{INK}" stroke-width="1.5"><animateMotion path="{ball}" dur="2.2s" repeatCount="indefinite"/></circle>')
    return 146


def mesh_compare(c, top, b):
    """四边形网格 vs 三角形网格，逐格点亮，左错右对。"""
    T, QY = c.T, top
    INK = T['INK']
    c.card(c.TX, QY, c.RX - c.TX, 230)
    cs = 42
    for (gx, tri, colr) in ((178, False, T['ACCENT_L']), (468, True, T['SECOND'])):
        gy = QY + 30
        P = [[(gx + k * cs, gy + r * cs) for k in range(5)] for r in range(4)]
        c.add(f'<rect x="{gx}" y="{gy}" width="{4 * cs}" height="{3 * cs}" fill="#F3ECDF"/>')
        groups = {}
        for r in range(3):
            for k in range(4):
                a, bb, cc, d = P[r][k], P[r][k + 1], P[r + 1][k + 1], P[r + 1][k]
                if tri:
                    for j, pg in enumerate(((a, bb, cc), (a, cc, d))):
                        groups.setdefault(k + r + j, []).append(pg)
                else:
                    groups.setdefault(k + r, []).append((a, bb, cc, d))
        dur = 0.32 * (max(groups) + 1)
        for gk, polys in sorted(groups.items()):
            pts = ''.join(f'<polygon points="{" ".join(f"{x},{y}" for (x, y) in pg)}" fill="{colr}"/>' for pg in polys)
            c.add(f'<g opacity="0"><animate attributeName="opacity" values="0;0.75;0" dur="{dur:.2f}s" begin="{gk * 0.32:.2f}s" repeatCount="indefinite"/>{pts}</g>')
        gl = ''.join(f'M{gx},{gy + r * cs}H{gx + 4 * cs}' for r in range(4)) + ''.join(f'M{gx + k * cs},{gy}V{gy + 3 * cs}' for k in range(5))
        if tri:
            gl += ''.join(f'M{gx + k * cs},{gy + r * cs}L{gx + (k + 1) * cs},{gy + (r + 1) * cs}' for r in range(3) for k in range(4))
        c.add(f'<path d="{gl}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')
    bx, by = 178 + 4 * cs, QY + 30
    c.add(f'<circle cx="{bx}" cy="{by}" r="15" fill="{T["ACCENT"]}"/><path d="M{bx - 6},{by - 6} L{bx + 6},{by + 6} M{bx + 6},{by - 6} L{bx - 6},{by + 6}" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round"/>')
    cx, cy = 468 + 4 * cs, QY + 30
    c.add(f'<circle cx="{cx}" cy="{cy}" r="15" fill="{T["SECOND"]}"/><path d="M{cx - 7},{cy} L{cx - 2},{cy + 5} L{cx + 7},{cy - 5}" fill="none" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
    c.add(c.text(407, QY + 103, 'VS', 18, T['GRAY3'], 700, anchor='middle', family=c.MONO))
    L, R = b.get('left', {}), b.get('right', {})
    c.add(c.text(262, QY + 192, L.get('title', ''), 18, c.fg, 800, anchor='middle'))
    c.add(c.text(262, QY + 216, L.get('sub', ''), 15, c.muted, anchor='middle'))
    c.add(c.text(552, QY + 192, R.get('title', ''), 18, c.fg, 800, anchor='middle'))
    c.add(c.text(552, QY + 216, R.get('sub', ''), 15, c.muted, anchor='middle'))
    return 230


def cpu_gpu(c, top, b):
    """左边 4 个大核依次亮，右边 72 个小核成列波浪闪。"""
    T = c.T
    CY = top + 12
    for px in range(176, 320, 16):
        c.add(f'<line x1="{px}" y1="{CY - 12}" x2="{px}" y2="{CY}" stroke="{T["GRAY3"]}" stroke-width="3"/><line x1="{px}" y1="{CY + 160}" x2="{px}" y2="{CY + 172}" stroke="{T["GRAY3"]}" stroke-width="3"/>')
    for px in range(416, 676, 16):
        c.add(f'<line x1="{px}" y1="{CY - 12}" x2="{px}" y2="{CY}" stroke="{T["GRAY3"]}" stroke-width="3"/><line x1="{px}" y1="{CY + 160}" x2="{px}" y2="{CY + 172}" stroke="{T["GRAY3"]}" stroke-width="3"/>')
    c.add(f'<rect x="160" y="{CY}" width="160" height="160" rx="12" fill="{T["INK"]}"/>')
    for k, (qx, qy) in enumerate(((172, CY + 12), (246, CY + 12), (246, CY + 86), (172, CY + 86))):
        c.add(f'<rect x="{qx}" y="{qy}" width="62" height="62" rx="6" fill="#3A4252"/>')
        c.add(f'<rect x="{qx}" y="{qy}" width="62" height="62" rx="6" fill="{T["ACCENT_L"]}" opacity="0">'
              f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;0.06;0.25;1" dur="2.4s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/></rect>')
    c.add(f'<rect x="400" y="{CY}" width="290" height="160" rx="12" fill="{T["INK"]}"/>')
    cols, rows, cell, gap = 12, 6, 18, 4
    gx0 = 400 + (290 - (cols * (cell + gap) - gap)) / 2
    gy0 = CY + (160 - (rows * (cell + gap) - gap)) / 2
    for k in range(cols):
        rects = ''.join(f'<rect x="{gx0 + k * (cell + gap):.1f}" y="{gy0 + r * (cell + gap):.1f}" width="{cell}" height="{cell}" rx="3" fill="{T["ACCENT_L"]}"/>' for r in range(rows))
        c.add(f'<g opacity="0.22"><animate attributeName="opacity" values="0.22;1;0.22" dur="1.8s" begin="{k * 0.09:.2f}s" repeatCount="indefinite"/>{rects}</g>')
    L, R = b.get('left', {}), b.get('right', {})
    c.add(c.text(240, CY + 214, L.get('title', ''), 19, c.fg, 800, anchor='middle'))
    c.add(c.text(240, CY + 242, L.get('sub', ''), 17, c.muted, anchor='middle'))
    c.add(c.text(545, CY + 214, R.get('title', ''), 19, c.fg, 800, anchor='middle'))
    c.add(c.text(545, CY + 242, R.get('sub', ''), 17, c.muted, anchor='middle'))
    return 262


def cuda_fanout(c, top, b):
    """一行代码扇出成上百万个线程。"""
    T = c.T
    KY = top - 7
    TX = c.TX
    c.add(f'<rect x="{TX}" y="{KY + 30}" width="270" height="118" rx="12" fill="{T["INK"]}"/>')
    c.add(f'<circle cx="{TX + 20}" cy="{KY + 48}" r="4" fill="#E06C5A"/><circle cx="{TX + 34}" cy="{KY + 48}" r="4" fill="#E9A23B"/><circle cx="{TX + 48}" cy="{KY + 48}" r="4" fill="#5FB37A"/>')
    c.add(c.text(TX + 18, KY + 84, b.get('code1', '__global__ void add(...)'), 14, '#8B93A6', family=c.MONO))
    c.add(c.text(TX + 18, KY + 114, b.get('code2', 'add<<<4096, 256>>>(...);'), 14, T['DACCENT'], 700, family=c.MONO))
    c.add(f'<rect x="{TX + 228}" y="{KY + 101}" width="9" height="16" fill="{T["DACCENT"]}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>')
    c.add(c.text(TX + 135, KY + 176, b.get('caption', '一次调用'), 17, c.muted, 600, anchor='middle'))
    ox, oy = 396, KY + 89
    targets = [(548, KY + 12 + i * 14.5) for i in range(12)]
    fan = ' '.join(f'M{ox},{oy} L{tx},{ty:.1f}' for (tx, ty) in targets)
    c.add(f'<path d="{fan}" fill="none" stroke="{T["RULE2"]}" stroke-width="1.5"/>')
    c.add(f'<path d="{fan}" fill="none" stroke="{T["ACCENT_L"]}" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="8 160">'
          f'<animate attributeName="stroke-dashoffset" values="0;-168" dur="1.4s" repeatCount="indefinite"/></path>')
    c.add(f'<circle cx="{ox}" cy="{oy}" r="6" fill="{T["INK"]}"/>')
    for i, (tx, ty) in enumerate(targets):
        c.add(f'<rect x="{tx + 2}" y="{ty - 5:.1f}" width="10" height="10" rx="2" fill="{T["INK"]}"/>')
        c.add(f'<rect x="{tx + 2}" y="{ty - 5:.1f}" width="10" height="10" rx="2" fill="{T["ACCENT_L"]}" opacity="0">'
              f'<animate attributeName="opacity" values="0;1;0" dur="1.4s" begin="{0.6 + i * 0.03:.2f}s" repeatCount="indefinite"/></rect>')
    c.add(c.text(586, KY + 92, b.get('value', '105 万'), 34, c.acc, 900))
    c.add(c.text(586, KY + 122, b.get('unit', '个线程同时跑'), 17, c.muted, 600))
    c.add(c.text(586, KY + 148, b.get('formula', '4096 × 256'), 13, c.faint, family=c.MONO))
    return 176


def alexnet(c, top, b):
    """两块显卡风扇转 → 神经网络信号流动 → 错误率对比条。"""
    T = c.T
    VY = top - 3
    TX = c.TX
    for k in range(2):
        gy = VY + 18 + k * 66
        c.add(f'<rect x="{TX}" y="{gy}" width="146" height="54" rx="8" fill="{T["INK"]}"/>')
        c.add(f'<rect x="{TX}" y="{gy + 46}" width="146" height="8" rx="2" fill="#3A4252"/>')
        for fx in (TX + 40, TX + 106):
            fy = gy + 23
            c.add(f'<circle cx="{fx}" cy="{fy}" r="18" fill="#2A3140" stroke="#4A5265" stroke-width="2"/>')
            blades = ''.join(f'<path d="M0,0 C4,-6 4,-13 0,-15 C-3,-11 -4,-5 0,0 Z" fill="#8A93A6" transform="rotate({a})"/>' for a in (0, 90, 180, 270))
            c.add(f'<g transform="translate({fx} {fy})"><g>{blades}<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{0.9 + 0.2 * k:.1f}s" repeatCount="indefinite"/></g></g>')
            c.add(f'<circle cx="{fx}" cy="{fy}" r="3.5" fill="{T["ACCENT_L"]}"/>')
    c.add(c.text(TX + 73, VY + 172, b.get('gpu', 'GTX 580 × 2'), 17, c.fg, 800, anchor='middle'))
    arrow = 'fill="none" stroke="{}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'.format(T['GRAY3'])
    c.add(f'<path d="M274,{VY + 84} H300 M292,{VY + 77} L301,{VY + 84} L292,{VY + 91}" {arrow}/>')
    L1 = [(328, VY + 30 + 36 * i) for i in range(4)]
    L2 = [(404, VY + 12 + 36 * i) for i in range(5)]
    L3 = [(480, VY + 48 + 36 * i) for i in range(3)]
    edges = ' '.join(f'M{a[0]},{a[1]} L{q[0]},{q[1]}' for a in L1 for q in L2) + ' ' + ' '.join(f'M{a[0]},{a[1]} L{q[0]},{q[1]}' for a in L2 for q in L3)
    c.add(f'<path d="{edges}" fill="none" stroke="{T["RULE2"]}" stroke-width="1.5"/>')
    c.add(f'<path d="{edges}" fill="none" stroke="{T["ACCENT_L"]}" stroke-width="2.2" stroke-dasharray="7 70" stroke-linecap="round">'
          f'<animate attributeName="stroke-dashoffset" values="0;-77" dur="1.6s" repeatCount="indefinite"/></path>')
    for (x, y) in L1 + L2 + L3:
        c.add(f'<circle cx="{x}" cy="{y}" r="9" fill="{T["PAPER"]}" stroke="{T["INK"]}" stroke-width="2.5"/>')
    c.add(f'<circle cx="{L3[1][0]}" cy="{L3[1][1]}" r="9" fill="{T["ACCENT"]}"/>')
    c.add(c.pulse(L3[1][0], L3[1][1], T['ACCENT'], 9, 22, 1.6))
    c.add(c.text(404, VY + 214, '神经网络', 17, c.muted, anchor='middle'))
    c.add(f'<path d="M506,{VY + 84} H530 M522,{VY + 77} L531,{VY + 84} L522,{VY + 91}" {arrow}/>')
    BX, BW = 546, 86
    a, z = b.get('ours', 15.3), b.get('runner_up', 26.2)
    c.add(c.text(BX, VY + 30, 'top-5 错误率', 17, c.muted, 600))
    c.add(c.text(BX, VY + 68, 'AlexNet', 18, c.fg, 800))
    c.add(f'<rect x="{BX}" y="{VY + 78}" width="{BW * a / z:.1f}" height="24" rx="4" fill="{T["ACCENT"]}"/>')
    c.add(c.text(BX + BW * a / z + 9, VY + 97, f'{a}%', 18, c.acc, 800))
    c.add(c.text(BX, VY + 142, '第二名', 18, c.muted, 600))
    c.add(f'<rect x="{BX}" y="{VY + 152}" width="{BW}" height="24" rx="4" fill="{T["GRAY3"]}"/>')
    c.add(c.text(BX + BW + 9, VY + 171, f'{z}%', 18, c.muted, 800))
    return 218


BLOCKS = {
    'apple2': apple2, 'pingpong': pingpong, 'mesh_compare': mesh_compare,
    'cpu_gpu': cpu_gpu, 'cuda_fanout': cuda_fanout, 'alexnet': alexnet,
}
