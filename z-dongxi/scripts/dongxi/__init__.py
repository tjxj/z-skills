"""「动」悉万物：把一段内容排成一张会动的 3:4 解析图。"""
from .core import H, W, Painter
from .layouts import LAYOUTS
from .styles import DEFAULT_STYLE, STYLES, pick_style


def render(spec, style=None):
    """spec 为 dict，返回单行 SVG 字符串。"""
    kind = spec.get("type")
    if kind not in LAYOUTS:
        raise ValueError(f"未知图型 {kind}，可选：{', '.join(LAYOUTS)}")
    name = style or spec.get("style") or "auto"
    if name == "auto":
        name = pick_style(" ".join(str(spec.get(k, "")) for k in ("title", "kicker", "subtitle", "topic")))
    if name not in STYLES:
        raise ValueError(f"未知风格 {name}，可选：{', '.join(STYLES)}")
    P = Painter(STYLES[name], name, spec.get("seed", 11))
    head, top = P.header(spec.get("kicker"), spec["title"], spec.get("subtitle"), spec.get("seal"), True)
    bot = H - (62 if spec.get("foot") else 36)
    body, T = LAYOUTS[kind](P, spec, top + 6, bot)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%"'
           f' style="display:block;max-width:{W}px;margin:0 auto">'
           + P.background() + head + body + P.foot(spec.get("foot")) + "</svg>")
    return svg.replace("\n", " ").replace("。", "．"), name, T
