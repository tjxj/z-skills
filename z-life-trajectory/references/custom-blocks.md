# 写定制插画块

现成的 22 种块讲的是通用的事：站点、卡片、计数、图表。每个人身上都有一两个标志性的物件或场景（乒乓球台、Apple II、显卡风扇、一行 CUDA 代码），画出来比写一句话更让人记得住。这时给他写一个定制插画块。

`examples/jensen_blocks.py` 里有 6 个现成的例子：`apple2`（绿屏贪吃蛇）、`pingpong`（球在两人之间来回）、`mesh_compare`（网格逐格点亮）、`cpu_gpu`（4 个大核和 72 个小核）、`cuda_fanout`（一行代码扇出上百万线程）、`alexnet`（显卡风扇 + 神经网络 + 错误率条）。

## 文件和加载

在 spec 同目录建一个 .py，导出 `BLOCKS` 字典：

```python
def bookshelf(c, top, b):
    ...
    return 150          # 这块占多高

BLOCKS = {'bookshelf': bookshelf}
```

spec 里加载，然后像内置块一样用：

```json
"plugins": ["someone_blocks.py"],
...
{"type": "bookshelf", "count": 14, "value": "1000 本", "label": "十年读完"}
```

`b` 就是 JSON 里的这一项，字段随你定。

## 函数怎么被调用

签名固定为 `fn(c, top, b) -> 高度`：

- `c`：画笔，见下文
- `top`：这块的顶边，整张图的绝对纵坐标。所有纵坐标都写成 `top + 偏移`
- 返回值：这块占的高度（像素）

每个块会被调用两次：第一次量高度（`c.measuring` 为 True，`top` 是个假值，画出来的东西会被丢掉，`c.warn` 也不生效），第二次在真正的位置画。所以：

- 返回的高度只能取决于 `b` 的内容，和 `top` 无关
- 别在函数里改 `b`，也别依赖全局状态
- 要随机就用 `random.Random(固定种子)`，保证两次结果一样
- `top` 经常带小数，坐标写成 `{top + 20:.1f}` 能让 SVG 小一些

## 坐标

整张图宽 750，每屏高 1000。

| 常量 | 值 | 含义 |
|---|---|---|
| `c.SPINE` | 78 | 左侧主线的横坐标 |
| `c.TX` | 118 | 正文左边 |
| `c.RX` | 702 | 正文右边 |
| `c.W` / `c.SH` | 750 / 1000 | 整图宽、每屏高 |
| `c.MONO` / `c.SERIF` | 字体栈 | 等宽字体、衬线字体，传给 `family` |

插画一般画在 `c.TX` 到 `c.RX` 之间。想让主线伸出一根短线接到插画上，调用 `c.stub(y)`。

## 画笔 `c`

**输出**

| 方法 | 说明 |
|---|---|
| `c.add(svg)` | 把一段 SVG 字符串加到画面上 |
| `c.warn(msg)` | 记一条提醒，`build --strict` 时会失败 |

**文字**

| 方法 | 说明 |
|---|---|
| `c.text(x, y, s, size, fill, weight=None, anchor=None, ls=None, family=None, opacity=None, limit=None)` | 返回 `<text>` 字符串，要包在 `c.add()` 里。`anchor` 可选 `middle` / `end`，`ls` 是字间距。超出右界（默认 `c.RX`，可用 `limit` 改）或左界 30 时报 `OVERFLOW` |
| `c.tw(s, size, weight=400, ls=0, family=None)` | 量一行字的宽度 |
| `c.wrap(s, size, weight, width)` | 按宽度折行，返回行列表 |
| `c.wrap_lines(lines, size, weight, width)` | 对一组行逐行折行 |
| `c.lines_of(v, size, weight, width)` | 标题专用：`v` 是列表就按给的断行，是字符串就自动折行 |
| `c.styled(item)` | 解析文字行，返回 `(文字, 颜色, 字重)`，支持 `{"text", "style"}` 写法 |

**图形（直接画上去，不用再 `c.add`）**

| 方法 | 说明 |
|---|---|
| `c.card(x, y, w, h, fill=None, stroke=None)` | 圆角卡片，深色屏自动换深色 |
| `c.icon(name, cx, cy, scale=1.0)` | 放一个图标，名字见 `icons.md` |
| `c.stub(y)` | 从主线伸出一根短线到 `c.TX`，并在主线上画圆点 |
| `c.marker(x, y, kind='stop')` | 主线圆点：`stop` / `major`（带脉冲）/ `terminus` |
| `c.arrowhead(x, y, dx, dy, size=9, color=None, w=3)` | 箭头尖，`(dx, dy)` 是朝向 |
| `c.grow_bar_h(x, y, w, h, color, begin=0, dur=7)` | 从左往右长出来的横条，长满后停一会再收回 |

**返回字符串的图形（要包在 `c.add()` 里）**

| 方法 | 说明 |
|---|---|
| `c.pulse(x, y, color=None, r0=13, r1=30, dur=2.6, begin=0)` | 向外扩散的脉冲圈 |

