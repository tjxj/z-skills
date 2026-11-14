# 录视频

`scripts/record.py` 把长图录成 3:4 竖屏视频：每屏停一会，然后缓动滑到下一屏。视频不带音轨，配乐、配音在剪辑软件里加。

## 依赖

```bash
pip install playwright
python3 -m playwright install chromium
brew install ffmpeg            # Linux 用 apt install ffmpeg
```

## 命令

```bash
python3 scripts/record.py person.json --plan                              # 只看时间表
python3 scripts/record.py person.json -o person.mp4 --test 1,8,40         # 只截这几个时刻
python3 scripts/record.py person.json -o person.mp4                       # 录视频
python3 scripts/record.py person.json -o person.mp4 --glide 1.2 --small   # 切屏快一点，另存小文件
```

| 参数 | 说明 |
|---|---|
| `-o` | 输出 mp4，默认和 spec 同名 |
| `--glide` | 每次切屏滑多少秒，默认 1.5 |
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
- 最后一屏多停 1.8 秒，结尾 1.2 秒淡出到纸色

想手动指定，在那一屏写 `"hold": 秒数`（封面写在 `cover` 里）。`--plan` 会打印每屏的到达时刻和停留时长，先看一眼再录。后期配乐想让切屏卡在鼓点上，也是照着这张表调 `hold`。

## 动画和切屏对齐

时长 ≥ 4.5 秒的动画（柱子长出来、圆环耗尽、计数）在视频里会推迟到这一屏滑到眼前时才开始，观众能看到完整的过程。短循环动画不受影响。

## 输出

- H.264，1080×1440，30fps，crf 17，没有音轨
- 黄仁勋示例 17 屏，129 秒，约 28MB；`--small` 版约 16MB，本机录制约 2 分钟

## 检查

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact person.mp4
ffmpeg -v error -ss 50 -i person.mp4 -frames:v 1 -y check_50s.jpg
```

抽 3~4 帧：开头、某次切屏中间、深色屏、结尾淡出。看字有没有糊、切屏中间有没有跳帧、结尾是否淡出干净。

## 常见问题

| 现象 | 处理 |
|---|---|
| 视频太长 | 删字，给信息少的屏写更小的 `hold`，或者把 `--glide` 调小 |
| 某屏读不完就切走了 | 给那一屏写更大的 `hold` |
| 切屏太急或太拖 | 调 `--glide`，1.2~1.8 秒比较自然 |
| 报「找不到 ffmpeg」 | 先装 ffmpeg |
