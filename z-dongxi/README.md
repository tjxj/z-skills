<div align="center">

# 「动」悉万物 · z-dongxi

**一段内容进去，一张会动的解析图出来**

13 种图型 × 12 种风格 · 单行内联 SVG · 直接粘进公众号 · 也能导出 PNG / GIF / MP4

<img src="demos/svg/rag.svg" width="420">

</div>

## 它能做什么

把「有过程」的内容演出来：数据怎么流、请求怎么穿透、状态怎么跳、钱怎么省、人怎么漏、消息怎么扩散。

- **给主题和内容就行**：图型、风格、布局、动画节奏都自动定，使用者不碰坐标
- **技术和非技术都能讲**：RAG、HTTPS、MoE，也能讲手冲咖啡、碳循环、电商漏斗
- **公众号原生可用**：只用公众号支持的 SMIL 动画，不用 id / defs / style / script，单行输出，粘贴即用
- **静态即终态**：不播放动画时也是一张完整的图，截图、导出 PNG 都能用
- **自带质检**：lint 查兼容性，截帧看每一秒画面对不对
- **一键转视频**：导出 1080×1440 的 MP4，发视频号、小红书

## 示例

> GitHub 上直接显示动画；点开单张看大图。所有 spec 在 [`demos/specs/`](demos/specs)。

| <img src="demos/svg/rag.svg" width="360"> | <img src="demos/svg/rag-sketch.svg" width="360"> |
|:---:|:---:|
| **RAG 全流程**<br>`pipeline` × `swiss`<br>离线建库与在线问答两条线，向量库接到检索 | **RAG 为什么要先翻书**<br>`flow` × `sketch`<br>同一个问题，演两遍：先演幻觉，再演 RAG |
| <img src="demos/svg/https.svg" width="360"> | <img src="demos/svg/agent-loop.svg" width="360"> |
| **HTTPS 握手**<br>`sequence` × `blueprint`<br>三方消息一条条发出，激活条跟着走 | **Agent ReAct 循环**<br>`cycle` × `terminal`<br>绕三圈，中间计数从 2 failed 到全部通过 |
| <img src="demos/svg/order-state.svg" width="360"> | <img src="demos/svg/coffee.svg" width="360"> |
| **订单状态机**<br>`state` × `field`<br>订单沿着状态一路走，退款后关闭 | **从豆到杯**<br>`pipeline` × `kraft`<br>非技术话题：手冲咖啡的六道工序 |
| <img src="demos/svg/funnel.svg" width="360"> | <img src="demos/svg/cost-race.svg" width="360"> |
| **电商漏斗**<br>`funnel` × `riso`<br>一万个粒子往下掉，被筛掉的从两边漏出 | **1 亿 token 成本赛跑**<br>`race` × `editorial`<br>三根条同时起跑，最便宜的最先停 |
| <img src="demos/svg/ai-timeline.svg" width="360"> | <img src="demos/svg/mindmap.svg" width="360"> |
| **大模型十年**<br>`timeline` × `inkwash`<br>时间轴从上往下画，节点逐个亮起 | **AI 应用开发学习路线**<br>`tree` × `sketch`<br>思维导图一层层长出来 |
| <img src="demos/svg/rumor.svg" width="360"> | <img src="demos/svg/compound.svg" width="360"> |
| **谣言三轮传播**<br>`network` × `neon`<br>圆环一圈圈扩散，右上角计数跳动 | **复利定投 30 年**<br>`bars` × `porcelain`<br>柱子依次长高，最后一根落定结论 |
| <img src="demos/svg/infer-stack.svg" width="360"> | <img src="demos/svg/photosynthesis.svg" width="360"> |
| **推理栈穿透**<br>`layers` × `blueprint`<br>Prompt 一层层下到 GPU，Token 原路返回 | **碳循环**<br>`cycle` × `chalk`<br>黑板上的生物课，绕两圈 |
| <img src="demos/svg/versus.svg" width="360"> | <img src="demos/svg/moe.svg" width="360"> |
| **周报从 2 小时到 6 分钟**<br>`versus` × `swiss`<br>左右两条进度同时跑，右边早早完成 | **MoE 混合专家路由**<br>`flow` × `neon`<br>同一个词先后点亮两个专家 |

