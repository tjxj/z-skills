#!/usr/bin/env python3
"""把 slides.html 构建成可直接双击打开的单文件演示稿。

输出（默认写到源文件所在目录）：
  index.html           整页版：每页完整呈现
  index-timeline.html  逐步书写版：点击一次写一步

样式、运行时、手写字体（按本稿用字裁剪）、图片全部内嵌，拷到 Windows / U 盘 /
微信传文件都能原样打开。
"""
from __future__ import annotations

import argparse
import base64
import glob
import html as htmlmod
import io
import mimetypes
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / "assets"
BUNDLED_FONT = ASSETS / "fonts" / "Xiaolai-GB2312.woff2"
FAMILY = "WH Hand"
EXTRA_CHARS = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "，。、：；！？“”‘’（）《》〈〉【】「」『』—–…·・→←↑↓↔⇒✓✗×÷±≈≠≤≥°％‰￥€$①②③④⑤⑥⑦⑧⑨⑩"
)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------------------------------------------------------------- 字体

def find_hanzipen() -> Path | None:
    names = ("Hanzipen.ttc", "HanziPen.ttc")
    dirs = [Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental")]
    for d in dirs:
        for n in names:
            if (d / n).is_file():
                return d / n
    for n in names:
        hits = sorted(glob.glob(f"/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*.asset/AssetData/{n}"))
        if hits:
            return Path(hits[-1])
    return None


def collect_chars(source: str) -> str:
    class P(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.buf: list[str] = []
            self.skip = 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.skip += 1
            for k, v in attrs:
                if v and k in ("data-note", "data-title", "alt", "title", "aria-label"):
                    self.buf.append(v)

        def handle_endtag(self, tag):
            if tag in ("script", "style") and self.skip:
                self.skip -= 1

        def handle_data(self, data):
            if not self.skip:
                self.buf.append(data)

    p = P()
    p.feed(source)
    text = "".join(p.buf) + EXTRA_CHARS
    return "".join(sorted({c for c in text if not c.isspace() or c == " "}))


def _has_fonttools() -> bool:
    try:
        import fontTools.subset  # noqa: F401
        return True
    except ImportError:
        return False


def _has_brotli() -> bool:
    try:
        import brotli  # noqa: F401
        return True
    except ImportError:
        return False


def subset_font(path: Path, chars: str, face: int = 0) -> tuple[bytes, str, list[str]]:
    import logging

    from fontTools import subset
    from fontTools.ttLib import TTFont

    logging.getLogger("fontTools").setLevel(logging.ERROR)

    font = TTFont(str(path), fontNumber=face, lazy=False)
    cmap = font.getBestCmap() or {}
    missing = [c for c in chars if ord(c) not in cmap and not c.isspace() and c not in EXTRA_CHARS]
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.flavor = "woff2" if _has_brotli() else "woff"
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    font.flavor = opts.flavor
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue(), opts.flavor, missing


def font_face(choice: str, chars: str) -> tuple[str, str, list[str]]:
    """返回 (@font-face CSS, 说明, 缺字列表)。"""
    choice = choice or "auto"
    path: Path | None = None
    face = 0
    label = choice
    if choice == "auto":
        hp = find_hanzipen()
        if hp:
            path, label = hp, "hanzipen"
        else:
            label = "xiaolai"
    if choice == "hanzipen" or label == "hanzipen":
        path = path or find_hanzipen()
        if not path:
            raise SystemExit("找不到翩翩体（HanziPen SC）。macOS 打开「字体册」搜索“翩翩体”下载；Windows 请用 --font xiaolai")
        label = "hanzipen"
    elif label == "xiaolai" or choice == "xiaolai":
        label = "xiaolai"
        path = BUNDLED_FONT
    elif choice not in ("auto",):
        path = Path(choice).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"字体文件不存在：{path}")
        label = path.name

    can_subset = _has_fonttools() and (path.suffix.lower() != ".woff2" or _has_brotli())
    if can_subset:
        data, flavor, missing = subset_font(path, chars, face)
        b64 = base64.b64encode(data).decode()
        css = f'@font-face{{font-family:"{FAMILY}";src:url(data:font/{flavor};base64,{b64}) format("{flavor}");font-display:block;}}'
        return css, f"{label}（按本稿 {len(chars)} 个字符裁剪，{len(data) // 1024} KB）", missing

    if label == "hanzipen":
        log("提示：未安装 fontTools，翩翩体改为引用本机字体，换电脑会丢失手写效果。pip install fonttools brotli 后重新构建即可内嵌。")
        css = f'@font-face{{font-family:"{FAMILY}";src:local("HanziPen SC"),local("HanziPenSC-W3");font-display:block;}}'
        return css, "hanzipen（本机引用，未内嵌）", []
    if path.suffix.lower() in (".woff2", ".woff", ".ttf", ".otf"):
        data = path.read_bytes()
        fmt = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}[path.suffix.lower()]
        mime = {"truetype": "ttf", "opentype": "otf"}.get(fmt, fmt)
        css = f'@font-face{{font-family:"{FAMILY}";src:url(data:font/{mime};base64,{base64.b64encode(data).decode()}) format("{fmt}");font-display:block;}}'
        missing = []
        table = path.with_suffix(".chars.txt")
        if table.is_file():  # 随附字体附带字表，没有 fontTools 也能准确判断缺字
            covered = set(table.read_text(encoding="utf-8"))
            missing = [c for c in chars if c not in covered and not c.isspace() and c not in EXTRA_CHARS]
        return css, f"{label}（完整内嵌 {len(data) // 1024} KB，装 fonttools 可裁剪变小）", missing
    raise SystemExit("当前环境无法处理该字体：请 pip install fonttools brotli")


