---
name: z-handwriting-font
description: 把自己（或家人）的手写字做成能安装使用的 OpenType 字体（.otf）。两条路：格子路线——打印模板、一格写一个字、手机拍照，自动定位裁切；信件路线——只有一封旧信、一页笔记，按原文切出现有的字。自动统一字号与笔画粗细、矢量化、生成竖排标点和同字多写法轮换，附检查与样张。触发词：手写字体、做一套自己的字体、把字迹做成字体、家人字迹字体、手写体 otf、handwriting font。
---

# 手写字体工坊

目标：让一个不是字体设计师的人，在一两个周末里得到一套“能装进电脑、能打字、看得出是自己笔迹”的字体。它不是专业字库：字形不做逐字精修，没有字偶距，汉字只覆盖用户真正写过的那些。

```text
格子路线  template ─▶ 打印、手写、拍照 ─▶ extract ─▶ review ─▶ build ─▶ specimen / check
信件路线  segment ─▶ 人工核对 boxes.json ─▶ cut ─▶ review ─▶ build ─▶ specimen / check
```

所有字形都只来自用户给的图片；脚本不读取、不复制任何现成字体的轮廓。`assets/common-2997.txt` 是自建的常用字清单（GB2312 一级字按习惯排序的粗略版本），只用来决定模板写哪些字。

## 开工前确认

1. **字迹归谁**：是用户本人的字，还是家人、朋友的？不是本人的，提醒用户先征得书写者同意，再决定字体能不能公开发布。
2. **走哪条路**：书写者还能写字 → 格子路线（推荐，质量高得多）；只剩旧手稿 → 信件路线，并提前说明能得到的字数就是手稿里不重复的字数。
3. **写多少**：《现代汉语常用字表》的说明里，2500 个常用字覆盖了约 97.97% 的语料，再加 1000 个次常用字约 99.48%。字频是长尾的，前几百个字就占了日常文本的大头。建议先从 `--count 500` 起，用得顺手再加页。
4. 依赖：`pip install -r requirements.txt`，再装 potrace（`brew install potrace` / `apt install potrace`）。可选 `pip install opentype-sanitizer` 用于检查。

## 格子路线

```bash
python3 scripts/hwfont.py template --count 500 --extra latin,digits,punct --out tpl
```

得到 `tpl/template.pdf`（A4，每页 72 格，每格上方灰色小字是要写的字）和 `template.json`。告诉用户：

- 原尺寸打印，不要“适合页面”缩放；黑色签字笔或中性笔，比平时稍粗。
- 字写在格子中间、别碰框线，一格一个；写错就整格涂掉留空，脚本会把它当缺字。
- 拍照时四个黑色方块都要在画面里，光线均匀，尽量正对纸面；顺序随意，页码印在页脚的小方块里。

```bash
python3 scripts/hwfont.py extract --template tpl --photos IMG_*.jpg --out work
python3 scripts/hwfont.py review --work work
```

打开 `work/review.png` 逐格看：标签和字是否对上、有没有半个字、有没有脏点。`work/extract_report.json` 列出空格、碰边和没识别出页码的照片。有问题的格子删掉对应 `work/glyphs/U+XXXX.png` 重拍或补写那一页即可。

## 信件路线

需要两样东西：手稿照片，和一份逐字抄录（`transcript.txt`，标点照抄，换行不重要）。

```bash
python3 scripts/hwfont.py segment --photo letter.jpg --text transcript.txt --out work
```

脚本按行切、按字距切，再把抄录里的字依次贴到方框上，输出 `work/boxes.png`（叠框预览）和 `work/boxes.json`。**这一步一定要人工核对**：连笔字会被切成一个框、左右结构的字会被切成两个框，只要错一个，后面的标签就全部错位。打开 boxes.png，从第一个错位处开始改 boxes.json——合并、拆分或调整 `box`，修正 `char`，直到框数和字数对上、每个框的字都对。框数和抄录字数差多少，脚本会打印出来。

```bash
python3 scripts/hwfont.py cut --work work
python3 scripts/hwfont.py review --work work
```

同一个字出现多次会全部保留成 `.alt1 .alt2…`，字体里用上下文替换轮换显示，打字时不会每个“的”都一模一样。

## 生成字体

```bash
python3 scripts/hwfont.py build --work work --family MyHand --version 0.100 \
    --copyright "Handwriting © 2026 书写者姓名" --license "仅限个人使用"
python3 scripts/hwfont.py specimen --font work/MyHand-Regular.otf --text "今天天气很好，我们去公园散步。" --out work/specimen.png
python3 scripts/hwfont.py check --font work/MyHand-Regular.otf
```

build 会把所有汉字统一缩放到中位字面 800/1000、用距离变换把笔画粗细拉到一致、放大后用 potrace 描成曲线；西文和数字按比例落在基线上；全角逗号句号顿号放在左下，并生成竖排位置。参数：

- `--keep-position`：保留字在原格子里的位置和大小（更像手写，但字会忽大忽小），信件路线常用。
- `--no-weight`：不统一粗细，保留原笔的轻重。
- `--face 760`：整体字面调小一点。

specimen 会列出样张文字里缺的字。check 会报告超出字身框的字形，安装了 opentype-sanitizer 时还会跑一遍 OTS——浏览器和系统都用它判断字体是否损坏。

## 交付前

把 specimen 图给用户看，说清楚：收录了多少字、缺字时系统会用别的字体补上（混排时会显得突兀）、没有字偶距和逐字修形。字体名、版本号在 build 时写入，`--copyright` 和 `--license` 写入版权与许可说明；公开发布前请用户确认书写者同意和许可证（例如 SIL OFL）。

## 已知局限

- 信件路线的切分只是起点，连笔草书、字距极紧的手稿需要大量人工改框。
- 低分辨率照片（每字不足 80 像素）描出来会发虚；格子路线每格约 160 像素，足够。
- 不做部件拼字：没写过的字就是没有。想用已有部件拼出新字，是另一件需要逐个调结构的工作，这个 skill 不碰。
