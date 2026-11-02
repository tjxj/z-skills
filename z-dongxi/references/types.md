# 35 种图型：选型表与 spec 字段

先问一句：**这段内容里，什么东西在动？** 动的东西决定图型。

## 过程类（13 种）：东西在走

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

## 数据与结构类（18 种）：数字和关系在长出来

| 内容里在动的东西 | 图型 | 对应 Mermaid | 典型题材 |
|---|---|---|---|
| 一笔钱 / 一个整体被分成几份 | `donut` 环形占比 | pie | 成本拆账、流量来源、时间分配 |
| 一堆选项按两个维度落位 | `quadrant` 四象限 | quadrantChart | 功能优先级、选型、精力管理 |
| 几件事排期，有依赖、有今天 | `gantt` 甘特排期 | gantt | 项目计划、上线排期、学习计划 |
| 一批量从几处流向几处 | `sankey` 桑基流向 | sankey | 流量去向、预算流向、能量转换 |
| 分支拉出、提交、合并 | `gitgraph` 分支图 | gitGraph | Git 工作流、版本发布、实验分支 |
| 一段体验里情绪起落 | `journey` 用户旅程 | journey | 用户体验、学习曲线、上手过程 |
| 一张卡片在几列之间推进 | `kanban` 看板流转 | kanban | 需求流转、内容生产、招聘进度 |
| 几个对象在多个维度打分 | `radar` 雷达对比 | radar | 模型选型、能力评估、产品对比 |
| 几个条件的交集 | `venn` 韦恩交集 | — | 选题、人才画像、产品定位 |
| 由下往上越来越少、越来越值钱 | `pyramid` 金字塔 | — | DIKW、需求层次、能力模型 |
| 几张表靠主外键连起来 | `er` 实体关系 | erDiagram | 数据库设计、数据模型、业务对象 |
| 面积代表大小的拆分 | `treemap` 矩形树图 | treemap | 订阅开销、代码体积、市场份额 |
| 一百个人里各占多少 | `waffle` 华夫格 | — | 转化率、留存、占比科普 |
| 几个关键数字一起跳 | `stat` 数字看板 | — | 发布战报、周报、增长复盘 |
| 两个维度交叉的强弱 | `heatmap` 热力格 | — | 发文时间、活跃时段、错误分布 |
| 几个方案逐项打勾比较 | `table` 对照表 | — | 选型对比、套餐对比、方案取舍 |
| 照着做的几步 | `steps` 大号步骤 | — | 上手教程、SOP、操作清单 |
| 一个核心外面围着一圈圈生态 | `orbit` 生态轨道 | — | 协议生态、产品矩阵、技术栈 |

## 层次与立体（4 种）：嵌套、分层、前后变化、三个维度

| 内容里在动的东西 | 图型 | 对应 Mermaid | 典型题材 |
|---|---|---|---|
| 状态里还套着状态，或者两件事同时在变；想指出哪条路违反了规则 | `statechart` 层级状态机 | stateDiagram（复合、并行） | 订单子流程、外卖配送、权限漏洞排查 |
| 一层层叠起来的系统，用立体块拆开看 | `iso` 等距堆叠 | — | 技术栈、AI 应用分层、组织结构 |
| 同一批东西前后两个时间点的数值 | `slope` 坡度图 | — | 价格涨跌、排名变化、改版前后 |
| 一堆对象同时有三个数字（横、纵、大小） | `bubble` 气泡图 | — | 模型选型、市场格局、项目投入产出 |

拿不准就选 `flow`。只想放一张纯静态的分类清单时，用表格更合适。

## 公共字段

```json
{"type":"pipeline","style":"auto","ratio":"3:4","kicker":"小字眉题","title":"主标题，一句话说清讲什么",
 "subtitle":"副标题，可选","foot":"页脚一句话，可选","seal":"印章/图号，可选","direction":"LR 或 TB，可选"}
```

