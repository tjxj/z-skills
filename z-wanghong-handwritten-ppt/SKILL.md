---
name: z-wanghong-handwritten-ppt
description: 把文章、讲稿或技术主题做成王虹学术报告风格的 16:9 手写 HTML 幻灯片：近白纸面、小号深蓝手写字、短红线、细红框、绿色荧光带、红色警示三角、词语思维导图和带说明的截图。一次产出可离线发送的单文件整页版、逐步书写动画版、逐页 PNG、总览图（可选 PDF），macOS / Windows / Linux 通用。触发词：王虹PPT风格、王虹手写PPT、Notability学术手写幻灯片、手写网页PPT、手写PPT、数学家手写报告风、手写PPT时间轴版、手写演示动画。
---

# 王虹学术手写风 HTML 幻灯片

目标画面：像数学家在平板上提前写好的报告页。纸面几乎纯白，字小而工整，颜色只承担逻辑，页面大量留白，每页只讲一件事。

作者只写一份 `slides.html`（纯内容 + 组件类名），其余全部由脚本完成：

```text
slides.html ──build.py──▶ index.html            整页版（翻页、总览、讲稿、演讲者视图）
                       ├▶ index-timeline.html   逐步书写版（文字逐行写出、线条逐笔画出）
                       └ 两个文件都内嵌字体子集、样式、运行时和图片，单文件可直接发送
index.html ──render.py──▶ png/01.png… + contact-sheet.png（+ deck.pdf）
任意一份 ──check_deck.py──▶ 真实浏览器逐页量排版，有错误退出码 1
```

## 开工前读

1. 用户给的文章、讲稿、数据和图片。
2. `references/style-guide.md`：根据王虹真实报告照片拆出来的视觉规则（必读）。
3. `references/components.md`：全部组件写法和属性。
4. 从 `templates/slides.html` 复制一份开始写；成品参考 `examples/deepseek-v4-flash/`。

## 工作流程

### 1. 定故事线

从原文提取：总问题 → 背景 → 3 到 6 个核心判断 → 支撑每个判断的数据、对比、流程、截图 → 最后一句话。拆成 10 到 24 页。

- 每页一个问题，标题就是这句话（`h2.lead`），像笔记开头的一句话，不加横线。
- 正文 2 到 5 行，单页正文不超过约 120 字；检查器超过 220 字会报警。
- 复杂信息换成图：流程（`.flow`）、词语思维导图（`.map`）、手写表格（`.hand-table`）、手绘坐标（`svg.diagram`）、截图（`.fig` / `.shot`）。
- 原文的图片优先用上，截图配一行小字说明（`figcaption.cap`）。

### 2. 写 slides.html

骨架固定：

```html
<main class="deck">
  <section class="slide cover" data-title="封面">
    <h1 class="title">标题</h1>
    <div class="cover-art"><img src="img/cover.png" alt=""></div>
    <div class="cover-meta"><div>作者</div><div>机构 / 场合 · 日期</div></div>
    <aside class="notes">讲稿</aside>
  </section>

  <section class="slide" data-title="短名">
    <h2 class="lead">这一页回答的问题</h2>
    <div class="body">
      <p class="line">一行手写<span class="ul">短红线</span></p>
    </div>
    <aside class="notes">一到三句讲稿。</aside>
  </section>
</main>
```

规则：

- 每页都有 `data-title` 和 `aside.notes`。
- 不手写 `<script>`、`@font-face`、`font-family`；字体与运行时由 build.py 注入。
- 本稿专属微调写在 `<head><style>` 里，用模板变量（`var(--red)` 等），不改 `assets/`。
- 图片放 `img/` 相对引用；网络图片 build 时会自动下载内嵌。
- 不写页眉、页脚、页码、logo、卡片阴影、渐变、圆角色块、emoji 图标。

标记用法（颜色有固定含义，详见 style-guide）：

