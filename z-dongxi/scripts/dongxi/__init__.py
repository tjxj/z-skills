"""「动」悉万物：把一段内容排成一张会动的解析图（3:4 / 9:16 / 1:1 / 4:3 / 16:9）。"""
from .core import CANVAS, DEFAULT_RATIO, Painter
from .layouts import LAYOUTS
from .styles import DEFAULT_STYLE, STYLES, pick_style

try:
    from .charts import CHARTS
    LAYOUTS.update(CHARTS)
    from .extra import EXTRA
    LAYOUTS.update(EXTRA)
except ImportError:
    pass


def render(spec, style=None, ratio=None):
    """spec 为 dict，返回 (单行 SVG, 风格名, 周期秒数)。"""
    kind = spec.get("type")
    if kind not in LAYOUTS:
        raise ValueError(f"未知图型 {kind}，可选：{', '.join(LAYOUTS)}")
    name = style or spec.get("style") or "auto"
    if name == "auto":
        name = pick_style(" ".join(str(spec.get(k, "")) for k in ("title", "kicker", "subtitle", "topic")))
    if name not in STYLES:
        raise ValueError(f"未知风格 {name}，可选：{', '.join(STYLES)}")
    ratio = ratio or spec.get("ratio") or DEFAULT_RATIO
    if ratio not in CANVAS:
        raise ValueError(f"未知画幅 {ratio}，可选：{', '.join(CANVAS)}")
    P = Painter(STYLES[name], name, spec.get("seed", 11), ratio)
    head, top = P.header(spec.get("kicker"), spec["title"], spec.get("subtitle"), spec.get("seal"), True)
    bot = P.H - (62 if spec.get("foot") else 36)
    props = ""
    if spec.get("scene"):
        from .props import SCENE_H, scene
        bot -= SCENE_H
    body, T = LAYOUTS[kind](P, spec, top + 6, bot)
    if spec.get("scene"):
        props = scene(P, spec["scene"], bot + 4)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {P.W} {P.H}" width="100%"'
           f' style="display:block;max-width:{P.W}px;margin:0 auto">'
           + P.background() + head + props + body + P.foot(spec.get("foot")) + "</svg>")
    return svg.replace("\n", " ").replace("。", "．"), name, T