**颜色**

随深浅屏自动切换，优先用这些：

| 属性 | 浅色屏 | 深色屏 |
|---|---|---|
| `c.fg` | 墨色 | 纸色 |
| `c.muted` | 灰 | 浅灰 |
| `c.faint` | 浅灰 | 暗灰 |
| `c.acc` | 主题色 | 提亮的主题色 |
| `c.bg` | 纸色 | 深色底 |
| `c.card_fill` / `c.card_stroke` | 白卡片 | 深色卡片 |

要用主题里的其他颜色，读 `c.T['键名']`：`INK` `PAPER` `ACCENT` `ACCENT_L`（浅一档）`ACCENT_P`（淡底色）`SECOND`（第二主题色）`GRAY` `GRAY2` `GRAY3` `RULE` `RULE2` `GOLD` `DARK` `DACCENT` `WHITE` 等，完整列表见 `lifeline.py` 里的 `_BASE` 和 `THEMES`。`c.T` 里的颜色不随深浅屏变，块要放进深色屏时用 `c.dark` 判断一下。

## 公众号兼容

插件吐出的 SVG 和引擎一样要过 `lint`：

- 不用 `id`、`<defs>`、`<style>`、`<script>`、滤镜、渐变、`url(#…)`、`<use>`、`<clipPath>`、`<mask>`、`<image>`、`<foreignObject>`
- 动画只用 SMIL：`<animate>`、`<animateTransform>`、`<animateMotion path="…">`（不用 `<mpath>`），全部写 `repeatCount="indefinite"`
- 字号不小于 13
- 字符串里不要有换行，不出现全角句号「。」

## 动画时长和录屏

录视频时，时长 ≥ 4.5 秒的动画会推迟到这一屏滑到眼前的那一刻才开始，观众能从头看到；短于 4.5 秒的循环动画一直在转。所以：

- 讲故事的动画（柱子长出来、圆环耗尽、点阵熄灭）写成 ≥ 4.5 秒，用 `keyTimes` 在结尾停一会再重来
- 循环的小动画（风扇转、光标闪、球来回）写成 1~3 秒

## 常用动画写法

```python
# 闪烁
f'<rect ...><animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite"/></rect>'

# 沿路径流动的虚线（数据流、信号）
f'<path d="{d}" fill="none" stroke="{c.acc}" stroke-width="2.4" stroke-dasharray="8 160">'
f'<animate attributeName="stroke-dashoffset" values="0;-168" dur="1.4s" repeatCount="indefinite"/></path>'

# 小球沿路径运动
f'<circle r="7" fill="{c.acc}"><animateMotion path="{d}" dur="2.2s" repeatCount="indefinite"/></circle>'

# 绕自身中心旋转：外层 g 平移到中心，内层 g 转
f'<g transform="translate({cx} {cy})"><g>{blades}<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="1s" repeatCount="indefinite"/></g></g>'

# 依次点亮：同一个动画，begin 错开
for k in range(n):
    c.add(f'<g opacity="0.2"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.8s" begin="{k * 0.1:.2f}s" repeatCount="indefinite"/>{cell(k)}</g>')
```

## 一个完整的小例子

书一本本亮起来，右边写总数：

```python
def bookshelf(c, top, b):
    n = max(1, min(int(b.get('count', 12)), 16))
    c.card(c.TX, top, c.RX - c.TX, 150)
    c.stub(top + 75)
    for k in range(n):
        x = c.TX + 24 + k * 18
        h = 70 + (k * 37) % 30
        y = top + 118 - h
        c.add(f'<rect x="{x}" y="{y:.1f}" width="14" height="{h}" rx="2" fill="{c.card_stroke}"/>')
        c.add(f'<rect x="{x}" y="{y:.1f}" width="14" height="{h}" rx="2" fill="{c.acc}" opacity="0">'
              f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.9;1" dur="6s" '
              f'begin="{k * 0.25:.2f}s" repeatCount="indefinite"/></rect>')
    c.add(f'<line x1="{c.TX + 14}" y1="{top + 121:.1f}" x2="{c.TX + 34 + n * 18}" y2="{top + 121:.1f}" '
          f'stroke="{c.fg}" stroke-width="4" stroke-linecap="round"/>')
    c.add(c.text(c.RX - 24, top + 72, b.get('value', ''), 44, c.acc, 900, anchor='end'))
    c.add(c.text(c.RX - 24, top + 106, b.get('label', ''), 17, c.muted, 600, anchor='end'))
    return 150


BLOCKS = {'bookshelf': bookshelf}
```

## 检查

```bash
python3 scripts/lifeline.py build person.json -o person.svg --strict
python3 scripts/preview.py person.svg -o preview -t 1,4 --screens 7
```

`--screens` 只出指定的几屏（0 是封面），改插件时省时间。第 1 秒那张看动画刚开始的样子，第 4 秒那张看基本到位的样子：字有没有压到图形、深色屏上颜色看不看得清、短线是否接到主线上。