- `style`：27 种风格名之一，或 `auto`（按标题关键词自动选）
- `ratio`：`3:4`（默认，公众号）/ `9:16`（竖屏视频、小红书全屏）/ `1:1`（朋友圈、方图）/ `4:3`（PPT、博客）/ `16:9`（B 站、横屏视频、PPT）。命令行 `--ratio` 优先
- `scene`：任何图型都能加，在画面底部摆一排会动的小物件，比如 `["cup","laptop","plant","walker"]`。可选 `cup` 奶茶杯（冒热气）、`pot` 茶壶、`hourglass` 沙漏（沙子跟着周期漏）、`plant` 盆栽（叶子摆）、`lamp` 台灯、`bell` 服务铃、`laptop` 笔记本（字一行行出、光标闪）、`server` 机柜（指示灯闪）、`coins` 硬币（一枚落下）、`book` 书（翻页）、`sun` 太阳、`moon` 月亮星星、`bulb` 灯泡、`cat` 猫（甩尾巴）、`walker` 走路小人（沿台面来回走）。会占掉底部约 118px，节点多时别加
- `direction`：`flow`、`pipeline`、`timeline`、`statechart` 支持。不写时竖版画幅从上往下，横版画幅从左往右
- 标题超过 2 行会被截断，所以要短；所有坐标都从画幅推出，换画幅不用改 spec

## 过程类字段

**flow**
- `nodes`: `[{id,title,sub?,role?,shape?:"box|diamond|db",rank?,x?}]`，rank 为第几层（不写自动按边推断），x 为 0~1 的位置
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
- 横版单线超过 4 节时自动折成两行蛇形

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

## 数据与结构类字段

**donut**：扇区依次画出，中间数字跳到重点项
- `items`: `[{label,value,hl?,color?}]`，3~6 项；`unit`
- `center`: `{title,text?,sub?}`，text 不写时显示 hl 项的百分比

**quadrant**：四格先铺，点一个个落位，重点点有涟漪
- `axes`: `{x:[左端,右端],y:[下端,上端],x_name?}`；`quadrants`: `[左上,右上,左下,右下]`；`best`: 高亮第几格（0 起，默认 1）
- `points`: `[{label,x,y,hl?,color?}]`，x/y 为 0~1
- `notes`: `[{title,sub?,role?}]`，横版画幅时放在右侧

**gantt**：任务条依次伸长，依赖箭头跟着连，今天线最后落下
- `tasks`: `[{name,start,end,group?,after?,label?,hl?}]`，start==end 画里程碑菱形；after 为前置任务序号或名字
- `unit`、`end`、`ticks`、`tick_labels`、`now`、`now_label`

**sankey**：带状流依次铺开，小圆点沿带子跑
- `flows`: `[{from,to,value,hl?}]`，节点按出现顺序自动分列；`unit`；`colors`: `{节点名:颜色}`

**gitgraph**：分支从主线拉出，提交逐个点亮，合并线画回去
- `branches`: `[{name,from?,color?}]`
- `commits`: `[{branch,msg,tag?,merge?:分支名,hl?}]`，按时间顺序

**journey**：情绪曲线一路画过去，每一站亮起心情标签
- `stages`: `[{title,sub?,score,feel?,hl?}]`，score 1~5（`scale` 可改上限）

**kanban**：主角卡片从第一列一路挪到最后一列
- `columns`: `[{name,cards:[文字或{title,sub}]}]`，3~5 列
- `move`: `{title,sub?,path:[列序号...],note?}`

**radar**：多边形从中心胀开
- `axes`: 维度名 4~8 个；`series`: `[{name,values,color?}]`，1~3 组；`max`；`show_values`
- `note`: `{title,sub}`，横版画幅放右下

**venn**：圆从两边滑进来叠在一起，交集处亮起
- `sets`: `[{title,sub?,color?}]`，2~3 个
- `overlaps`: `{"ab":"..","bc":"..","ac":".."}`；`center`: 三圈交集文字；`caption`