## 12 种风格

同一份 RAG spec，只改 `style`：

<img src="docs/styles-grid.png" width="100%">

| 风格 | 中文 | 适合 |
|---|---|---|
| `swiss` | 瑞士网格 | 技术长文默认款 |
| `sketch` | 白板手绘（Excalidraw 风） | 科普、入门、头脑风暴 |
| `blueprint` | 工程蓝图 | 协议、硬件、分层结构 |
| `terminal` | 终端绿屏 | Agent、CLI、安全 |
| `riso` | 孔版印刷 | 营销、增长、电商 |
| `editorial` | 杂志社论 | 观点、行业、对比 |
| `field` | 现场手册 | SOP、规程、状态机 |
| `neon` | 霓虹夜 | 传播、网络、AI |
| `porcelain` | 杂志瓷蓝 | 金融、理财、数据 |
| `chalk` | 黑板粉笔 | 课堂、生物、物理 |
| `inkwash` | 水墨朱印 | 国风、历史、文化 |
| `kraft` | 牛皮纸便签 | 生活、小店、非技术 |

## 13 种图型

先问「这段内容里什么在动」，再选图型：

| 什么在动 | 图型 | 相当于 Mermaid 的 |
|---|---|---|
| 步骤推进，有分叉 | `flow` 动态流程图 | flowchart |
| 角色间来回发消息 | `sequence` 动态时序图 | sequenceDiagram |
| 对象在状态间跳转 | `state` 状态机 | stateDiagram |
| 数据一节节被加工 | `pipeline` 数据管线（支持双线） | flowchart LR |
| 请求逐层穿透 | `layers` 分层穿透 | block |
| 循环迭代 | `cycle` 闭环飞轮 | — |
| 比快慢、比花费 | `race` 对比赛跑 | xychart |
| 按时间发生 | `timeline` 时间线 | timeline |
| 层层筛选 | `funnel` 漏斗 | — |
| 主题逐层展开 | `tree` 思维导图 | mindmap |
| 数值增长 | `bars` 柱线增长 | xychart |
| 从一点扩散 | `network` 网络扩散 | — |
| 改造前后对比 | `versus` 前后对比 | — |

都不合适时有自定义模式，用同一套画笔手写，见 [references/custom.md](references/custom.md)。

## 安装

```bash
npx skills add tjxj/z-skills --skill z-dongxi
```

依赖：Python 3.9+；导出 PNG 需要 `rsvg-convert`（`brew install librsvg`）；截帧和视频需要 `playwright`（`pip install playwright && playwright install chromium`）、`Pillow`、`ffmpeg`。

## 用法

在 Claude Code / Codex 等支持 skill 的 Agent 里直接说：

> 用动悉万物给我画一张图，解释 RAG 的完整流程
>
> 把这段 HTTPS 握手的描述做成动态时序图，蓝图风
>
> 这篇讲电商转化的文章，帮我配一张会动的漏斗图

Agent 会选图型、写 spec、渲染、lint、截帧自检。也可以手动跑：

```bash
python3 scripts/render.py --spec demos/specs/rag.json --out rag.svg --png rag.png
python3 scripts/render.py --spec demos/specs/rag.json --style sketch --out rag-sketch.svg
python3 scripts/lint.py rag.svg
python3 scripts/capture.py rag.svg --sheet sheet.png      # 8 帧联系表
python3 scripts/capture.py rag.svg --mp4 rag.mp4          # 1080×1440 视频
python3 scripts/render.py --list                          # 列出图型与风格
```

最小 spec：

```json
{"type": "cycle", "style": "auto", "title": "Agent 干活的循环",
 "steps": [{"title": "想"}, {"title": "做"}, {"title": "看"}]}
```

## 适用边界

适合：有先后、因果、流动、数量变化的内容。
不适合：纯分类列表、精确数据表、超过 9 个节点的大架构、需要点击交互的图。

## 致谢

风格体系与分级 lint 的思路受 [Nutlope/hallmark](https://github.com/Nutlope/hallmark) 启发；手绘风格致敬 [Excalidraw](https://excalidraw.com)。
