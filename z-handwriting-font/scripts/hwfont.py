"""hwfont: turn your own handwriting into an OpenType font.

Two ways in:
  grid    print a template, write one character per box, photograph the pages
  letter  you only have an old manuscript (a letter, a notebook page): cut what is there

Commands
  template  --chars FILE|--count N [--extra latin,digits,punct] --out DIR
  extract   --template DIR --photos P1 P2 ... --out WORK        (grid route)
  segment   --photo IMG --text TRANSCRIPT --out WORK            (letter route, step 1)
  cut       --work WORK                                         (letter route, step 2, after checking boxes.json)
  review    --work WORK                                         contact sheet of every glyph
  build     --work WORK --family NAME [--keep-position] [--no-weight]
  specimen  --font OTF --text "..." --out PNG
  check     --font OTF

Everything is drawn from the images you give it. No outline, code or data from an existing font is used;
system fonts are only used to print the small reference labels on the paper template.
"""
import argparse, glob, json, os, re, subprocess, sys, tempfile
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps
Image.init()   # register every plugin up front (PDF output needs the JPEG writer)

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'assets')

# ---------------------------------------------------------------- character sets
LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'
PUNCT = '，。、；：？！“”‘’（）《》—…·'
ASCII_PUNCT = '.,;:?!\'"()-/&@#%+='

def load_chars(path):
    s = ''.join(l for l in open(path, encoding='utf8') if not l.startswith('#'))
    seen, out = set(), []
    for c in s:
        if c.isspace() or c in seen: continue
        seen.add(c); out.append(c)
    return out

def is_ascii(c): return ord(c) < 0x80

# ---------------------------------------------------------------- template geometry (A4 at 200 dpi)
W, H = 1654, 2339
FID, FM = 70, 60                          # fiducial square size, margin
COLS, ROWS = 8, 9
GX0, GY0, GX1 = 100, 210, W - 100
CW = (GX1 - GX0) // COLS                  # 181
LABEL = 34; PAD = 10
SQ = CW - 2 * PAD                         # writing square, 161 px = 20.4 mm
CH = LABEL + SQ + 8
PER_PAGE = COLS * ROWS
BITS = 10; BIT, BITGAP, BITX, BITY = 28, 12, 330, H - FM - FID // 2 - 14

def fid_centers():
    a, b = FM + FID / 2, None
    return np.float32([[FM + FID / 2, FM + FID / 2], [W - FM - FID / 2, FM + FID / 2],
                       [FM + FID / 2, H - FM - FID / 2], [W - FM - FID / 2, H - FM - FID / 2]])

def cell_square(i):
    r, c = divmod(i, COLS)
    x = GX0 + c * CW + PAD; y = GY0 + r * CH + LABEL
    return x, y, x + SQ, y + SQ

def label_font(size):
    cands = [os.environ.get('HWFONT_LABEL_FONT', ''),
             '/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/PingFang.ttc',
             '/System/Library/Fonts/STHeiti Light.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf',
             '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc']
    for p in cands:
        if p and os.path.exists(p): return ImageFont.truetype(p, size)
    sys.exit('No CJK font found for the template labels. Set HWFONT_LABEL_FONT to any .ttf/.ttc that has Chinese.')