**pyramid**：从底层一级级往上垒
- `levels`: `[{title,sub?,note?,role?}]`，从上到下写，3~6 层

**er**：表一张张落下，关系线连上，小圆点沿外键跑
- `entities`: `[{id,title,fields:["id PK","user_id FK","name"],hl?,pos?:[列,行]}]`
- `relations`: `[{from,to,card?:"1:N",label?}]`；`cols`: 每行几张表

**treemap**：块按大小依次长出来
- `items`: `[{label,value,hl?,color?,text?}]`；`unit`

**waffle**：100 格一格格填色，大数字最后落定
- `parts`: `[{label,value,color?}]`，合计 100；`big`、`label`、`caption`

**stat**：数字从 0 跳到终值，迷你走势线画出来
- `items`: `[{label,value,delta?,lower_better?,spark?:[...],sub?,hl?}]`，2~6 个；`cols`

**heatmap**：格子一行行亮起，最大值描边
- `rows`、`cols`、`values`（二维数组）；`min`、`max`、`legend`、`note`、`show_values`

**table**：表头先立，行逐条扫过，推荐列高亮
- `columns`: 列名数组；`rows`: `[{label,cells:[...]}]`，cell 写 ✓ / ✕ / 部分 / 任意短文字
- `hl`: 高亮第几列；`hl_tag`；`caption`

**steps**：大号序号一个个点亮
- `steps`: `[{title,sub?,hl?}]`，3~6 步

**orbit**：环一圈圈画出，成员沿轨道落位，小圆点绕圈跑
- `center`: 中心文字；`rings`: `[{name?,items:[...]}]`，1~3 圈，每圈最多 8 个

## 层次与立体字段

**statechart**：状态逐个点亮，小圆点沿转移线走；进到复合状态时外框跟着亮；有 `bug` 时最后用红色虚线描出违规路径并盖章
- `states`: `[{id,title,sub?,parent?,initial?,region?,parallel?,kind?,role?,note?,rank?}]`
  - `parent`：写了就是子状态，画在父状态的框里；父状态自动变成复合状态
  - `parallel:true`：复合状态分成几个并行区域，子状态用 `region` 分组，区域之间画虚线
  - `initial:true`：复合状态或区域的起点，前面画实心圆
  - `kind`：`final` / `end` 画成深色，`error` 画成强调色
  - `note`：一句注解，用引线拉到页边，斜体小字；旁边没地方时自动省略
- `transitions`: `[{from,to,label?,guard?,dashed?}]`，`guard` 是守卫条件，显示成 `[条件]`；from 写复合状态表示从里面任何一步都能走
- `initial`：顶层起点，不写取第一个
- `walk`：点亮顺序，元素可以是数组（并行区域同时处于几个状态），如 `["pick",["ride","wait"],["near","call"],"done"]`
- `bug`: `{path:[id...], rule, stamp?, title?}`，`rule` 写在底部的虚线框里
- 竖版从上往下排，横版自动改成从左往右；放不下时整体等比缩小

**iso**：块从下往上依次落位，小方块从顶层一路穿到底层，经过的那层闪一下；顶层上有个小人来回走
- `layers`: `[{title,sub?,tag?,highlight?,color?}]`，从上到下写，3~6 层
- `caption`：一句引线注解，标在包裹起点旁；`walker:false` 去掉小人

**slope**：普通条目先一条条画出，重点条目最后加粗画
- `left` / `right`：两根轴的名字；`items`: `[{name,a,b,note?,color?}]`；`unit`
- `highlight`: 重点条目名字数组；`updown:true` 时涨用 good 色、跌用 bad 色；`min` / `max` 固定刻度

**bubble**：气泡从大到小依次弹出，重点气泡最后泛起涟漪
- `x` / `y`: `{label,min,max}`；`items`: `[{name,x,y,size,group?,note?,color?}]`
- `highlight`: 名字数组，带 `note` 的重点气泡会拉一条引线注解

