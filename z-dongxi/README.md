<div align="center">

# 「动」悉万物 · z-dongxi

**一段内容进去，一张会动的解析图出来**

31 种图型 × 25 种风格 × 5 种画幅 · 单行内联 SVG · 直接粘进公众号 · 也能导出 PNG / GIF / MP4

<img src="demos/svg/rag.svg" width="300"> <img src="demos/svg/traffic-sankey.svg" width="300"> <img src="demos/svg/launch-stat.svg" width="300">

</div>

## 它能做什么

把「有过程、有数字」的内容演出来：数据怎么流、请求怎么穿透、钱花在哪、流量去了哪、排期卡在哪、哪个方案更划算。

- **一句话就能出图**：说主题和内容，图型、风格、画幅、动画节奏都自动定，使用者不碰坐标
- **31 种图型**：13 种过程类（流程、时序、状态机、管线……）+ 18 种数据与结构类（环形、甘特、桑基、雷达、ER、热力格……），Mermaid 常用的图基本都有动态版
- **25 种风格**：瑞士网格、Excalidraw 白板手绘、工程蓝图、终端绿屏、暗夜产品、国际海报、新粗野、水墨朱印……同一份内容换一个词就换一身衣服
- **5 种画幅**：3:4 公众号（默认）、9:16 竖屏、1:1 方图、4:3 PPT、16:9 横屏视频，换画幅不用改内容
- **公众号原生可用**：只用公众号支持的 SMIL 动画，不用 id / defs / style / script，单行输出，粘贴即用
- **静态即终态**：不播放动画时也是一张完整的图，截图、导出 PNG 都能用
- **自带质检**：lint 查兼容性，截帧看每一秒画面对不对
- **一键转视频**：导出 MP4，宽 1080，高跟着画幅走

## 31 种图型一览

<img src="docs/types-grid.jpg" width="100%">

## 示例 · 过程类

> GitHub 上直接显示动画；点开单张看大图。所有 spec 在 [`demos/specs/`](demos/specs)。

| | | |
|:---:|:---:|:---:|
| <img src="demos/svg/rag.svg" width="260"> | <img src="demos/svg/rag-sketch.svg" width="260"> | <img src="demos/svg/https.svg" width="260"> |
| **RAG 一次问答，数据走了哪几步**<br>`pipeline` × `swiss`<br>离线建库与在线问答两条线，向量库接到检索 | **大模型为什么要先“翻书”再回答**<br>`flow` × `sketch`<br>同一个问题演两遍：先演幻觉，再演 RAG | **HTTPS 握手：一来一回就加密好了**<br>`sequence` × `blueprint`<br>三方消息一条条发出，激活条跟着走 |
| <img src="demos/svg/agent-loop.svg" width="260"> | <img src="demos/svg/order-state.svg" width="260"> | <img src="demos/svg/infer-stack.svg" width="260"> |
| **Agent 干活的循环：想、做、看**<br>`cycle` × `terminal`<br>绕三圈，中间计数从 2 failed 到全部通过 | **一个订单，一生会经过哪些状态**<br>`state` × `field`<br>订单沿着状态一路走，退款后关闭 | **你发一句话，穿过了几层软件**<br>`layers` × `blueprint`<br>Prompt 一层层下到 GPU，Token 原路返回 |
| <img src="demos/svg/moe.svg" width="260"> | <img src="demos/svg/coffee.svg" width="260"> | <img src="demos/svg/funnel.svg" width="260"> |
| **混合专家：每个词只叫醒两个专家**<br>`flow` × `neon`<br>同一个词先后点亮两个专家 | **一杯手冲咖啡，要经过几双手**<br>`pipeline` × `kraft`<br>非技术话题：手冲咖啡的六道工序 | **一万人点进来，最后几个人付钱**<br>`funnel` × `riso`<br>一万个粒子往下掉，被筛掉的从两边漏出 |
| <img src="demos/svg/cost-race.svg" width="260"> | <img src="demos/svg/ai-timeline.svg" width="260"> | <img src="demos/svg/mindmap.svg" width="260"> |
| **跑完 1 亿 token，哪种方案先回本**<br>`race` × `editorial`<br>三根条同时起跑，最便宜的最先停 | **大模型这十年，几个关键节点**<br>`timeline` × `inkwash`<br>时间轴从上往下画，节点逐个亮起 | **想入门 AI 应用开发，学什么**<br>`tree` × `sketch`<br>思维导图一层层长出来 |
| <img src="demos/svg/rumor.svg" width="260"> | <img src="demos/svg/compound.svg" width="260"> | <img src="demos/svg/versus.svg" width="260"> |
| **一条谣言，三轮转发能到多少人**<br>`network` × `neon`<br>圆环一圈圈扩散，右上角计数跳动 | **每月定投 2000，年化 8%，会变成多少**<br>`bars` × `porcelain`<br>柱子依次长高，最后一根落定结论 | **周报从 2 小时变成 6 分钟**<br>`versus` × `swiss`<br>左右两条进度同时跑，右边早早完成 |
| <img src="demos/svg/photosynthesis.svg" width="260"> |
| **碳在地球上转一圈**<br>`cycle` × `chalk`<br>黑板上的生物课，绕两圈 |

