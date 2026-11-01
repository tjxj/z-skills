# 13 种图型：选型表与 spec 字段

先问一句：**这段内容里，什么东西在动？** 动的东西决定图型。

| 内容里在动的东西 | 图型 | 对应 Mermaid | 典型题材 |
|---|---|---|---|
| 一件事按步骤走，有分叉、有回头 | `flow` 动态流程图 | flowchart | 审批流程、算法判断、MoE 路由 |
| 几个角色之间来回发消息 | `sequence` 动态时序图 | sequenceDiagram | HTTPS 握手、OAuth 登录、API 调用链 |
| 一个对象在几种状态间跳转 | `state` 状态机 | stateDiagram | 订单状态、工单流转、TCP 连接 |
| 数据一节节被加工，可以有两条并行线 | `pipeline` 数据管线 | flowchart LR | RAG、ETL、视频生产线、咖啡从豆到杯 |
| 请求逐层穿透，再原路返回或被拦截 | `layers` 分层穿透 | block | 推理栈、OSI、网关鉴权、防火墙 |
| 循环往复、越转越好 | `cycle` 闭环飞轮 | — | Agent ReAct、增长飞轮、碳循环 |
| 几个方案比快慢、比花费 | `race` 对比赛跑 | xychart | 成本对比、速度评测、回本周期 |
| 按时间顺序发生的事件 | `timeline` 时间线 | timeline | 行业编年、项目里程碑、版本史 |
| 一层层筛掉、越来越少 | `funnel` 漏斗筛选 | — | 电商转化、招聘漏斗、检索召回 |
| 一个主题逐层展开 | `tree` 思维导图 | mindmap | 学习路线、知识框架、产品功能树 |
| 数值随时间变化 | `bars` 柱线增长 | xychart | 复利、用户增长、跑分 |
| 从一点向外扩散 | `network` 网络扩散 | — | 谣言传播、病毒式增长、依赖传染 |
| 改造前后两套流程比效率 | `versus` 前后对比 | — | ROI 展示、AI 落地前后、新旧方案 |

拿不准就选 `flow`。Mermaid 的 gantt / pie / er / class 图本身没有「过程」，硬做成动图没意义，见 SKILL.md 的「不适合」。

## 公共字段

```json
{"type":"pipeline","style":"auto","kicker":"小字眉题","title":"主标题，一句话说清讲什么",
 "subtitle":"副标题，可选","foot":"页脚一句话，可选","seal":"印章/图号，可选"}
```

- `style`：12 种风格名之一，或 `auto`（按标题关键词自动选）
- 所有文字字段都可以是中文，宽度自动折行；标题超过 2 行会被截断，所以要短

## 各图型字段

**flow**
- `nodes`: `[{id,title,sub?,role?,shape?:"box|diamond|db",rank?,x?}]`，rank 为第几行（不写自动按边推断），x 为 0~1 的水平位置
- `edges`: `[{from,to,label?,dashed?}]`，形成环的边自动画成回头线
- `play`: 演哪几条路径，`[{path:[id...],note?,color?:"accent|bad|good|accent2"}]`，最后一条停住作为终态

**sequence**
- `actors`: `[{id,title}]`，最多 4 个
- `messages`: `[{from,to,text,note?,reply?}]`，from==to 画自调用，最多约 8 条

**state**
- `states`: `[{id,title,sub?,kind?:"start|end",role?,pos?:[x,y]}]`，默认绕椭圆排开
- `transitions`: `[{from,to,label?,dashed?}]`
- `walk`: 演示时依次走过的状态 id；`center`: 圆心小字

**pipeline**
- 单线：`stages`；双线：`lanes:[{name,stages}]`
- stage：`{id,title,sub?,glyph?,role?,row?}`，glyph 是沿线流动的小标签（如 DOC、VEC、Q）
- `links`: 跨线连接 `[{from,to,label?,dashed?}]`；`sequential:false` 让两条线同时跑

**layers**
- `layers`: `[{title,sub?,chips?:[...],role?}]`，从上到下
- `trace`: `down` 或 `roundtrip`；`stop`: 在第几层被拦截（0 起），`stop_label`；`glyph` / `back_glyph`

**cycle**
- `steps`: `[{title,sub?}]`，3~7 个
- `center`: `{title,sub,values?:[每轮显示的文字],counter?:"第{n}轮"}`；`rounds`: 转几圈

**race**
- `items`: `[{name,value,note?,label?,hl?}]`；`better`: `lower`（越少越好）或 `higher`
- `unit`、`badge`（终点大字结论）、`meter`（右上角计数器格式，如 "已花 {v}"）

**timeline**
- `events`: `[{time,title,sub?,hl?}]`，4~7 个最好看

**funnel**
- `stages`: `[{title,value,note?,label?}]`，value 递减；`unit`；`particles`: 粒子数

**tree**
- `root`: `{title}`；`children`: `[{title,hl?,children:[{title}]}]`，一级 2~4 个，二级每支最多 5 个

**bars**
- `series`: `[{label,value,hl?,text?}]`；`kind`: `bar` 或 `line`；`unit`、`y_label`、`note`、`max`

**network**
- `waves`: `[[源头],[第一圈...],[第二圈...]]`；`counts`: 每一圈后的累计值；`counter`: "已覆盖 {v}"

**versus**
- `left` / `right`: `{title,sub?,steps:[...],total}`；`slow_dur`、`speed_ratio`（右边比左边快多少）、`badge`
