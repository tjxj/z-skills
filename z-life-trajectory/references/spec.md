# spec 字段

一份 spec 是一个 JSON 文件：封面 + 若干内容屏，每屏是一串从上往下排的块。完整例子见 `examples/jensen-huang.json`。

## 顶层

| 字段 | 说明 |
|---|---|
| `person` | 人物名，只做记录 |
| `theme` | `terra`（默认）/ `indigo` / `jade` / `crimson` |
| `colors` | 覆盖主题里的颜色，如 `{"ACCENT": "#B5452F"}`。可改的键见 `lifeline.py` 里的 `THEMES` |
| `font` | 量字宽用的字体文件。默认依次找思源宋体、Noto Serif CJK、宋体 |
| `plugins` | 定制插画块的 .py 文件列表，路径相对 spec 所在目录 |
| `forbid` | 禁用词列表，生成的 SVG 里出现就报错 |
| `sources` | 资料来源，一行，40 字以内，显示在最后一屏底部 |
| `cover` | 封面，见下 |
| `screens` | 内容屏列表，见下 |

## 封面 `cover`

```json
"cover": {
  "news": {"date": "2026.11.12", "text": "英伟达官宣：黄仁勋辞去总裁、CEO 及董事职务"},
  "kicker": "执掌英伟达", "big": "33", "big_unit": "年",
  "name": "黄仁勋", "subtitle": "的人生轨迹", "years": "1963—2026",
  "route": "台南 → 曼谷 → 肯塔基 → 俄勒冈 → 硅谷",
  "map_title": "人生线路图", "map_note": "15 站 · 63 年",
  "stops": [{"year": "1963", "label": "出生"}, {"year": "1993", "label": "创立英伟达", "kind": "major"}],
  "hint": "往下，逐站细看"
}
```

| 字段 | 说明 |
|---|---|
| `news` | 顶部深色新闻条 `{date, text}`，没有由头就不写 |
| `name` / `subtitle` | 大字人名和下面一行（默认「的人生轨迹」）。人名太长会自动缩字号，也可用 `name_size` 指定 |
| `kicker` / `big` / `big_unit` | 右上角的大数字和它的前缀、单位，比如「执掌英伟达 33 年」。`big_size` 可指定字号；人名放不下时大数字也会略缩，最小 96 |
| `years` | 生卒年或起止年 |
| `route` | 一生走过的地方，用 → 连接 |
| `map_title` / `map_note` | 线路图标题和右侧小字 |
| `stops` | 线路图上的站，最多 15 个。`kind`: `start` 起点 / `major` 大站 / `end` 终点（首尾不写也会自动处理）。站名 5 字左右 |
| `cols` | 每行几站，默认 9 站以上 5 列，否则 4 列 |
| `hint` | 右下角提示 |
| `hold` | 只影响视频：封面停留秒数 |

线路图是蛇形的：第一行从左到右，第二行从右到左，以此类推，一辆小车沿线一直跑。

## 内容屏 `screens[i]`

| 字段 | 说明 |
|---|---|
| `era` | 左上角的时期，如 `1985 — 1992`、`1973 — 1975 · 肯塔基` |
| `title` | 大标题，12 字内（超了自动缩字号，最小 40） |
| `sub` | 标题下一行细节，24 字内 |
| `dark` | `true` 时这一屏是深色底，全片最多用一次 |
| `blocks` | 块列表，从上往下排 |
| `hold` | 只影响视频：这屏停留秒数 |

版面会自动排：先量出每块的高度，再把剩余空间平均分到块与块之间。放不下时先压缩间距，还放不下才报 `CROWDED`。

### 所有块都能用的字段

| 字段 | 说明 |
|---|---|
| `type` | 块类型 |
| `gap` | 和上一块之间的固定间距（像素），写了就不参与自动分配 |
| `attach` + `dy` | 叠在上一块上，不占高度，`dy` 是相对上一块顶边的偏移。例：在「英伟达成立」右边放三枚 $200 |

### 文字行

凡是 `lines` / `left` / `right` / `notes` 这类文字列表，每一项可以是字符串，也可以是 `{"text": "…", "style": "bold"}`。`style` 可选 `bold`（加粗深色）、`accent`（主题色）、`faint`（浅灰）、`second`（第二主题色）。

## 22 种块

### 叙事

**`station` 站点**：主线上的一站。最常用。

```json
{"type": "station", "year": "1984", "title": "电子工程学士，以最高荣誉毕业", "kind": "major",
 "lines": ["实验课搭档 Lori Mills，后来成了他的妻子"], "icon": "cap"}
```

`year` 年份或日期；`title` 一行字符串，或字符串列表（手动分行）；`lines` 说明，最多两行；`kind`: `stop`（默认）/ `major`（大站，圆点更大并带脉冲）；`icon` + `icon_scale`（默认 0.85）在右侧放一个图标，文字会自动让出位置；`title_size` 默认 29；`marker: false` 不画主线上的圆点。

**`compact` 紧凑站**：一行年份 + 一行标题 + 最多一行说明。连续几个 `compact` 会自动对齐成一列，适合「这几年发生了很多事」。字段同 `station`（无图标）。

**`terminus` 终点**：主线到这里收住，带闪烁的终点横杠。字段同 `station`。整张图只用一次，放最后一屏。

**`card` 卡片**：左边图标、右边文字的白卡片，主线伸出一根短线接上。