## 示例 · 数据与结构类

| | | |
|:---:|:---:|:---:|
| <img src="demos/svg/cost-donut.svg" width="260"> | <img src="demos/svg/feature-quadrant.svg" width="260"> | <img src="demos/svg/rag-gantt.svg" width="260"> |
| **一个 AI 客服，每月的钱花在哪**<br>`donut` × `candy`<br>扇区依次画出，中心数字跳到 62% | **AI 功能这么多，先做哪个**<br>`quadrant` × `bento`<br>六个功能逐个落位，右上角那个泛起涟漪 | **两周上线一个 RAG 客服**<br>`gantt` × `linear`<br>任务条依次伸长，依赖箭头跟着连，今天线落下 |
| <img src="demos/svg/traffic-sankey.svg" width="260"> | <img src="demos/svg/hotfix-git.svg" width="260"> | <img src="demos/svg/cc-journey.svg" width="260"> |
| **1 万个访客，最后留下了谁**<br>`sankey` × `editorial`<br>1 万人分流，小圆点沿着带子跑到付费 | **线上出 bug，hotfix 怎么走**<br>`gitgraph` × `terminal`<br>从 main 拉出 hotfix，修完合回两条线 | **第一次用 AI 写代码的心情**<br>`journey` × `lavender`<br>情绪曲线跌进低谷再爬上来 |
| <img src="demos/svg/req-kanban.svg" width="260"> | <img src="demos/svg/model-radar.svg" width="260"> | <img src="demos/svg/topic-venn.svg" width="260"> |
| **一个需求，从提出到上线**<br>`kanban` × `sticker`<br>一张卡片三天走完四列 | **旗舰模型和开源小模型，差在哪**<br>`radar` × `neon`<br>两个多边形从中心胀开，长短板一眼看清 | **什么选题能写出好文章**<br>`venn` × `riso`<br>三个圈滑进来叠在一起，交集亮起 |
| <img src="demos/svg/dikw-pyramid.svg" width="260"> | <img src="demos/svg/shop-er.svg" width="260"> | <img src="demos/svg/ai-treemap.svg" width="260"> |
| **从数据到智慧，差了几层**<br>`pyramid` × `porcelain`<br>从数据一层层垒到智慧 | **一张订单背后的四张表**<br>`er` × `blueprint`<br>四张表落下，外键线连上，数据沿线跑 | **一个月 AI 订阅，钱都去哪了**<br>`treemap` × `bauhaus`<br>面积按花费依次长出来 |
| <img src="demos/svg/pay-waffle.svg" width="260"> | <img src="demos/svg/launch-stat.svg" width="260"> | <img src="demos/svg/post-heatmap.svg" width="260"> |
| **100 个试用用户，几个会付费**<br>`waffle` × `poster`<br>100 格逐格填色，7 个付费的最后亮起 | **开源项目发布第一周**<br>`stat` × `brutal`<br>四个数字从 0 跳到终值，走势线画出来 | **一周里什么时候发，阅读最高**<br>`heatmap` × `ember`<br>一周 42 个时段逐行亮起，峰值描边 |
| <img src="demos/svg/choose-table.svg" width="260"> | <img src="demos/svg/agent-steps.svg" width="260"> | <img src="demos/svg/mcp-orbit.svg" width="260"> |
| **RAG、微调、长上下文，怎么选**<br>`table` × `swiss`<br>逐行扫过，推荐列一直高亮 | **零基础做出第一个 Agent**<br>`steps` × `field`<br>大号序号一个个点亮 | **一个协议，接起了哪些东西**<br>`orbit` × `arcade`<br>内外两圈轨道，小圆点绕着 MCP 转 |

## 25 种风格

同一份 RAG spec，只改 `style`：

<img src="docs/styles-grid.jpg" width="100%">

