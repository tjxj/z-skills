# 用图片模型生成单页的提示词

HTML 版是主力交付物。只有当用户需要“真手写”的单张图片（例如公众号配图、海报中的一页）时，才用下面的提示词让图片模型生成。视觉规则与 `style-guide.md` 一致。

## 统一风格（每页都附上）

```text
Exact 16:9 landscape presentation slide. A page of handwritten lecture notes written on a tablet (Notability style), photographed flat — no projector, no paper edge, no perspective.

Background: almost pure white, no texture, no grid, no border.
Handwriting: small, neat, thin dark-navy strokes, slightly uneven baselines with lines tilting up very slightly to the right, generous line spacing. The heading is just the first sentence written at the top-left, only slightly larger than the body, with no rule under it.
Content occupies roughly half of the page; the right side and the bottom stay empty.

Marks, used sparingly and only for meaning:
- a short red hand-drawn underline under two or three key characters
- a thin red rectangle whose corner strokes cross and overshoot, around a formula or a recommended option
- a semi-transparent green highlighter band under the one-sentence conclusion
- a small yellow or green dot behind a single symbol or number
- a red outline warning triangle with an exclamation mark followed by red text for a risk
- blue ink for formulas, symbols and side notes; grey small text for captions
At most two kinds of emphasis on one page.

Render every Chinese character, Latin word and number exactly as supplied. No extra text.
Forbidden: cards, shadows, gradients, rounded colour blocks, icons, emoji, logos, headers, footers, page numbers, watermarks, bold text, huge numbers.
```

## 单页模板

```text
{统一风格}

Heading (top-left): "{标题句}"
Body lines, left-aligned, in this order:
1. "{第一行}"
2. "{第二行}"  — indent this line and write it in blue
3. "{第三行}"  — draw a short red underline under "{关键词}"
Conclusion with a green highlighter band: "{结论}"
Diagram on the right (optional): {对象、方向、标签、颜色}
```

## 封面

```text
{统一风格}

Cover page. Small centered title in the upper part: "{标题}".
In the middle, one {插图描述：论文插图 / 手绘示意 / 实拍照片}, modest size, lots of white space around it.
At the bottom, one small centered line: "{作者} · {机构或场合} · {日期}".
No subtitle, no decoration.
```

## 词语思维导图

```text
{统一风格}

Heading: "{标题句}"
A word mind map without boxes: the central word "{中心词}" with a small yellow dot behind it, and {N} words around it: "{词1}", "{词2}", "{词3}" … Each is connected to the centre by a thin, slightly curved hand-drawn line. One short blue note under the centre: "{说明}".
```

## 截图页

```text
{统一风格}

Heading: "{标题句}"
Left: three short handwritten lines: "{行1}" / "{行2}" / "{行3}".
Right: the supplied screenshot placed flat inside a thin light-grey hand-drawn frame, with one small grey caption under it: "{图注}".
```
