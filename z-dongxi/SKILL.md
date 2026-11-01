---
name: z-dongxi
description: 「动」悉万物——把一段内容变成一张会动的解析图（单行内联 SVG，可直接粘进公众号，也能导出 PNG / GIF / MP4）。31 种图型：13 种过程类（动态流程图、时序图、状态机、数据管线、分层穿透、闭环飞轮、对比赛跑、时间线、漏斗、思维导图、柱线增长、网络扩散、前后对比）+ 18 种数据与结构类（环形占比、四象限、甘特、桑基、Git 分支图、用户旅程、看板、雷达、韦恩、金字塔、ER 图、矩形树图、华夫格、数字看板、热力格、对照表、大号步骤、生态轨道）。25 种风格（瑞士网格、糖果技术图、Excalidraw 白板手绘、工程蓝图、终端绿屏、暗夜产品、霓虹夜、像素街机、杂志社论、国际海报、半调报纸、杂志瓷蓝、余烬、新粗野、贴纸、包豪斯、孔版印刷、便当格、薰衣草、现场手册、黑板粉笔、横线笔记、水墨朱印、牛皮纸、植物园）。5 种画幅：3:4（公众号默认）、9:16、1:1、4:3、16:9。技术和非技术话题都能讲。触发词：动态图、动图解释、动态流程图、动态SVG、动态解析图、会动的图、让这张图动起来、mermaid动起来、动悉万物、「动」悉万物、excalidraw风动图、手绘动图、动态饼图、动态甘特图、动态桑基图、动态数据图。
---

# 「动」悉万物

输入一个主题和一段内容，输出一张会动的解析图。使用者不需要懂 SVG，也不需要选图型、风格和画幅。

## 工作流（照做，不要跳步）

### 1. 判断适不适合

适合：内容里有**先后顺序、因果、流动、数量变化、占比、对比、结构关系**。
不适合（直接告诉用户换静态图或表格）：
- 主节点超过 9 个的大架构图（建议拆成两张）
- 需要读精确数值的大数据表（超过 8 行 × 6 列）
- 需要点击交互的图

### 2. 一句话找出「什么在动」

写下：`这张图里，<什么东西> 从 <哪> 到 <哪>，读者看完应该明白 <一句结论>`。
读 `references/types.md` 的两张选型表，按「什么在动」选图型：
- 东西在走（步骤、消息、数据、请求）→ 过程类 13 种
- 数字和关系在长（占比、排期、流向、打分、交集、关键数字）→ 数据与结构类 18 种
拿不准选 `flow`。

### 3. 选风格和画幅

风格：用户指定了就用；没指定就 `"style":"auto"`。也可以按题材挑（见 `references/styles.md`）：
技术默认 `swiss`，架构图解 `candy`，科普入门 `sketch`，协议结构 `blueprint`，Agent/CLI `terminal`，开发者产品 `linear`，营销 `riso`，观点行业 `editorial`，战报 `poster`，SOP `field`，传播 `neon`，金融 `porcelain`，测评 `brutal`，课堂 `chalk`，国风 `inkwash`，生活 `kraft`。

画幅：公众号文章配图一律 `3:4`（默认，不用写）。其他场景按用户说的：竖屏视频、小红书全屏 `9:16`；朋友圈方图 `1:1`；PPT、博客 `4:3`；B 站、横屏视频 `16:9`。

### 4. 写 spec（JSON）

照 `references/types.md` 的字段写。要点：
- 标题一句话，18 字以内最好，必须说清这张图讲什么
- 节点标题 2~8 字，副标题写**具体例子或数字**（"每块约 500 字" 好过 "文本分块"）
- 用真实场景的数字和例子，别用 A/B/C 占位；示例数据要在 `foot` 或 `subtitle` 里注明
- 最后一个节点 / 结论用 `role:"accent"` 或 `hl:true`，让终态有焦点

保存到 `demos/specs/` 以外的工作目录，比如文章同目录下 `xxx.json`。

### 5. 渲染

```bash
python3 scripts/render.py --spec xxx.json --out xxx.svg --png xxx.png
python3 scripts/render.py --spec xxx.json --ratio 16:9 --out xxx-16x9.svg   # 换画幅
```

插进 Markdown 文章（插在指定标题下第一段之后）：

```bash
python3 scripts/render.py --spec xxx.json --insert-to 文章.md --heading "### RAG 怎么跑"
```

### 6. 检查（必须）

```bash
python3 scripts/lint.py xxx.svg            # Floor 必须全过
python3 scripts/capture.py xxx.svg --sheet sheet.png   # 看 8 帧
```

打开 PNG 和 sheet 看一遍：文字有没有溢出、挤在一起、动画顺序是否就是剧本顺序。有问题就改 spec（缩短文字、减少节点、调 rank/row）重新渲染。

### 7. 按需导出

```bash
python3 scripts/capture.py xxx.svg --mp4 xxx.mp4     # 宽 1080，高按画幅；发视频号 / 小红书 / B 站
python3 scripts/capture.py xxx.svg --gif xxx.gif     # 发群、发微博
```

## 31 种图型都不合适时

读 `references/custom.md`，用同一套画笔手写，仍然要过 lint 和截帧检查。

## 硬规矩

- 画布只用 5 种画幅之一：750×1000（3:4）、750×1334（9:16）、900×900（1:1）、1200×900（4:3）、1280×720（16:9）
- SVG 单行，无 id / defs / style / script / CSS 动画
- 静态终态必须完整可读
- 一张图最多 2 种强调色、2~3 种动作
- 不加任何署名框、底部引用框、「老章工程手记」之类的装饰
- 动作必须有含义（见 `references/motion.md`）

## 文件

```
scripts/render.py        渲染入口（--ratio 换画幅，--list 列出图型/风格/画幅）
scripts/lint.py          公众号兼容 + 反模板检查
scripts/capture.py       截帧 / 联系表 / MP4 / GIF
scripts/gallery.py       重出 demos/ 与 docs/ 图库（维护用）
scripts/dongxi/          引擎：styles.py 风格，core.py 画笔与画幅，layouts.py 过程类，charts.py 数据与结构类
references/              选型、风格、动作、自定义、设计笔记
demos/specs/             34 个示例 spec，可直接照抄改
```