| 想表达 | 写法 |
|---|---|
| 关键词 | `<span class="ul">词</span>` 短红线；蓝线 `.ul-blue` |
| 公式 / 定义 / 推荐项 | `<span class="box">…</span>`，块级加 `.block` |
| 一页结论 | `<p class="takeaway">…</p>` 绿色荧光带 |
| 点名一个符号或数字 | `<span class="dot-yellow">x</span>` / `.dot-green` |
| 圈出一个词 | `<span class="circle">词</span>` |
| 例外 / 被否定的做法 | `<span class="strike">旧做法</span>` |
| 风险 | `<p class="line red"><span class="warn"></span>风险说明</p>` |
| 指向说明 | `data-note="短注" data-dir="e"`（n ne e se s sw w nw） |

一页最多两种强调，一页最多一个 `.takeaway`。

### 3. 构建

```bash
python3 scripts/build.py path/to/slides.html
```

Windows 用 `py scripts\build.py path\to\slides.html`（或 `python`）。常用参数：

- `--font auto|hanzipen|xiaolai|<字体文件>`：默认 auto。macOS 有“翩翩体-简”（HanziPen SC，字体册可下载）就用它，否则用随附的开源小赖字体（Windows / Linux 自动走这条）。
- `--no-timeline`：只要整页版。
- `--out-dir DIR`：输出到别处（默认与 slides.html 同目录）。
- `--max-image 1800`：图片长边上限；装了 Pillow 会自动缩放并转 WebP。

装了 `fontTools`（`pip install fonttools brotli`）会按本稿实际用字裁剪字体，单文件通常只有几百 KB；没装也能用，只是文件更大。

### 4. 检查（必须）

```bash
python3 scripts/check_deck.py path/to/index.html
```

在 1920×1080 画布上逐页实测：越界与贴边、内容溢出、字号过小、文字与标注重叠、标注压图、图片加载失败或被放大发虚、页面中段空洞、内容全挤在上半页、末行孤字、单页字数、讲稿缺失、字体缺字。错误必须改到 0；警告逐条看，确认可以接受才保留。也可直接检查 slides.html（会先临时构建）。

### 5. 导出并实际看图

```bash
python3 scripts/render.py path/to/index.html          # png/ + contact-sheet.png
python3 scripts/render.py path/to/index.html --pdf    # 另出 deck.pdf
```

需要 Chrome 或 Edge；找不到时用 `--chrome 路径` 或环境变量 `WH_CHROME`。逐张打开 PNG 和总览图看：

- 留白是否舒展，内容重心是否落在画面上中部
- 强调是否克制，红色是否只给真正的重点
- 截图是否清楚，说明文字是否在图下
- 整套连起来看是否一条逻辑链

改 slides.html → 重新 build → check → render，直到满意。

### 6. 交付

```text
<主题>-handwritten-ppt/
  slides.html            源稿（以后改这里）
  img/                   原始图片
  index.html             整页版（单文件，可直接发送）
  index-timeline.html    逐步书写版（单文件）
  png/01.png …           逐页图片
  contact-sheet.png      总览图
  deck.pdf               （可选）
```

告诉用户两个 HTML 的操作：

- 翻页 → / 空格 / 点击；逐步版每按一次写出下一步，动画中再按一次立即写完。
- O 总览、N 讲稿、S 演讲者视图（双屏，含下一页预览和计时）、P 自动播放、B / W 黑白屏、F 全屏、T 在两个版本间切换、? 全部快捷键。
- 地址末尾 `#/5` 直达第 5 页；手机和平板可左右滑动。

## 随附内容

- `templates/slides.html`：9 种页型的起步模板
- `assets/template.css`：画布、排版与全部组件样式
- `assets/runtime.js`：手绘标记、连线、箭头标注、逐步书写动画、演示界面、导出与排版检查
- `assets/fonts/`：小赖字体 GB2312 子集（SIL OFL 1.1，见 `OFL.txt`）
- `scripts/build.py`：构建单文件 HTML
- `scripts/check_deck.py`：静态 + 浏览器排版检查
- `scripts/render.py`：PNG / 总览图 / PDF
- `references/style-guide.md`：视觉规则；`references/components.md`：组件手册；`references/prompts.md`：生成图片版页面的提示词
- `examples/deepseek-v4-flash/`：19 页完整示例
- `tests/`：`python3 -m unittest discover -s tests`
