# 热敏小票 `receipt-strip`

橙色台面上的收银小票，一条条明细像在结账。

![渲染效果](preview.jpg)

## 什么时候用

购物清单、预算账单、好物测评、比价。

## 色板

台面 `#FF6A2B` · 纸 `#FDFCF6` · 墨 `#1A1A1A` · 印章红 `#E8401C`

## 字体

思源黑体负责标题和明细，JetBrains Mono 负责数字。

## 招牌元素

锯齿撕边、虚线分隔、点线引导、合计大数字、条形码、已核对印章。

## 注意

`stat.items[].text` 写金额或短值，会排到行尾；图片自动转成黑白。

## 复现

```bash
node scripts/build.cjs styles/receipt-strip/sample.json --out styles/receipt-strip/cards.html
node scripts/render.cjs styles/receipt-strip/cards.html --out ./output
```

风格由 `style.css` 和 `pages.html` 定义，`sample.json` 是示范内容。

## 样图

`samples/` 是 `sample.json` 的渲染结果，文案为虚构示例。
