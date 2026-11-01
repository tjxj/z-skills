# 12 种风格（材质）

风格只管「用什么材料画」：底色、墨色、强调色、字体、笔触、纹理。它不决定画什么，同一份 spec 换风格就是换一身衣服。

| 名字 | 中文 | 一句话 | 适合 |
|---|---|---|---|
| `swiss` | 瑞士网格 | 冷灰点阵、墨黑骨架、陶土橙流光 | 技术长文默认款 |
| `sketch` | 白板手绘 | Excalidraw 式抖线、斜线填充、楷体 | 科普、入门、头脑风暴 |
| `blueprint` | 工程蓝图 | 蓝晒底、白细线、黄标注、图号框 | 协议、硬件、分层结构 |
| `terminal` | 终端绿屏 | 黑底绿字、扫描线、闪烁光标 | Agent、CLI、安全 |
| `riso` | 孔版印刷 | 荧光粉 + 联邦蓝套色错位、颗粒 | 营销、增长、电商 |
| `editorial` | 杂志社论 | 米白纸、宋体、双线、报刊红 | 观点、行业、对比 |
| `field` | 现场手册 | 硬边切角、厚描边、红蓝硬投影 | SOP、规程、状态机 |
| `neon` | 霓虹夜 | 深夜蓝、青粉辉光 | 传播、网络、AI 未来感 |
| `porcelain` | 杂志瓷蓝 | 瓷白钴蓝、细线描金 | 金融、理财、数据 |
| `chalk` | 黑板粉笔 | 墨绿黑板、粉笔抖线 | 课堂、生物、物理 |
| `inkwash` | 水墨朱印 | 宣纸、淡墨、朱砂印章 | 国风、历史、文化 |
| `kraft` | 牛皮纸便签 | 牛皮纸底、彩色便签、胶带 | 生活、小店、非技术 |

## 自动选风格

`"style":"auto"` 会拿标题、眉题、副标题去和每种风格的关键词表比对，命中最多的胜出，一个都不中就用 `swiss`。关键词表在 `scripts/dongxi/styles.py` 里，可以自己加。

## 加一种新风格

在 `STYLES` 里加一个 dict，必填字段：

```
bg panel panel2 ink muted rule accent accent2 accent_ink good bad
font_title font_body font_mono title_weight radius stroke shape texture frame shadow keywords note cn
```

可选开关：`hachure`（斜线填充）、`tones`（节点轮换色）、`glow`（辉光）、`misreg`（套色错位）、`tape`（胶带）。

## 风格守则

- 一张图最多两种强调色，第三种颜色只能是灰
- 深色风格的强调色要亮（对比度够），浅色风格的强调色要沉
- 公众号不加载网络字体，字体栈都要有系统兜底；楷体风格在没装霞鹜文楷的手机上会回落到系统楷体
