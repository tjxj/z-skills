# 深夜终端 `night-terminal`

黑底绿字的命令行窗口，提示符串起全页。

![渲染效果](preview.jpg)

## 什么时候用

开发教程、命令速查、AI 工具、效率脚本。

## 色板

底 `#0B0F13` · 字 `#E8F0EC` · 绿 `#4DF29A` · 琥珀 `#FFB84D` · 红 `#FF6B6B`

## 字体

JetBrains Mono 配思源黑体。

## 招牌元素

窗口标题栏、`$` 提示符、OK 状态、diff 红绿对比、进度条、光标块。

## 注意

对比页是上下堆叠的 diff，适合写命令和代码片段。

## 复现

```bash
node scripts/build.cjs styles/night-terminal/sample.json --out styles/night-terminal/cards.html
node scripts/render.cjs styles/night-terminal/cards.html --out ./output
```

风格由 `style.css` 和 `pages.html` 定义，`sample.json` 是示范内容。

## 样图

`samples/` 是 `sample.json` 的渲染结果，文案为虚构示例。