# ---------------------------------------------------------------- 图片

def load_image(src: str, base: Path, keep_remote: bool) -> tuple[bytes, str] | None:
    if src.startswith("data:"):
        return None
    if re.match(r"^https?://", src):
        if keep_remote:
            return None
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (wanghong-ppt build)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            mime = resp.headers.get_content_type()
        return data, mime
    path = Path(htmlmod.unescape(src).split("#")[0].split("?")[0])
    if not path.is_absolute():
        path = (base / path).resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return path.read_bytes(), mime


def shrink(data: bytes, mime: str, max_side: int) -> tuple[bytes, str]:
    if mime in ("image/svg+xml", "image/gif"):
        return data, mime
    try:
        from PIL import Image
    except ImportError:
        return data, mime
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return data, mime
    resized = False
    if max(im.size) > max_side:
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        resized = True
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() or im.mode == "P" else "RGB")
    out = io.BytesIO()
    im.save(out, "WEBP", quality=88, method=5)
    webp = out.getvalue()
    if resized or len(webp) < len(data) * 0.9:
        return webp, "image/webp"
    return data, mime


# ---------------------------------------------------------------- 组装

STRIP = [
    re.compile(r"<link\b[^>]*(template|base|animations|neat-annotations|timeline|deepseek-example)\.css[^>]*>\s*", re.I),
    re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"'][^\"']*(runtime|timeline)\.js[\"'][^>]*>\s*</script>\s*", re.I),
    re.compile(r"<style\b[^>]*\bid\s*=\s*[\"']wh-(font|template)[\"'][^>]*>.*?</style>\s*", re.I | re.S),
    re.compile(r"<script\b[^>]*\bid\s*=\s*[\"']wh-(runtime|audit)[\"'][^>]*>.*?</script>\s*", re.I | re.S),
    re.compile(r"<meta\b[^>]*name\s*=\s*[\"']wh-[^\"']*[\"'][^>]*>\s*", re.I),
]
DECK_TAG = re.compile(r"<main\b([^>]*\bclass\s*=\s*[\"'][^\"']*\bdeck\b[^\"']*[\"'][^>]*)>", re.I)
IMG_SRC = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*)([\"'])(.*?)\2", re.I | re.S)
SVG_IMG = re.compile(r"(<image\b[^>]*?\b(?:xlink:)?href\s*=\s*)([\"'])(.*?)\2", re.I | re.S)


def count_slides(text: str) -> int:
    return len(re.findall(r"<section\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bslide\b", text, re.I))


def build(source: Path, out_dir: Path, font: str = "auto", timeline: bool = True,
          max_image: int = 1800, keep_remote: bool = False, quiet: bool = False) -> list[Path]:
    source = source.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [out_dir / "index.html"] + ([out_dir / "index-timeline.html"] if timeline else [])
    if source in targets:
        raise SystemExit(f"源文件不能与输出同名：{source}。请把源稿命名为 slides.html")
    text = source.read_text(encoding="utf-8")
    if not DECK_TAG.search(text):
        raise SystemExit('源文件里没有 <main class="deck">')
    n = count_slides(text)
    if not n:
        raise SystemExit('源文件里没有 <section class="slide">')
    for rx in STRIP:
        text = rx.sub("", text)

    # 图片内嵌
    cache: dict[str, str] = {}
    problems: list[str] = []

    def inline(m: re.Match) -> str:
        src = htmlmod.unescape(m.group(3).strip())
        if src in cache:
            return f"{m.group(1)}{m.group(2)}{cache[src]}{m.group(2)}"
        try:
            got = load_image(src, source.parent, keep_remote)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"图片无法读取：{src}（{exc}）")
            return m.group(0)
        if not got:
            return m.group(0)
        data, mime = shrink(*got, max_image)
        uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
        cache[src] = uri
        return f"{m.group(1)}{m.group(2)}{uri}{m.group(2)}"

    text = IMG_SRC.sub(inline, text)
    text = SVG_IMG.sub(inline, text)

    chars = collect_chars(text)
    face_css, font_note, missing = font_face(font, chars)
    css = (ASSETS / "template.css").read_text(encoding="utf-8")
    js = (ASSETS / "runtime.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    head_inject = (
        '<meta name="wh-generator" content="z-wanghong-handwritten-ppt">\n'
        f'<meta name="wh-missing-glyphs" content="{htmlmod.escape("".join(missing))}">\n'
        f'<style id="wh-font">{face_css}</style>\n'
        f'<style id="wh-template">\n{css}\n</style>\n'
    )
    if not re.search(r"<meta\b[^>]*name\s*=\s*[\"']viewport", text, re.I):
        head_inject = '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + head_inject
    m = re.search(r"<head\b[^>]*>", text, re.I)
    if not m:
        raise SystemExit("源文件缺少 <head>")
    # 放在 <meta charset> 之后、作者自己的 <style> 之前，作者样式可以覆盖模板
    charset = re.search(r"<meta\b[^>]*charset[^>]*>\s*", text[m.end():], re.I)
    at = m.end() + (charset.end() if charset else 0)
    text = text[:at] + "\n" + head_inject + text[at:]
    if "</body>" not in text.lower():
        raise SystemExit("源文件缺少 </body>")
    idx = text.lower().rfind("</body>")
    text = text[:idx] + f'<script id="wh-runtime">\n{js}\n</script>\n' + text[idx:]

    def with_mode(t: str, mode: str, alt: str | None) -> str:
        def rep(mm: re.Match) -> str:
            attrs = re.sub(r"\s+data-(mode|alt)\s*=\s*([\"']).*?\2", "", mm.group(1))
            extra = f' data-mode="{mode}"' + (f' data-alt="{alt}"' if alt else "")
            return f"<main{attrs}{extra}>"
        return DECK_TAG.sub(rep, t, count=1)

    outputs = []
    static = with_mode(text, "static", "index-timeline.html" if timeline else None)
    targets[0].write_text(static, encoding="utf-8")
    outputs.append(targets[0])
    if timeline:
        steps = with_mode(text, "steps", "index.html")
        targets[1].write_text(steps, encoding="utf-8")
        outputs.append(targets[1])

    if not quiet:
        size = targets[0].stat().st_size / 1024 / 1024
        log(f"构建完成：{n} 页，字体 {font_note}，图片内嵌 {len(cache)} 张，单文件 {size:.1f} MB")
        for p in outputs:
            log(f"  {p}")
        if missing:
            log(f"注意：手写字体缺 {len(missing)} 个字，将用楷体补位：{''.join(missing[:60])}")
    for p in problems:
        log(f"错误：{p}")
    if problems:
        raise SystemExit(1)
    return outputs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="slides.html 源稿")
    ap.add_argument("--out-dir", type=Path, help="输出目录，默认与源稿同目录")
    ap.add_argument("--font", default="auto", help="auto | hanzipen | xiaolai | 字体文件路径（默认 auto：Mac 有翩翩体用翩翩体，否则用内置小赖字体）")
    ap.add_argument("--no-timeline", action="store_true", help="只生成整页版")
    ap.add_argument("--max-image", type=int, default=1800, help="图片最长边上限，默认 1800px")
    ap.add_argument("--keep-remote", action="store_true", help="网络图片保持外链，不下载内嵌")
    args = ap.parse_args()
    src = args.source.expanduser()
    if not src.is_file():
        raise SystemExit(f"找不到源文件：{src}")
    build(src, (args.out_dir or src.parent).expanduser(), args.font, not args.no_timeline, args.max_image, args.keep_remote)


if __name__ == "__main__":
    main()
