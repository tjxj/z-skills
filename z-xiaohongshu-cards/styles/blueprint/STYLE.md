# 蓝晒图纸 `blueprint`

普鲁士蓝工程图，白线、尺寸线和标题栏。

![渲染效果](preview.jpg)

## 什么时候用

技术原理、系统架构、产品拆解、流程说明。

## 色板

图纸蓝 `#113A8C` · 线 `#CFE1FF` · 辅线 `#8FB3EE` · 标注黄 `#FFD166`

## 字体

思源黑体负责内容，JetBrains Mono 负责编号。

## 招牌元素

图框对中标记、尺寸标注线、总线节点、流程箭头、底部标题栏。

## 注意

和现场手册同属工程气质：内容偏原理选蓝晒图纸，偏 SOP 和台账选现场手册。

## 复现

```bash
node scripts/build.cjs styles/blueprint/sample.json --out styles/blueprint/cards.html
node scripts/render.cjs styles/blueprint/cards.html --out ./output
```

风格由 `style.css` 和 `pages.html` 定义，`sample.json` 是示范内容。

## 样图

`samples/` 是 `sample.json` 的渲染结果，文案为虚构示例。