| 浅色 · 信息图 | 深色 · 科技 | 手作 · 有温度 |
|---|---|---|
| `swiss` 瑞士网格 · 技术长文默认 | `blueprint` 工程蓝图 · 协议结构 | `sketch` 白板手绘 · Excalidraw 风 |
| `candy` 糖果技术图 · 架构图解 | `terminal` 终端绿屏 · Agent / CLI | `brutal` 新粗野 · 工具测评 |
| `editorial` 杂志社论 · 观点行业 | `linear` 暗夜产品 · 开发者工具 | `sticker` 贴纸 · 清单盘点 |
| `poster` 国际海报 · 战报宣言 | `neon` 霓虹夜 · 传播网络 | `riso` 孔版印刷 · 营销增长 |
| `newsprint` 半调报纸 · 复盘调查 | `arcade` 像素街机 · 游戏化 | `chalk` 黑板粉笔 · 课堂原理 |
| `porcelain` 杂志瓷蓝 · 金融数据 | `ember` 余烬 · 深度长文 | `notebook` 横线笔记 · 读书笔记 |
| `bento` 便当格 · 产品功能 | | `inkwash` 水墨朱印 · 国风历史 |
| `lavender` 薰衣草 · 心理成长 | | `kraft` 牛皮纸 · 生活小店 |
| `bauhaus` 包豪斯 · 设计方法论 | | `garden` 植物园 · 自然健康 |
| `field` 现场手册 · SOP 规程 | | |

## 5 种画幅

同一份 spec 加 `--ratio` 就能换画幅，布局自动重排：横版的管线会折成两行，时间线改成横向，看板和数字卡片铺满一行。

| 画幅 | 尺寸 | 用在哪 |
|---|---|---|
| `3:4` | 750×1000 | 公众号文章配图（默认） |
| `9:16` | 750×1334 | 视频号、抖音、小红书全屏 |
| `1:1` | 900×900 | 朋友圈、方图 |
| `4:3` | 1200×900 | PPT、博客 |
| `16:9` | 1280×720 | B 站、横屏视频、PPT |

<img src="docs/wide-grid.jpg" width="100%">

| <img src="demos/ratios/rag-9x16.svg" width="200"> | <img src="demos/ratios/rag-1x1.svg" width="260"> | <img src="demos/ratios/rag-4x3.svg" width="320"> |
|:---:|:---:|:---:|
| 9:16 | 1:1 | 4:3 |

## 安装

```bash
npx skills add tjxj/z-skills --skill z-dongxi
```

依赖：Python 3.9+；导出 PNG 需要 `rsvg-convert`（`brew install librsvg`）；截帧和视频需要 `playwright`（`pip install playwright && playwright install chromium`）、`Pillow`、`ffmpeg`。

## 用法

在 Claude Code / Codex 等支持 skill 的 Agent 里直接说：

> 用动悉万物给我画一张图，解释 RAG 的完整流程
>
> 把这个月的 AI 订阅开销做成会动的矩形树图，包豪斯风
>
> 这份两周排期做成动态甘特图，16:9，我要放进 PPT
>
> 这篇讲电商转化的文章，帮我配一张会动的桑基图

Agent 会选图型、写 spec、渲染、lint、截帧自检。也可以手动跑：

```bash
python3 scripts/render.py --spec demos/specs/rag.json --out rag.svg --png rag.png
python3 scripts/render.py --spec demos/specs/rag.json --style sketch --out rag-sketch.svg
python3 scripts/render.py --spec demos/specs/rag-gantt.json --ratio 16:9 --out gantt.svg
python3 scripts/lint.py rag.svg
python3 scripts/capture.py rag.svg --sheet sheet.png      # 8 帧联系表
python3 scripts/capture.py rag.svg --mp4 rag.mp4          # 视频
python3 scripts/render.py --list                          # 列出图型、风格、画幅
```

最小 spec：

```json
{"type": "donut", "title": "一个 AI 客服，每月的钱花在哪", "unit": " 元",
 "items": [{"label": "大模型 API", "value": 7400, "hl": true}, {"label": "向量库", "value": 1700}, {"label": "服务器", "value": 1500}]}
```

每种图型的字段见 [references/types.md](references/types.md)。都不合适时有自定义模式，用同一套画笔手写，见 [references/custom.md](references/custom.md)。

## 适用边界

适合：有先后、因果、流动、占比、对比、结构关系的内容。
不适合：超过 9 个主节点的大架构（拆成两张）、需要读精确数值的大表、需要点击交互的图。

## 致谢

风格体系与分级 lint 的思路受 [Nutlope/hallmark](https://github.com/Nutlope/hallmark) 启发；手绘风格致敬 [Excalidraw](https://excalidraw.com)；图型清单参考了 [Mermaid](https://mermaid.js.org)。