```json
{"type": "card", "icon": "workstation", "icon_scale": 1.55, "icon_w": 230, "icon_label": "Sun 工作站",
 "year": "1989", "title": ["三个人一起做出", "GX 图形引擎"], "lines": ["GX 卖得非常好"], "note": "小字备注", "height": 290}
```

`icon_w` 左栏宽（默认 216）；`icon_label` 图标下的小字；`height` 最小高度；`fill` 卡片底色；`stub: false` 不画连线。

**`quote` 引语**：本人原话。`lead` 引语前的一行交代，`lines` 原话（最后一行用主题色），`cite` 出处。

### 插画

**`counter` 计数**：一排小方块逐个点亮，适合「每天 10 个单词」「连跳两级」。`icon` 左侧图标，`title`、`sub`，`count` 方块数（≤10），`labels` 方块上的字（默认 1、2、3…），`stub` 是否接主线。高 140。

**`journey` 航线**：从 A 到 B 的一道弧线，交通工具沿线移动。`from`、`to`、`label`（弧线上方小字），`vehicle`: `plane` / `ship` / `car` / `train`。高 108。

**`exchange` 交换**：两个图标中间一个双向箭头，适合「他教室友识字，室友教他卧推」。`left` / `right` 为 `{icon, label, scale}`，`middle` 箭头上的字。高 200。

**`team` 合伙人**：卡座、桌子和最多 4 个人名，可带一次改名（`rename: {from, to}`）和最多 3 行旁注 `notes`。人名可写 `{"text": "黄仁勋 · 30 岁 · CEO", "style": "bold"}` 标出主角。高 216。

**`tokens` 筹码**：一排小牌子加一个总数，如 `$200 $200 $200 = $600`。`items`、`total`、`x`（起点横坐标）。常配合 `attach` 叠在站点旁边。

**`icons` 图标排**：最多 4 个图标并排，每个有 `label` 和可选 `sub`。`card: false` 不画底卡。适合「他的四个身份」「三件代表作」。

**`plaque` 纪念牌**：一块牌子，`title`、`sub`；`scene: "booth"` 时画成挂在卡座上方。

**`compare` 对比**：左右两栏对比，中间 VS。每栏 `{icon 或 big, size, title, sub}`，`big` 是大字（如「4 核」），`verdict: "left"|"right"` 标出胜者，`vs` 改中间的字。

### 数字

**`bigstat` 大数字**：`value`、`unit`、`size`（默认 96）、`accent`（用主题色）、`lines` 下方说明、`line_size`、`x`。

**`ring` 倒计时圆环**：圆环一点点耗尽，最后被救回来。`value` 中间的数字，`unit`，`left` 左侧文字，`right` 右侧文字（救回时出现），`drain` 耗掉的比例（默认 11/12），`rescue` 是否救回（默认 true），`cx` 圆心横坐标。高 228。

**`dots` 幸存者点阵**：一堆点逐渐熄灭，只剩几个亮着。`total` 总数，`keep` 剩几个，`cols` 每行几个，`seed` 熄灭顺序的随机种子，`lines` 左侧文字。

**`bars` 柱状时间轴**：横轴是时间，柱子依次长出来。

```json
{"type": "bars", "height": 546,
 "axis": {"from": 0, "to": 34, "ticks": [[0, "2023"], [12, "2024"], [24, "2025"]]},
 "items": [{"t": 4, "v": 1, "label": "1 万亿", "note": "2023.05"}, {"t": 33, "v": 5, "label": "5 万亿", "note": "2025.10"}],
 "bracket": {"from": 0, "to": 1, "text": "180 天"},
 "event": {"t": 24, "level": 146, "lines": ["2025.01 DeepSeek", "单日蒸发约 6000 亿"]},
 "inset": {"value": "29", "unit": "个月", "lines": ["从 1 万亿到 5 万亿"]}}
```

`t` 是横轴位置（单位自定，这里是月），`v` 是柱高；`bracket` 在两根柱子（下标）之间标一个跨度；`event` 在某个时刻画一条虚线和说明，`level` 是说明距底部的高度；`inset` 左上角的大数字。

**`hbars` 横条**：`title`，`items` 为 `{label, v, text}`，`highlight` 高亮第几条（默认最后一条）。适合营收、身家、排名。

**`lifebar` 人生进度条**：一生分成几段，CEO 那段用主题色。

```json
{"type": "lifebar", "title": "63 年人生，33 年是英伟达 CEO", "start": 1963.13, "end": 2026.87,
 "segments": [{"from": 1963.13, "to": 1984, "label": "成长"}, {"from": 1993.26, "to": 2026.87, "label": "英伟达 CEO · 33 年", "accent": true}],
 "ticks": [[1963.13, "1963"], [2026.87, "2026"]]}
```

年份可以带小数（月份 / 12）。`ticks` 不写就用每段边界。`tail: false` 不画从终点连过来的虚线。

### 底层

**`text`**：纯文字段落，`lines`、`size`（默认 19）、`leading` 行距（默认字号 × 1.58）、`x`（默认 118）。太长的行自动折行。

**`raw`**：直接塞一段 SVG。横坐标就是整张图的横坐标（0~750，正文在 118~702），纵坐标从这块的顶边算起。`height` 必填，`stub_at` 在这个高度接主线。只在临时补一个小图形时用，复杂插画请写插件。

**`spacer`**：空白，`height`。
