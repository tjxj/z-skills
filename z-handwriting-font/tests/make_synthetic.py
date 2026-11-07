"""Fill a printed template with glyphs from any handwriting font you own, then fake a phone photo of it.

  python3 tests/make_synthetic.py TEMPLATE_DIR FILL_FONT OUT_DIR

Each page: random jitter of size/position per character, a tilt and perspective, uneven lighting,
sensor noise and JPEG compression. Characters the fill font lacks are left blank on purpose.
"""
import json, os, sys, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import hwfont as H

tdir, font, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True); random.seed(7); np.random.seed(7)
T = json.load(open(os.path.join(tdir, 'template.json'), encoding='utf8'))
cm = TTFont(font).getBestCmap()
order = list(range(len(T['pages']))); random.shuffle(order)          # photos arrive out of order
for p in order:
    im = Image.open(os.path.join(tdir, f'page-{p + 1:02d}.png')).convert('L'); d = ImageDraw.Draw(im)
    for i, c in enumerate(T['pages'][p]):
        if ord(c) not in cm: continue
        x0, y0, x1, y1 = H.cell_square(i); s = int(H.SQ * random.uniform(.68, .86))
        f = ImageFont.truetype(font, s)
        dx = random.randint(-8, 8); dy = random.randint(-8, 8)
        d.text(((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy), c, font=f, fill=random.randint(10, 40), anchor='mm')
    g = np.array(im)
    # perspective + tilt into a 3000x4000 "photo" with a desk around the page
    PW, PH = 3000, 4000; src = np.float32([[0, 0], [H.W, 0], [0, H.H], [H.W, H.H]])
    j = lambda: random.uniform(-90, 90)
    dst = np.float32([[300 + j(), 260 + j()], [2700 + j(), 330 + j()], [250 + j(), 3700 + j()], [2760 + j(), 3640 + j()]])
    M = cv2.getPerspectiveTransform(src, dst)
    photo = cv2.warpPerspective(g, M, (PW, PH), flags=cv2.INTER_CUBIC, borderValue=95)
    yy, xx = np.mgrid[0:PH, 0:PW]
    light = .72 + .28 * np.exp(-(((xx - 900) / 2600) ** 2 + ((yy - 1200) / 3000) ** 2))   # brighter top-left, shadowed corner
    photo = photo * light + np.random.normal(0, 6, photo.shape)
    photo = cv2.GaussianBlur(np.clip(photo, 0, 255).astype(np.uint8), (0, 0), 1.1)
    Image.fromarray(photo).save(os.path.join(out, f'IMG_{1000 + p * 7}.jpg'), quality=82)
print(f'{len(order)} photos -> {out}')
