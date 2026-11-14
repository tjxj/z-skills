# z-life-trajectory 人生轨迹长图

把任意一位名人的一生做成一张超长的动态 SVG：封面是蛇形的「人生线路图」，往下每屏讲一个时期，一条主线从出生一路走到今天。每屏 750×1000（3:4），可以直接粘进公众号；也能录成带配乐的 1080×1440 竖屏视频，每屏都在音乐的强拍上停稳。

<img src="docs/preview.jpg" width="100%">

```bash
npx skills add tjxj/z-skills --skill z-life-trajectory
pip install -r requirements.txt && python3 -m playwright install chromium
```

然后对 Agent 说「做一张 XX 的人生轨迹长图」或「XX 的人生回顾」。完整流程见 [SKILL.md](SKILL.md)。

## 能做什么

- 22 种内容块：站点、紧凑站、卡片、引语、计数、航线、交换、合伙人、筹码、图标排、纪念牌、对比、大数字、倒计时圆环、幸存者点阵、柱状时间轴、横条、人生进度条等
- 50 个会动的小图标；现成的不够，就给这个人写定制插画块（示例里有 Apple II 贪吃蛇、乒乓球台、显卡风扇）
- 四套主题色：陶土橙、靛蓝、玉绿、绯红
- 排版自检：文字出界、整屏过挤、过空都会提醒；公众号兼容检查（不用 id、style、滤镜、渐变，动画只用 SMIL）
- 录视频：按文字量估算每屏停多久，切屏对齐音乐强拍；配乐可以现场合成（无版权），也可以用自己的音乐自动找拍

## 跑一遍示例

```bash
cd z-life-trajectory
python3 scripts/lifeline.py build examples/jensen-huang.json -o jensen.svg --strict
python3 scripts/preview.py jensen.svg -o preview -t 4
python3 scripts/record.py examples/jensen-huang.json -o jensen.mp4
```

[`examples/jensen-huang.svg`](examples/jensen-huang.svg) 是生成好的长图，用浏览器打开就能看动画。spec 在 [`examples/jensen-huang.json`](examples/jensen-huang.json)，定制插画块在 [`examples/jensen_blocks.py`](examples/jensen_blocks.py)。

## 依赖

- Python 3，`pip install -r requirements.txt`
- Playwright 的 Chromium（截图、录屏）
- ffmpeg（录屏）
- librosa（可选，给自己的音乐找拍点）
- 字体：默认用思源宋体量字宽，没有就依次找 Noto Serif CJK、宋体；也可以用 `--font` 或环境变量 `LIFELINE_FONT` 指定

## 局限

- 引擎只管排版和动画，事实靠查资料。生成前请按 [`references/research.md`](references/research.md) 核对每个日期和数字
- 字宽按本机字体量。读者手机上的字体不一样时，个别长行可能比预期宽一点，标题和说明留些余量更稳
- 公众号编辑器里 SVG 太大会变卡，`lint` 超过 400KB 会提醒；示例 17 屏约 136KB
- 合成配乐是程序生成的器乐，风格有限；正式发布的视频可以换成自己有使用权的音乐
