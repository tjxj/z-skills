"""重出 demos/ 与 docs/ 下的全部示例和图库（维护用）。

python3 scripts/gallery.py            # 全量
依赖 rsvg-convert 与 Pillow。
"""
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from dongxi import CANVAS, STYLES, render  # noqa: E402

SPECS = ROOT / "demos" / "specs"
FONTS = [pathlib.Path.home() / "Library/Fonts/SourceHanSerifSC-VF.ttf", "/System/Library/Fonts/STHeiti Medium.ttc"]
# 每种图型挑一张做图库代表
TYPE_PICK = {"flow": "rag-sketch", "pipeline": "rag", "cycle": "agent-loop"}
RATIO_SPEC = "rag"
STYLE_SPEC = "rag"
WIDE = ["rag", "traffic-sankey", "rag-gantt", "launch-stat", "post-heatmap", "model-radar"]


def font(size):
    for f in FONTS:
        if pathlib.Path(f).exists():
            return ImageFont.truetype(str(f), size)
    return ImageFont.load_default()


def png(svg_path, out, width):
    subprocess.run(["rsvg-convert", "-w", str(width), "-o", str(out), str(svg_path)], check=True)


def sheet(items, out, cols, tile_w, bg="#1d1d1f", fg="#f5f5f7", label_h=46):
    """items: [(svg路径, 标签)]，拼成带标签的图库。"""
    tmp = pathlib.Path(tempfile.mkdtemp())
    ims = []
    for i, (svg, lab) in enumerate(items):
        p = tmp / f"{i}.png"
        png(svg, p, tile_w)
        ims.append((Image.open(p).convert("RGB"), lab))
    th = max(im.height for im, _ in ims)
    gap = 18
    rows = (len(ims) + cols - 1) // cols
    g = Image.new("RGB", (cols * (tile_w + gap) + gap, rows * (th + label_h + gap) + gap), bg)
    d = ImageDraw.Draw(g)
    f = font(24)
    for k, (im, lab) in enumerate(ims):
        x = gap + (k % cols) * (tile_w + gap)
        y = gap + (k // cols) * (th + label_h + gap)
        g.paste(im, (x, y))
        d.text((x + 2, y + im.height + 10), lab, fill=fg, font=f)
    g.save(out, quality=88, optimize=True)


def main():
    svg_dir, png_dir, sty_dir, rat_dir, docs = (ROOT / "demos" / "svg", ROOT / "demos" / "png", ROOT / "demos" / "styles",
                                                ROOT / "demos" / "ratios", ROOT / "docs")
    for d in (svg_dir, png_dir, sty_dir, rat_dir, docs):
        d.mkdir(parents=True, exist_ok=True)
    specs = {p.stem: json.loads(p.read_text()) for p in sorted(SPECS.glob("*.json"))}
    meta = {}
    for name, sp in specs.items():
        svg, style, T = render(sp)
        (svg_dir / f"{name}.svg").write_text(svg)
        png(svg_dir / f"{name}.svg", png_dir / f"{name}.png", 750)
        meta[name] = (sp["type"], style)
        print(f"{name:18s} {sp['type']:10s} {style:10s} {T:.1f}s")
    for st in STYLES:
        svg, _, _ = render(specs[STYLE_SPEC], st)
        (sty_dir / f"{STYLE_SPEC}-{st}.svg").write_text(svg)
    for name in WIDE:
        svg, _, _ = render(specs[name], None, "16:9")
        (rat_dir / f"{name}-16x9.svg").write_text(svg)
    for r in CANVAS:
        svg, _, _ = render(specs[RATIO_SPEC], None, r)
        (rat_dir / f"{RATIO_SPEC}-{r.replace(':', 'x')}.svg").write_text(svg)

    by_type = {}
    for name, (t, st) in meta.items():
        if TYPE_PICK.get(t, name) == name or t not in TYPE_PICK:
            by_type.setdefault(t, (name, st))
    sheet([(svg_dir / f"{nm}.svg", f"{t} · {st}") for t, (nm, st) in by_type.items()], docs / "types-grid.jpg", 6, 360)
    sheet([(sty_dir / f"{STYLE_SPEC}-{st}.svg", st) for st in STYLES], docs / "styles-grid.jpg", 5, 400)
    sheet([(rat_dir / f"{nm}-16x9.svg", f"{meta[nm][0]} · 16:9") for nm in WIDE], docs / "wide-grid.jpg", 2, 760)
    for old in ("demos-grid.png", "styles-grid.png"):
        (docs / old).unlink(missing_ok=True)
    print(f"{len(by_type)} 种图型 · {len(STYLES)} 种风格 · {len(CANVAS)} 种画幅")


if __name__ == "__main__":
    main()
