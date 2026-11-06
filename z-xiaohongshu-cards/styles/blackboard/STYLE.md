# 粉笔黑板 `blackboard`

墨绿黑板上的粉笔板书，有擦痕和粉笔槽。

![渲染效果](preview.jpg)

## 什么时候用

学习方法、知识点、读书笔记、课程总结。

## 色板

板面 `#1F3B33` · 粉笔白 `#FFFDF4` · 黄 `#FFE36B` · 粉 `#FFB0B5` · 蓝 `#BCE7F5`

## 字体

全程霞鹜文楷，粉笔颗粒由 SVG 滤镜生成。

## 招牌元素

粉笔颗粒、板擦痕迹、手画圆圈序号、波浪下划线、木质粉笔槽。

## 注意

配图不加粉笔滤镜，保持清晰；手写字体下正文字号要比宋体大一档。

## 复现

```bash
node scripts/build.cjs styles/blackboard/sample.json --out styles/blackboard/cards.html
node scripts/render.cjs styles/blackboard/cards.html --out ./output
```

风格由 `style.css` 和 `pages.html` 定义，`sample.json` 是示范内容。

## 样图

`samples/` 是 `sample.json` 的渲染结果，文案为虚构示例。
