# 票根旅程 `ticket-stub`

硬纸车票、打孔缺口和撕票线，每页都是一站。

![渲染效果](preview.jpg)

## 什么时候用

旅行攻略、探店路线、周末计划、城市指南。

## 色板

台面 `#0E4D52` · 票面 `#FFF4DE` · 墨 `#14323C` · 路线橙 `#F2A03D` · 邮戳红 `#D2452D`

## 字体

思源宋体负责标题，霞鹜文楷负责明信片手写。

## 招牌元素

打孔缺口、撕票线、路线站点、邮戳、SEAT 大数字、明信片横线。

## 注意

票面下方留给条形码，每页主体约 900px 高，内容比其他风格略紧。

## 复现

```bash
node scripts/build.cjs styles/ticket-stub/sample.json --out styles/ticket-stub/cards.html
node scripts/render.cjs styles/ticket-stub/cards.html --out ./output
```

风格由 `style.css` 和 `pages.html` 定义，`sample.json` 是示范内容。

## 样图

`samples/` 是 `sample.json` 的渲染结果，文案为虚构示例。
