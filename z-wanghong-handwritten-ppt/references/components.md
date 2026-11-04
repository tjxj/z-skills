# 组件手册

画布固定 1920×1080，单位都按这个尺寸写；放映时整体等比缩放。所有组件都在 `assets/template.css`，手绘线条和动画由 `assets/runtime.js` 在打开时生成。

## 页面骨架

```html
<section class="slide" data-title="短名（总览、演讲者视图用）">
  <h2 class="lead">标题句</h2>
  <div class="body">…</div>
  <aside class="notes">讲稿</aside>
</section>
```

| 类 / 属性 | 作用 |
|---|---|
| `.body` | 正文区。默认放在标题下方 1:2 的位置，子元素间距 34px（`style="--gap: 24px"` 可改） |
| `.body.top` | 正文紧贴标题（内容多时用） |
| `.body.center` | 正文垂直居中 |
| `.slide.no-tilt` | 整页不加手写倾斜 |
| `data-auto` | 逐步版中整页自动写完，不分步 |

## 文字

| 写法 | 效果 |
|---|---|
| `p.line` / `p` | 正文行 40px |
| `.big` / `.small` / `.cap` | 56px / 32px / 24px 灰色说明 |
| `.blue` `.red` `.green` `.purple` `.muted` `.ink` | 文字颜色 |
| `.indent` | 缩进一级（补充说明） |
| `.center-x` / `.right-x` | 该行居中 / 靠右 |
| `.formula` | 蓝色公式字，44px |
| `.arrow` | 行内蓝色箭头（用 `→` `←` `↑` `↓`；`⇒` `⇄` `↔` 两种手写字体都没有） |
| `ul` / `ol` | 列表，每项是逐步版的一步 |
| `pre.tree` | 目录树（深蓝） |
| `pre.code` | 命令 / 代码（蓝色） |

## 标记

| 写法 | 效果 |
|---|---|
| `.ul` `.ul-blue` `.ul-green` `.ul-ink` | 手画短下划线 |
| `.box` `.box-blue` `.box-green` `.box-ink` | 四角出头的细框；加 `.block` 独占一行 |
| `.circle` `.circle-blue` `.circle-green` `.circle-ink` | 不闭合的椭圆圈 |
| `.hl-yellow` `.hl-green` `.hl-coral` | 荧光笔（逐步版从左向右扫过） |
| `.dot-yellow` `.dot-green` `.dot-coral` | 符号 / 数字后面的圆点 |
| `p.takeaway` | 一页结论的绿色荧光带；加 `.center-x` 居中 |
| `.strike` | 手画删除线，文字变灰 |
| `<span class="warn"></span>` | 红色警示三角，放在红字前 |
| `.shot` | 截图外的浅灰细框（包住 `img`） |

### 箭头标注

给任意元素加 `data-note`：

```html
<p class="line" data-note="真正的痛点" data-dir="e">越急越找不到</p>
```

| 属性 | 取值 |
|---|---|
| `data-note` | 短注，一到六个字最好；`\n` 换行 |
| `data-dir` | 标注在目标的哪一侧：`n` `ne` `e` `se` `s` `sw` `w` `nw`，默认 `e` |
| `data-color` | `red`（默认）`blue` `green` `ink` |
| `data-len` | 箭头长度，默认 76 |

放不下时会自动翻到对侧并夹回安全区；检查器会报告“标注被挤回画面”和“标注压住文字 / 图片”。

## 版式

### 多栏

```html
<div class="cols" style="--cols: 1fr 1.2fr; --gap: 80px">
  <div class="col">…几行文字…</div>
  <figure class="fig">…</figure>
</div>
```

`.cols.top` 顶部对齐（默认垂直居中）。`.col` / `.stack` 是竖排容器，`.row` 是横排容器，都支持 `--gap`。

### 流程

```html
<div class="flow">
  <span class="box-ink">装技能</span><span class="arrow">→</span>
  <span class="box-ink">连文档</span><span class="arrow">→</span>
  <span class="box">接微信</span>
</div>
```

### 图片与截图

```html
<figure class="fig" style="--img-h: 560px">
  <span class="shot"><img src="img/05.png" alt=""></span>
  <figcaption class="cap">一行说明</figcaption>
</figure>
```

