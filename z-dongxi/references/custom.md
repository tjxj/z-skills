# 自定义模式：31 种图型都不合适时

有些内容的「动」很特别，比如 KV Cache 复用、注意力矩阵、齿轮咬合。这时直接手写 SVG，但仍然走同一套规矩。

## 步骤

1. 先写剧本：用 3~6 句话写「第几秒，什么东西，从哪到哪，表示什么」
2. 定周期 T = 最后一个事件 + 2.6 秒
3. 用 `scripts/dongxi` 里的画笔，保证风格一致：

```python
import sys; sys.path.insert(0, "scripts")
from dongxi import STYLES, Painter
from dongxi.core import anim, motion, show_from, window

s = STYLES["swiss"]; P = Painter(s, "swiss", ratio="3:4"); T = 9.0   # P.W / P.H / P.L / P.R / P.CW 随画幅变
head, y = P.header("KV CACHE", "为什么第二个问题答得更快")
body = P.card(P.L, y + 20, P.CW / 2, 80, "第一轮", "算出 1000 个 token 的 KV")
body += f'<g opacity="0">{anim("opacity", show_from(2.0, T), T)}{P.lit(P.L, y + 20, P.CW / 2, 80)}</g>'
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {P.W} {P.H}">{P.background()}{head}{body}</svg>'
```

4. 跑 `python3 scripts/lint.py out.svg`，Floor 全过
5. 跑 `python3 scripts/capture.py out.svg --sheet sheet.png` 看 8 帧，确认每一帧都讲得通

## 不要做

- 不要套用和内容无关的通用动效（一直转的齿轮、随机飘的粒子）
- 不要一张图塞超过 9 个主节点，拆成两张
- 不要在动图里放大段文字，文字留给正文