def cmd_template(a):
    if a.chars: chars = load_chars(a.chars)
    else: chars = load_chars(os.path.join(ASSETS, 'common-2997.txt'))[:a.count]
    extra = {'latin': LATIN, 'digits': DIGITS, 'punct': PUNCT, 'ascii-punct': ASCII_PUNCT}
    for k in (a.extra.split(',') if a.extra else []):
        chars += [c for c in extra[k] if c not in chars]
    os.makedirs(a.out, exist_ok=True)
    f_lab, f_head = label_font(24), label_font(30)
    pages = [chars[i:i + PER_PAGE] for i in range(0, len(chars), PER_PAGE)]
    imgs = []
    for p, pc in enumerate(pages):
        im = Image.new('L', (W, H), 255); d = ImageDraw.Draw(im)
        for x, y in fid_centers(): d.rectangle([x - FID / 2, y - FID / 2, x + FID / 2, y + FID / 2], fill=0)
        for b in range(BITS):                          # page number as 10 black/white boxes
            x = BITX + b * (BIT + BITGAP)
            d.rectangle([x, BITY, x + BIT, BITY + BIT], fill=0 if (p >> b) & 1 else 255, outline=0, width=2)
        d.text((GX0 + 40, 110), f'{a.title}   第 {p + 1} / {len(pages)} 页   用黑色签字笔，一格一字，别写出框', font=f_head, fill=90)
        for i, c in enumerate(pc):
            x0, y0, x1, y1 = cell_square(i)
            d.text((x0, y0 - LABEL + 4), c, font=f_lab, fill=120)
            d.rectangle([x0, y0, x1, y1], outline=200, width=2)
            if is_ascii(c):                            # baseline guide for Latin, digits and ASCII punctuation
                yb = y0 + int(SQ * .88)
                d.line([x0 + 4, yb, x1 - 4, yb], fill=215, width=2)
        imgs.append(im)
        im.save(os.path.join(a.out, f'page-{p + 1:02d}.png'))
    imgs[0].save(os.path.join(a.out, 'template.pdf'), save_all=True, append_images=imgs[1:], resolution=200)
    json.dump({'pages': [''.join(pc) for pc in pages], 'title': a.title}, open(os.path.join(a.out, 'template.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'{len(chars)} characters on {len(pages)} pages -> {a.out}/template.pdf (print at 100%, A4)')

# ---------------------------------------------------------------- shared image helpers
def read_gray(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert('L')
    return np.array(im)

def flatten(g, k):
    """Divide out uneven lighting: estimate the paper by closing the ink away, return ink darkness 0..1."""
    bg = cv2.morphologyEx(g, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    bg = cv2.GaussianBlur(bg, (0, 0), k / 3)
    return np.clip(1 - g.astype(np.float32) / np.maximum(bg.astype(np.float32), 1), 0, 1)

def tight(m):
    ys, xs = np.nonzero(m)
    if len(ys) == 0: return m[:0, :0], (0, 0, 0, 0)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)

def despeck(m, min_px):
    n, l, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, 4] >= min_px
    return keep[l]

def save_mask(m, path): Image.fromarray(np.where(m, 0, 255).astype(np.uint8)).save(path)
def load_mask(path): return np.array(Image.open(path).convert('L')) < 128
def gname(c): return 'U+%04X' % ord(c)

# ---------------------------------------------------------------- grid route
def find_fiducials(g):
    ink = flatten(g, max(31, (min(g.shape) // 25) | 1)) > .35
    cs, _ = cv2.findContours(ink.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lo = (min(g.shape) * .02) ** 2; cands = []
    for c in cs:
        A = cv2.contourArea(c)
        if A < lo: continue
        (cx, cy), (w, h), _ = cv2.minAreaRect(c)
        if not (.75 < w / max(h, 1) < 1.33): continue
        if A / (w * h) < .85: continue
        cands.append((cx, cy, A))
    if len(cands) < 4: return None
    P = np.array([(x, y) for x, y, _ in cands]); s = P.sum(1); d = P[:, 0] - P[:, 1]
    return np.float32([P[s.argmin()], P[d.argmax()], P[d.argmin()], P[s.argmax()]])   # TL TR BL BR

def cmd_extract(a):
    T = json.load(open(os.path.join(a.template, 'template.json'), encoding='utf8'))
    out = os.path.join(a.out, 'glyphs'); os.makedirs(out, exist_ok=True)
    meta = load_meta(a.out); S = 3                       # warp at 3x the template scale
    report = {'pages': {}, 'blank': [], 'touches_edge': []}
    for ph in a.photos:
        g = read_gray(ph); src = find_fiducials(g)
        if src is None: print(f'! {ph}: could not find the four black corner squares; retake the photo with all four visible'); continue
        M = cv2.getPerspectiveTransform(src, fid_centers() * S)
        wg = cv2.warpPerspective(g, M, (W * S, H * S), flags=cv2.INTER_CUBIC, borderValue=255)
        dark = flatten(wg, 61)
        p = 0
        for b in range(BITS):
            x = (BITX + b * (BIT + BITGAP) + BIT / 2) * S; y = (BITY + BIT / 2) * S; r = int(BIT * S * .25)
            if dark[int(y) - r:int(y) + r, int(x) - r:int(x) + r].mean() > .3: p |= 1 << b
        if p >= len(T['pages']): print(f'! {ph}: page code {p} is not in this template'); continue
        chars = T['pages'][p]; report['pages'][ph] = p + 1; n_ok = 0
        for i, c in enumerate(chars):
            x0, y0, x1, y1 = [v * S for v in cell_square(i)]; inset = 5 * S
            sq = dark[y0 + inset:y1 - inset, x0 + inset:x1 - inset]
            m = despeck(sq > a.threshold, max(6, int(sq.size * 4e-4)))
            if m.sum() < sq.size * .002: report['blank'].append(c); continue
            edge = m[:2].any() or m[-2:].any() or m[:, :2].any() or m[:, -2:].any()
            if edge: report['touches_edge'].append(c)
            t, (bx0, by0, bx1, by1) = tight(m)
            save_mask(t, os.path.join(out, gname(c) + '.png'))
            side = sq.shape[0] + 2 * inset
            meta[c] = {'file': gname(c) + '.png', 'source': 'grid',
                       'box': [(bx0 + inset) / side, (by0 + inset) / side, (bx1 + inset) / side, (by1 + inset) / side], 'px_per_em': side}
            n_ok += 1
        print(f'{ph}: page {p + 1}, {n_ok}/{len(chars)} boxes written')
    json.dump(meta, open(os.path.join(a.out, 'glyphs.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump(report, open(os.path.join(a.out, 'extract_report.json'), 'w'), ensure_ascii=False, indent=1)
    print(f"blank {len(report['blank'])}, touching the box edge {len(report['touches_edge'])} (check these): {''.join(report['touches_edge'][:40])}")

def load_meta(work):
    p = os.path.join(work, 'glyphs.json')
    return json.load(open(p, encoding='utf8')) if os.path.exists(p) else {}

# ---------------------------------------------------------------- letter route
def cmd_segment(a):
    """Propose one box per written character, in reading order (horizontal lines, top to bottom)."""
    g = read_gray(a.photo)
    text = [c for c in open(a.text, encoding='utf8').read() if not c.isspace()]
    dark = flatten(g, max(31, (min(g.shape) // 20) | 1)); ink = despeck(dark > a.threshold, 4)
    rows = ink.sum(1) > 0
    # line height from the ink rows: group rows into runs, merge runs closer than a few px
    runs, y = [], 0
    while y < len(rows):
        if rows[y]:
            s = y
            while y < len(rows) and rows[y]: y += 1
            runs.append([s, y])
        y += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < 4: merged[-1][1] = r[1]
        else: merged.append(r)
    big = [r for r in merged if r[1] - r[0] > 8]
    lh = float(np.median([r[1] - r[0] for r in big])) if big else 40
    lines = []
    for r in merged:
        if r[1] - r[0] < lh * .45 and lines and r[0] - lines[-1][1] < lh * .6: lines[-1][1] = r[1]   # dots/commas join the line above
        else: lines.append(list(r))
    boxes = []
    for y0, y1 in lines:
        boxes += split_line(ink, y0, y1, lh)
    os.makedirs(a.out, exist_ok=True)
    items = [{'box': b, 'char': text[i] if i < len(text) else '?'} for i, b in enumerate(boxes)]
    json.dump({'photo': os.path.abspath(a.photo), 'threshold': a.threshold, 'items': items},
              open(os.path.join(a.out, 'boxes.json'), 'w'), ensure_ascii=False, indent=0)
    draw_boxes(g, items, os.path.join(a.out, 'boxes.png'))
    print(f'{len(boxes)} boxes for {len(text)} transcript characters -> {a.out}/boxes.png')
    if len(boxes) != len(text):
        print('! counts differ: open boxes.png, then merge/split/delete entries in boxes.json until every box holds one character and its label is right')

def split_line(ink, y0, y1, lh):
    """One text line -> character boxes. Uses the character pitch (about the line height) to merge
    loose halves such as 女|子 and to cut touching characters at the emptiest column."""
    band = ink[y0:y1]; col = band.sum(0).astype(float); W = len(col)
    runs, x = [], 0
    while x < W:
        if col[x]:
            s0 = x
            while x < W and col[x]: x += 1
            runs.append([s0, x])
        x += 1
    if not runs: return []
    cl = [runs[0]]
    for r in runs[1:]:
        if r[0] - cl[-1][1] <= 2: cl[-1][1] = r[1]
        else: cl.append(r)
    def height(r):
        ys = np.nonzero(band[:, r[0]:r[1]].any(1))[0]; return (ys[-1] - ys[0] + 1) if len(ys) else 0
    widths = [r[1] - r[0] for r in cl if .6 * lh < r[1] - r[0] < 1.5 * lh]
    cw = float(np.median(widths)) if widths else lh
    small = lambda r: (r[1] - r[0]) < .45 * cw and height(r) < .45 * lh      # a comma, a dot
    out = []
    i = 0
    while i < len(cl):
        cur = list(cl[i]); i += 1
        if not small(cur):
            while i < len(cl) and not small(cl[i]) and cl[i][1] - cur[0] < 1.2 * cw and \
                    ((cur[1] - cur[0]) < .7 * cw or (cl[i][1] - cl[i][0]) < .55 * cw) and cl[i][0] - cur[1] < .3 * cw:
                cur[1] = cl[i][1]; i += 1
        w = cur[1] - cur[0]; n = int(round(w / cw)) if w > 1.4 * cw else 1
        cuts = [cur[0]]
        sm = np.convolve(col, np.ones(5) / 5, 'same')
        for k in range(1, n):
            c = cur[0] + k * w / n; lo, hi = int(c - .3 * cw), int(c + .3 * cw)
            cuts.append(lo + int(np.argmin(sm[lo:hi])))
        cuts.append(cur[1])
        for xa, xb in zip(cuts[:-1], cuts[1:]):
            ys = np.nonzero(band[:, xa:xb].any(1))[0]
            if len(ys): out.append([int(xa), int(y0 + ys[0]), int(xb), int(y0 + ys[-1] + 1)])
    return out

def draw_boxes(g, items, path):
    im = Image.fromarray(g).convert('RGB'); d = ImageDraw.Draw(im); f = label_font(max(12, im.width // 70))
    for i, it in enumerate(items):
        x0, y0, x1, y1 = it['box']; d.rectangle([x0, y0, x1, y1], outline=(220, 40, 40), width=2)
        d.text((x0, y1 + 1), f"{i}{it['char']}", font=f, fill=(30, 90, 220))
    im.save(path)

def cmd_cut(a):
    B = json.load(open(os.path.join(a.work, 'boxes.json'), encoding='utf8'))
    g = read_gray(B['photo']); dark = flatten(g, max(31, (min(g.shape) // 20) | 1))
    out = os.path.join(a.work, 'glyphs'); os.makedirs(out, exist_ok=True)
    meta = load_meta(a.work); count = {}
    for it in B['items']:
        c = it['char']
        if c in ('?', '') or it.get('skip'): continue
        x0, y0, x1, y1 = it['box']; p = 3
        X0, Y0 = max(0, x0 - p), max(0, y0 - p)
        m = despeck(dark[Y0:y1 + p, X0:x1 + p] > B['threshold'], 4)
        inside = np.zeros_like(m); inside[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
        n, l = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
        keep = np.zeros_like(m)
        for j in range(1, n):        # a neighbour's stroke poking in is dropped; a stroke crossing the cut is clipped
            s_ = l == j; fr = (s_ & inside).sum() / s_.sum()
            if fr >= .5: keep |= s_ & (inside if fr < .9 else True)
        t, _ = tight(keep)
        if t.size == 0: continue
        k = count.get(c, 0); count[c] = k + 1
        fn = gname(c) + ('' if k == 0 else f'.alt{k}') + '.png'
        save_mask(t, os.path.join(out, fn))
        meta.setdefault(c, {'file': gname(c) + '.png', 'source': 'letter', 'alts': []})
        if k: meta[c]['alts'].append(fn)
    json.dump(meta, open(os.path.join(a.work, 'glyphs.json'), 'w'), ensure_ascii=False, indent=0)
    print(f'{len(count)} distinct characters, {sum(count.values())} samples -> {out}')

# ---------------------------------------------------------------- review sheet
def cmd_review(a):
    meta = load_meta(a.work); items = sorted(meta.items(), key=lambda kv: kv[0])
    cols = 16; cell = 110; f = label_font(16)
    rows = (len(items) + cols - 1) // cols
    im = Image.new('L', (cols * cell, rows * (cell + 20)), 255); d = ImageDraw.Draw(im)
    for i, (c, m) in enumerate(items):
        r, k = divmod(i, cols); x, y = k * cell, r * (cell + 20)
        g = load_mask(os.path.join(a.work, 'glyphs', m['file']))
        s = (cell - 16) / max(g.shape); t = Image.fromarray(np.where(g, 0, 255).astype(np.uint8)).resize(
            (max(1, int(g.shape[1] * s)), max(1, int(g.shape[0] * s))), Image.LANCZOS)
        im.paste(t, (x + (cell - t.width) // 2, y + 20 + (cell - 16 - t.height) // 2))
        d.text((x + 3, y + 1), c + (' +%d' % len(m.get('alts', [])) if m.get('alts') else ''), font=f, fill=110)
    p = os.path.join(a.work, 'review.png'); im.save(p); print(f'{len(items)} glyphs -> {p}')

# ---------------------------------------------------------------- outlines
def smooth_up(m, target=520):
    """Upsample a small binary crop so potrace sees smooth edges (detail is interpolated, not recovered)."""
    f = max(1.0, target / max(m.shape))
    if f == 1.0: return m, 1.0
    a = cv2.resize(m.astype(np.float32), None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(a, (0, 0), f * .35) > .5, f

def stroke_width(m):
    d = cv2.distanceTransform(np.pad(m, 2).astype(np.uint8), cv2.DIST_L2, 5)
    r = d[(d == cv2.dilate(d, np.ones((3, 3)))) & (d > 1)]
    return 2 * float(np.median(r)) if len(r) else 0

def set_width(m, target, limit):
    w = stroke_width(m); r = min(limit, abs(target - w) / 2)
    if r < .6 or w == 0: return m
    p = np.pad(m, int(r) + 3).astype(np.uint8)
    o = cv2.distanceTransform(p, cv2.DIST_L2, 5) > r if w > target else cv2.distanceTransform(1 - p, cv2.DIST_L2, 5) <= r
    return tight(cv2.GaussianBlur(o.astype(np.float32), (0, 0), 1.5) > .5)[0]

def trace(m):
    """Binary mask -> pen recording in pixel units, y up, origin at the mask's bottom-left."""
    from fontTools.svgLib.path import parse_path
    from fontTools.pens.recordingPen import RecordingPen
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'a.pbm')
        Image.fromarray(np.where(np.pad(m, 4), 0, 255).astype(np.uint8)).convert('1').save(f)
        svg = subprocess.run(['potrace', '-b', 'svg', '-t', '12', '-a', '1.1', '-O', '0.6', '-u', '10', '-o', '-', f],
                             capture_output=True, text=True, check=True).stdout
    pen = RecordingPen()
    for d_ in re.findall(r'\sd="([^"]+)"', svg): parse_path(d_, pen)
    return [(op, tuple((x * .1 - 4, y * .1 - 4) for x, y in args)) for op, args in pen.value]

# ---------------------------------------------------------------- build
EM, ASC, DESC = 1000, 880, -120

def cmd_build(a):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import replayRecording
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
    meta = load_meta(a.work)
    if not meta: sys.exit('no glyphs.json in ' + a.work)
    G = lambda fn: load_mask(os.path.join(a.work, 'glyphs', fn))
    han = [c for c, m in meta.items() if not is_ascii(c) and c not in PUNCT]
    # one global scale so the median Han character is FACE units tall; relative sizes stay as written
    def raw_k(m): return EM / m['px_per_em'] if m['source'] == 'grid' else 1.0
    sizes = [max(G(meta[c]['file']).shape) * raw_k(meta[c]) for c in han]
    gscale = a.face / float(np.median(sizes)) if sizes else 1.0
    def k_of(m): return raw_k(m) * gscale
    # target stroke width in font units: median over the Han glyphs
    widths = [stroke_width(G(meta[c]['file'])) * k_of(meta[c]) for c in han[:300]]
    target = float(np.median([w for w in widths if w > 0])) if widths else 0
    glyphs, adv, bbox, cmap, alts, rec = {}, {}, {}, {}, {}, {}

    def draw(name, mask, k, place):
        if not a.no_weight and target and not is_ascii_name(name):
            mask = set_width(mask, target / k, limit=max(1.0, .25 * target / k))
        up, f = smooth_up(mask); kk = k / f; v = trace(up); h, w = up.shape
        dx, dy, width = place(w * kk, h * kk)
        pen = T2CharStringPen(width, None); t = TransformPen(pen, (kk, 0, 0, kk, dx, dy)); replayRecording(v, t)
        b = BoundsPen(None); replayRecording(v, TransformPen(b, (kk, 0, 0, kk, dx, dy)))
        glyphs[name] = pen.getCharString(); adv[name] = width; bbox[name] = b.bounds; rec[name] = (v, kk, dx, dy)
    def is_ascii_name(n): return n.startswith('lat.')

    for c, m in meta.items():
        k = k_of(m); name = ('lat.%04X' % ord(c)) if is_ascii(c) else 'uni%04X' % ord(c)
        files = [m['file']] + m.get('alts', [])
        for j, fn in enumerate(files):
            n = name if j == 0 else f'{name}.alt{j}'
            mask = G(fn)
            if is_ascii(c):
                sb = 50
                if m['source'] == 'grid':          # keep the writer's height above the printed baseline (88% down the box)
                    x0, y0, x1, y1 = m['box']
                    place = lambda w, h, y1=y1: (sb, (0.88 - y1) * EM * gscale, round(w + 2 * sb))
                else:
                    place = lambda w, h: (sb, 0, round(w + 2 * sb))
            elif c in PUNCT:
                place = lambda w, h: (200 - w / 2, 40, EM) if c in '，。、' else (500 - w / 2, (ASC + DESC) / 2 - h / 2, EM)
            elif m['source'] == 'grid' and a.keep_position:
                x0, y0, x1, y1 = m['box']
                place = lambda w, h, x0=x0, y1=y1: (500 - (.5 - x0) * EM * gscale, (ASC + DESC) / 2 + (.5 - y1) * EM * gscale, EM)
            else:
                place = lambda w, h: (500 - w / 2, (ASC + DESC) / 2 - h / 2, EM)
            draw(n, mask, k, place)
            if j == 0: cmap[ord(c)] = n
        if len(files) > 1: alts[name] = [f'{name}.alt{j}' for j in range(1, len(files))]

    # vertical text: the lower-left comma/period/caesura move to the upper right
    vert = []
    for c in '，。、':
        n = 'uni%04X' % ord(c)
        if n in rec:
            v, kk, dx, dy = rec[n]; m = n + '.vert'
            pen = T2CharStringPen(EM, None); replayRecording(v, TransformPen(pen, (kk, 0, 0, kk, dx + 560, dy + 560)))
            glyphs[m] = pen.getCharString(); adv[m] = EM; x0, y0, x1, y1 = bbox[n]; bbox[m] = (x0 + 560, y0 + 560, x1 + 560, y1 + 560)
            vert.append(f' sub {n} by {m};')
    # .notdef: an empty box, so a missing character is visible instead of silently blank
    p = T2CharStringPen(EM, None)
    for (x0, y0, x1, y1), outer in (((100, -60, 900, 780), True), ((160, 0, 840, 720), False)):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)] if outer else [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
        p.moveTo(pts[0]); [p.lineTo(q) for q in pts[1:]]; p.closePath()
    glyphs['.notdef'] = p.getCharString(); adv['.notdef'] = EM; bbox['.notdef'] = (100, -60, 900, 780)
    for n, u, w in (('space', 0x20, 300), ('uni3000', 0x3000, EM)):
        glyphs[n] = T2CharStringPen(w, None).getCharString(); adv[n] = w; bbox[n] = None; cmap[u] = n
    order = ['.notdef', 'space', 'uni3000'] + sorted(k for k in glyphs if k not in ('.notdef', 'space', 'uni3000'))
    fam = a.family; ps = re.sub(r'[^A-Za-z0-9-]', '', fam) or 'Handwriting'
    fb = FontBuilder(EM, isTTF=False); fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
    fb.setupNameTable(dict(familyName=fam, styleName='Regular', uniqueFontIdentifier=f'{a.version};{ps}-Regular', fullName=fam,
                           psName=ps + '-Regular', version=f'Version {a.version}', description="Made with hwfont from the author's own handwriting.",
                           **({'copyright': a.copyright} if a.copyright else {}), **({'licenseDescription': a.license} if a.license else {})))
    fb.setupCFF(ps + '-Regular', {'FullName': fam, 'FamilyName': fam, 'Weight': 'Regular'}, {n: glyphs[n] for n in order}, {})
    fb.setupHorizontalMetrics({n: (adv[n], round(bbox[n][0]) if bbox[n] else 0) for n in order})
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC, lineGap=200)
    fb.setupOS2(sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=200, usWinAscent=1100, usWinDescent=250,
                fsSelection=(1 << 6) | (1 << 7), usWeightClass=400, version=4, sxHeight=500, sCapHeight=700,
                ulUnicodeRange1=1, ulUnicodeRange2=(1 << 16) | (1 << 27), ulCodePageRange1=1 << 18)
    fb.setupPost(keepGlyphNames=False)
    fb.setupVerticalHeader(ascent=500, descent=-500, lineGap=0)
    fb.setupVerticalMetrics({n: (EM, (ASC - round(bbox[n][3])) if bbox[n] else 0) for n in order})
    fea = ['languagesystem DFLT dflt;', 'languagesystem hani dflt;']
    if alts:   # rotate through the alternates so a repeated character does not look stamped
        rules = []
        for n, al in alts.items():
            chain = [n] + al
            rules.append(f" sub {n} {n}' by {al[0]};")
            for i, x in enumerate(al):
                nxt = chain[(i + 2) % len(chain)]
                if nxt != n: rules.append(f" sub {x} {n}' by {nxt};")
        fea.append('feature aalt {\n' + '\n'.join(f" sub {n} from [{n} {' '.join(al)}];" for n, al in alts.items()) + '\n} aalt;')
        fea.append('feature calt {\n' + '\n'.join(rules) + '\n} calt;')
    if vert: fea.append('feature vert {\n' + '\n'.join(vert) + '\n} vert;')
    addOpenTypeFeaturesFromString(fb.font, '\n'.join(fea))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fb.font.save(a.out)
    n_han = sum(1 for c in meta if '\u4e00' <= c <= '\u9fff')
    print(f'{a.out}: {len(meta)} characters ({n_han} Han), {sum(len(v) for v in alts.values())} alternates, stroke width target {target:.0f} units')

# ---------------------------------------------------------------- specimen and check
def cmd_specimen(a):
    from fontTools.ttLib import TTFont
    cm = TTFont(a.font).getBestCmap(); text = a.text
    f = ImageFont.truetype(a.font, a.size); lf = label_font(18)
    lines, cur = [], ''
    for ch in text:
        if ch == '\n' or len(cur) >= a.width: lines.append(cur); cur = '' if ch == '\n' else ch
        else: cur += ch
    lines.append(cur)
    lh = int(a.size * 1.45); im = Image.new('RGB', (int(a.size * a.width * 1.02) + 80, lh * len(lines) + 110), 'white')
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text((40, 40 + i * lh), l, font=f, fill=(20, 20, 20))
    miss = sorted({c for c in text if not c.isspace() and ord(c) not in cm})
    d.text((40, im.height - 50), f'{len(set(c for c in text if not c.isspace())) - len(miss)} 字已有，缺 {len(miss)} 字（显示为方框）', font=lf, fill=(150, 60, 60))
    im.save(a.out); print(f'{a.out}; missing: {"".join(miss)}')

def cmd_check(a):
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    f = TTFont(a.font); gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = []
    for n in f.getGlyphOrder():
        b = BoundsPen(gs); gs[n].draw(b)
        if b.bounds and not n.startswith('lat.') and not n.endswith('.vert'):
            x0, y0, x1, y1 = b.bounds
            if x0 < -20 or x1 > 1020 or y0 < -180 or y1 > 940: out.append(n)
    han = sum(1 for u in cm if 0x4E00 <= u <= 0x9FFF)
    print(f'glyphs {len(gs)}, mapped {len(cm)}, Han {han}; outside the em box: {len(out)} {out[:10]}')
    try:
        import ots
        r = ots.sanitize(a.font, os.devnull, capture_output=True); print('OTS', 'pass' if r.returncode == 0 else 'FAIL ' + r.stderr.decode()[:300])
    except ImportError:
        print('OTS not installed (pip install opentype-sanitizer) - skipped')

# ---------------------------------------------------------------- cli
def main():
    P = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    S = P.add_subparsers(dest='cmd', required=True)
    t = S.add_parser('template'); t.add_argument('--chars'); t.add_argument('--count', type=int, default=500)
    t.add_argument('--extra', default='punct,digits'); t.add_argument('--title', default='我的手写字体'); t.add_argument('--out', required=True)
    e = S.add_parser('extract'); e.add_argument('--template', required=True); e.add_argument('--photos', nargs='+', required=True)
    e.add_argument('--out', required=True); e.add_argument('--threshold', type=float, default=.38)
    s = S.add_parser('segment'); s.add_argument('--photo', required=True); s.add_argument('--text', required=True)
    s.add_argument('--out', required=True); s.add_argument('--threshold', type=float, default=.35)
    c = S.add_parser('cut'); c.add_argument('--work', required=True)
    r = S.add_parser('review'); r.add_argument('--work', required=True)
    b = S.add_parser('build'); b.add_argument('--work', required=True); b.add_argument('--family', required=True)
    b.add_argument('--out'); b.add_argument('--version', default='0.100'); b.add_argument('--face', type=float, default=800)
    b.add_argument('--keep-position', action='store_true'); b.add_argument('--no-weight', action='store_true')
    b.add_argument('--copyright', default=''); b.add_argument('--license', default='')
    sp = S.add_parser('specimen'); sp.add_argument('--font', required=True); sp.add_argument('--text', required=True)
    sp.add_argument('--out', required=True); sp.add_argument('--size', type=int, default=64); sp.add_argument('--width', type=int, default=16)
    ck = S.add_parser('check'); ck.add_argument('--font', required=True)
    a = P.parse_args()
    if a.cmd == 'build' and not a.out: a.out = os.path.join(a.work, re.sub(r'\W', '', a.family) + '-Regular.otf')
    if a.cmd == 'specimen' and os.path.exists(a.text): a.text = open(a.text, encoding='utf8').read().strip()
    globals()['cmd_' + a.cmd](a)

if __name__ == '__main__':
    main()
