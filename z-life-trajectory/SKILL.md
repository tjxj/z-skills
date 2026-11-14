---
name: z-life-trajectory
description: 人生轨迹长图——把任意一位名人的一生做成一张超长的动态 SVG（每屏 750×1000，3:4，可直接粘进公众号），再录成带配乐的 3:4 竖屏视频。封面是「人生线路图」，一条主线从出生一路走到今天；每屏讲一个时期，用站点、卡片、计数、航线、倒计时圆环、幸存者点阵、市值柱状图、营收横条、人生进度条等 22 种内容块和 50 个会动的小图标把故事演出来，也能给某个人物写定制插画块。自带排版自检（溢出、过挤、过空）、公众号兼容检查、逐屏截图，以及按音乐小节切屏的录屏脚本（可现场合成无版权配乐，也能用自己的音乐自动找拍点）。适合人物辞职、退休、去世、获奖、周年等新闻由头的生平回顾。触发词：人生轨迹、人生回顾、生平回顾、名人生平、人物生平长图、人物时间线、一张动图看完他的一生、XX 的一生、传记长图、人生线路图、生平视频、人生轨迹视频。
---

# 人生轨迹长图

输入一个人名（最好再加一个新闻由头），输出：

- 一张超长动态 SVG：封面 + 12~18 屏，每屏 750×1000，公众号里一屏一屏往下滑
- 一段 3:4 竖屏视频（1080×1440，带配乐），屏与屏之间跟着音乐小节缓动切换

## 工作流（照做，不要跳步）

### 1. 定由头和主线

- 由头：为什么是现在？辞职、退休、去世、获奖、新书、周年。有由头就写进封面 `cover.news`
- 主线：用一句话说出这个人的一生，比如「600 美元起家，33 年做到 5 万亿」。封面的大数字（`big`）和前缀（`kicker`）从这句话里来

### 2. 查资料，做事实表

读 `references/research.md`。要点：

- 先查权威来源：本人或机构官方、维基百科、主流媒体的长篇报道和人物特写
- 每条都记下**日期 + 事实 + 来源**；数字至少两处来源对得上，对不上就写「约」
- 挑 15~40 个节点，其中 3~5 个是能画成图的数字（金额、人数、天数、排名），1~3 句本人原话
- 敏感事件只写可归因的事实（「《XX》报道称」「董事会宣布」），措辞中性；不写与公共事件无关的私人个体姓名

### 3. 分屏

读 `references/design.md`。要点：

- 封面 + 12~18 屏。每屏一个时期，`title` 写这一段发生了什么（12 字内），`sub` 补一个具体细节
- 每屏 3~5 个块，至少一个插画或图表块；不要连着两屏只有站点
- 全片最多一屏 `"dark": true`，留给高潮（最大的那个数字）
- 最后一屏用 `terminus` 收住主线，再接一条 `lifebar` 总结一生
- 主题色：`terra`（陶土橙，默认）、`indigo`（科技、金融）、`jade`（科学、文化、自然）、`crimson`（体育、政治、戏剧性人物）

### 4. 写 spec（JSON）

照 `references/spec.md` 写，可以直接复制 `examples/jensen-huang.json` 改。要点：

- 站点标题 18 字内，说明文字每行 26 字内、最多两行；超了引擎会自动换行，但版面会挤
- 想让某些词绝对不出现，写进 `forbid`，出现就报错
- `sources` 写资料来源，显示在最后一屏底部

### 5. 生成，修到没有提醒

```bash
python3 scripts/lifeline.py build person.json -o person.svg --strict
```

| 提醒 | 意思 | 怎么改 |
|---|---|---|
| `OVERFLOW` | 某行字超出右边界 | 缩短这行字，或拆成两行 |
| `CROWDED` | 这屏内容比可用高度多 | 删字、把站点换成 `compact`，或拆成两屏 |
| `SPARSE` | 这屏内容不到六成高 | 补一个插画块（`card`、`counter`、`icons`）或再补一站 |
| 站名太长 | 封面线路图的站名放不下 | 站名缩到 5 字左右 |
| 未知块类型 | `type` 拼错，或插件没加载 | 对照 `references/spec.md`，检查 `plugins` |

### 6. 逐屏看图（必须）

```bash
python3 scripts/preview.py person.svg -o preview -t 1,4
```

先看总览 `preview/t4_sheet.jpg`，再一屏一屏打开 `t4_sNN.png`（第 4 秒，动画基本到位）和 `t1_sNN.png`（第 1 秒，动画刚开始）。检查：字压字、图标压字、卡片里的字出框、大片空白、深色屏对比度、主线和站点圆点是否对齐。有问题改 spec 重新生成。

### 7. 放进文章（可选）

在文章里想放长图的地方单独起一行写 `<!-- lifeline -->`，然后：

```bash
python3 scripts/lifeline.py embed person.svg 文章.md
```

再次执行会更新同一处。最后检查一遍文章：`python3 scripts/lifeline.py lint 文章.md`

### 8. 录视频（可选）

读 `references/video.md`。

```bash
python3 scripts/record.py person.json --plan                         # 看每屏停多久
python3 scripts/record.py person.json -o person.mp4 --test 1,8,40     # 抽几帧看
python3 scripts/record.py person.json -o person.mp4                   # 现场合成配乐
python3 scripts/record.py person.json -o person.mp4 --bgm song.mp3    # 用自己的音乐
```

录完用 ffmpeg 抽 3~4 帧看看（开头、某次切屏中间、深色屏、结尾），再用 `ffprobe` 确认时长和音轨。

## 现成的块不够用时

给这个人物写定制插画块（比如乒乓球台、Apple II、显卡风扇），放在 spec 同目录的 .py 里，用 `plugins` 加载。读 `references/custom-blocks.md`，参考 `examples/jensen_blocks.py`。

## 硬规矩

- 每屏 750×1000（3:4），整张图宽 750；视频 1080×1440
- 公众号兼容：不用 id / defs / style 元素 / script / 滤镜 / 渐变 / url(#) / use / clipPath / mask / image；动画只用 SMIL，全部 `repeatCount="indefinite"`；SVG 里没有空行，不出现全角句号「。」；最小字号 13。`lint` 会查
- 事实：每个日期和数字都要有出处；拿不准就写「约」「据报道」；敏感事件写可归因的事实，不下判断
- 标题不用夸张词（震惊、封神、炸裂、逆天之类）
- 不加署名框、二维码、水印
- 图标只用 `references/icons.md` 里的 50 个，或者在插件里自己画；不引用外部图片

## 文件

```
scripts/lifeline.py      引擎：build 生成长图，lint 查公众号兼容，icons 出图标总览，embed 放进文章
scripts/icons.py         50 个会动的小图标
scripts/preview.py       定格截图：每屏一张 PNG + 总览
scripts/record.py        录成 3:4 视频，切屏对齐音乐小节
scripts/bgm.py           现场合成配乐（warm / bright / calm）
references/spec.md       spec 字段和 22 种块
references/design.md     分屏和版面
references/research.md   查资料和事实核对
references/custom-blocks.md  写定制插画块
references/icons.md      图标清单
references/video.md      录屏、配乐、对拍
examples/                黄仁勋示例：spec、定制插画块、生成的长图
```