`--img-h` 控制最大高度（默认 620px）。几张图并排用 `<div class="figs">` 包住多个 `.fig`。检查器会提示图片被放大超过 1.25 倍（发虚）或加载失败。

### 词语思维导图

```html
<div class="map" style="--map-h: 660px">
  <div class="node big" id="m-core" style="left:50%; top:46%"><span class="dot-yellow">核心</span></div>
  <div class="node" id="m-a" style="left:18%; top:18%">记录</div>
  <div class="node blue" id="m-b" style="left:82%; top:82%">查询</div>
  <i class="link" data-from="#m-core" data-to="#m-a"></i>
  <i class="link blue" data-from="#m-core" data-to="#m-b" data-arrow></i>
</div>
```

| 属性 | 作用 |
|---|---|
| `.node` + `left/top` 百分比 | 词的中心位置 |
| `.link` `.link.red/.blue/.green` | 连线颜色 |
| `data-from` / `data-to` | 两端节点的选择器，线会停在文字外缘 |
| `data-arrow` | 末端加箭头 |
| `data-bend` | 弯曲程度（像素，可负），默认随机轻微弯曲 |
| `data-gap` | 线端离文字的距离，默认 12 |

### 手写表格

```html
<table class="hand-table center-x">
  <thead><tr><th>做法</th><th>记录</th></tr></thead>
  <tbody>
    <tr><td>纸质本子</td><td>快</td></tr>
    <tr class="pick"><td>对话式</td><td>最快</td></tr>
  </tbody>
</table>
```

只有横线，表头蓝色，`.pick` 行铺绿荧光。逐步版里一行是一步；加 `data-whole` 整表一次出现。

### 手绘图

```html
<svg class="diagram" viewBox="0 0 720 480" width="720" height="480">
  <path class="s" d="M60 420 L 700 420 M60 440 L 60 30"/>
  <path class="s-blue" d="M80 400 C 300 380, 420 200, 680 80"/>
  <circle class="s-red" cx="420" cy="230" r="14"/>
  <text x="440" y="220" font-size="30" fill="#d7303b">拐点</text>
</svg>
```

描边类：`.s`（深蓝）`.s-blue` `.s-red` `.s-green` `.s-purple` `.s-muted`。逐步版里路径按顺序画出，文字随后写出。`text` 自动用手写字体，字号不小于 24。

## 封面与结束页

```html
<section class="slide cover" data-title="封面">
  <h1 class="title">标题</h1>
  <div class="cover-art"><img src="img/cover.png" alt=""></div>
  <div class="cover-meta"><div>作者</div><div>机构 · 日期</div></div>
</section>

<section class="slide end" data-title="结束">
  <p class="big">一句话收尾</p>
  <p class="small muted">谢谢</p>
</section>
```

`.cover-art` 里可以放 `img` 或 `svg.diagram`，图片最大 1100×520。

## 逐步书写版的分步规则

- 自动拆分：`.body`、`.cols`、`.col`、`.stack`、`.row`、`.figs`、`.flow`、`.map`、`ul/ol` 会被展开，里面的每个段落、列表项、图片、表格行各占一步。
- `.arrow` 和它后面的元素合成一步。
- 连线和它 `data-to` 指向的节点合成一步（先画线，再写字）。
- `data-step="n"`：同一页里写了相同数字的元素（连同它们的子元素）合成一步；这些步按数字从小到大依次占据它们在页面中的原位置，没写的元素照常各自成步。
- `data-whole`：容器整体一次出现，不再拆分。
- 每一步里的动画顺序：图片淡入 → 图形描线 → 连线 → 文字逐行写出 → 荧光扫过 → 框线圈画出 → 箭头标注。

## 打开方式（URL 参数）

| 地址 | 用途 |
|---|---|
| `index.html#/5` | 打开第 5 页 |
| `index.html?export#/5` | 无界面的第 5 页（截图用） |
| `index.html?sheet` | 全部页面缩略图总览 |
| `index.html?audit` | 运行排版检查（`check_deck.py` 调用） |

脚本里可用 `window.WH`：`WH.show(n)`、`WH.next()`、`WH.prev()`、`WH.index()`、`WH.step()`、`WH.steps()`、`WH.finish()`、`WH.isAnimating()`、`WH.audit()`。
