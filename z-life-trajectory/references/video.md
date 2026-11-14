# 录视频

`scripts/record.py` 把长图录成 3:4 竖屏视频：每屏停一会，然后缓动滑到下一屏，每屏都在音乐的强拍上停稳。

## 依赖

```bash
pip install playwright numpy
python3 -m playwright install chromium
brew install ffmpeg            # Linux 用 apt install ffmpeg
pip install librosa            # 可选：给自己的音乐找拍点
```

## 命令

```bash
python3 scripts/record.py person.json --plan                          # 只看时间表
python3 scripts/record.py person.json -o person.mp4 --test 1,8,40     # 只截这几个时刻
python3 scripts/record.py person.json -o person.mp4                   # 现场合成配乐
python3 scripts/record.py person.json -o person.mp4 --mood bright     # 换配乐情绪
python3 scripts/record.py person.json -o person.mp4 --bgm song.mp3    # 用自己的音乐
python3 scripts/record.py person.json -o person.mp4 --bgm none        # 无声
```

| 参数 | 说明 |
|---|---|
| `-o` | 输出 mp4，默认和 spec 同名 |
| `--bgm` | `auto`（默认，现场合成）/ `none` / 音乐文件路径 |
| `--mood` | 合成配乐的情绪：`warm`（默认）/ `bright` / `calm` |
| `--seed` | 合成配乐的随机种子，换一个数换一种编排 |
| `--bpm` | 合成时改速度；用自己的音乐时手动给速度，跳过自动找拍 |
| `--t0` | 自己的音乐里第一个强拍在第几秒，配合 `--bpm` |
| `--bgm-start` | 自己的音乐从第几秒开始用，跳过前奏 |
| `--fps` | 帧率，默认 30 |
| `--width` | 视频宽度，默认 1080，高度按 3:4 算 |
| `--crf` | 画质，默认 17，越小越清晰 |
| `--small` | 另存一份 crf 23 的小文件 `-small.mp4`，方便在聊天软件里发 |
| `--plan` | 只打印时间表，不录 |
| `--test` | 逗号分隔的秒数，只截这几个时刻的画面，存到 `<输出名>_test/` |

## 每屏停多久

按文字量和插画块自动估：

- 内容屏：`2.4 + 0.02 × 字数 + 插画加成` 秒，限制在 4.8~9.5 秒。字数 = 汉字个数 + 英文单词数 × 1.6；插画加成从 0.3（`quote`、`card`）到 1.6（`bars`），定制插画块算 0.8
- 封面：5 秒 + 每个站 0.04 秒
- 最后一屏多停 1.8 秒

想手动指定，在那一屏写 `"hold": 秒数`（封面写在 `cover` 里）。`--plan` 会打印每屏的到达时刻、停留和切屏时长，先看一眼再录。

## 切屏怎么对拍

音乐的强拍（每小节第 1、3 拍）连成一张网格：

- 每一屏都在某个强拍上停稳；从哪个强拍出发滑过去，看哪个让上一屏的停留最接近估算值
- 滑动用时一格（两拍）；一格短于 0.9 秒时用两格，免得滑得太急
- 每屏实际停留不少于估算值的 75%，也不少于 3 秒
- 结尾落在最后一屏停够之后的强拍上，画面淡出到纸色，音乐 2.5 秒淡出

## 配乐

**现场合成（默认）**：`bgm.py` 按视频长度合成一段器乐：电钢琴琶音、铺底和弦、贝斯、轻鼓组，带混响。没有版权问题；同样的 `--seed` 每次结果一样。

| 情绪 | 速度 | 调性 | 适合 |
|---|---|---|---|
| `warm` | 100 BPM | A 小调 | 默认，回顾、致敬 |
| `bright` | 112 BPM | C 大调 | 创业、成功、正向的人生 |
| `calm` | 84 BPM | D 大调 | 告别、科学家、作家 |

只要音乐：

```bash
python3 scripts/bgm.py -o bgm.wav --seconds 120 --mood warm
```

**用自己的音乐**：`--bgm song.mp3`。脚本用 librosa 估速度（自动折到 70~150 BPM），再找第一个强拍，整首按匀速网格切屏。找不准或者报「节拍不明显」时：

- 手动给：`--bpm 128 --t0 0.42`（第一个强拍在 0.42 秒）
- 前奏太长：`--bgm-start 12`，从第 12 秒开始用
- 音乐比视频短会自动循环；响度统一到 -16 LUFS，开头 0.3 秒淡入、结尾 2.5 秒淡出

用别人的音乐前确认你有使用权。

## 动画和切屏对齐

时长 ≥ 4.5 秒的动画（柱子长出来、圆环耗尽、计数）在视频里会推迟到这一屏到达时才开始，观众能看到完整的过程。短循环动画不受影响。

## 输出

- H.264，1080×1440，30fps，crf 17；AAC 48kHz 立体声 192k
- 两分钟左右的视频约 25~35MB；`--small` 版本约为它的三分之二

## 检查

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,sample_rate -of compact person.mp4
ffmpeg -v error -ss 50 -i person.mp4 -frames:v 1 -y check_50s.jpg
```

抽 3~4 帧：开头、某次切屏中间、深色屏、结尾淡出。看字有没有糊、切屏中间有没有跳帧、结尾是否淡出干净。

## 常见问题

| 现象 | 处理 |
|---|---|
| 视频太长 | 删字，或者给信息少的屏写更小的 `hold` |
| 某屏读不完就切走了 | 给那一屏写更大的 `hold` |
| 报「节拍不明显」 | 换一首鼓点清楚的音乐，或用 `--bpm` / `--t0` 手动给，或改用 `--bgm auto` |
| 切屏总比鼓点早或晚一点 | 用 `--t0` 微调第一个强拍 |
| 没装 librosa | 自己的音乐照样能用，只是不对拍；装上，或手动给 `--bpm` / `--t0` |
