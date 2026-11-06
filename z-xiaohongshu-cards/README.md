# z-xiaohongshu-cards

一个持续生长的小红书 3:4 风格库。把文章交给 Agent，选一种风格，得到一组 1080×1440 PNG；做出新风格后，再把它沉淀回来。

![4 种风格](docs/styles-grid.jpg)

## 安装

```bash
npx skills add tjxj/z-skills --skill z-xiaohongshu-cards
npm i playwright
```

渲染优先使用系统 Chrome，没有时使用 Playwright 自带的 Chromium（`npx playwright install chromium`）。

## 使用

对 Agent 说：

```text
把这篇文章做成小红书 3:4 卡片，用黄便签手写风格
```

手动渲染：

```bash
cp styles/legal-pad/template.html ./cards.html
node scripts/render.cjs ./cards.html --out ./output --sheet ./output/sheet.jpg
```

脚本导出每张 `.card`，并检查尺寸和文字越界。检查不通过时退出码为 1。

## 风格

| 样图 | 风格 | 气质 | 适合 |
|---|---|---|---|
| <img src="styles/warm-paper/samples/01.jpg" width="150"> | **暖纸蓝橙**<br>`warm-paper` | 暖米色点阵纸上的产品手册，亲和、清楚 | 产品上手、App 教程、功能清单、对比选型 |
| <img src="styles/legal-pad/samples/01.jpg" width="150"> | **黄便签手写**<br>`legal-pad` | 黄色法律便签上贴图批注，像人亲手整理的笔记 | 教程、方法论、作品展示、学术与工具测评 |
| <img src="styles/rice-seal/samples/01.jpg" width="150"> | **宣纸朱印**<br>`rice-seal` | 装裱宣纸、远山、朱红印章，人文书卷气 | 诗词、历史、读书、人文项目 |
| <img src="styles/field-manual/samples/01.jpg" width="150"> | **现场手册**<br>`field-manual` | 象牙纸、海军蓝、信号红的工业手册台账 | 架构解释、SOP、决策清单、方法论 |

每个风格目录里有 `template.html`（可渲染模板）、`STYLE.md`（色板、字体、招牌元素）、`preview.jpg`（模板渲染图）和 `samples/`（原作样图）。

## 复现

```bash
node scripts/check_all.cjs
```

命令会重新渲染全部模板，检查 1080×1440 尺寸、文字越界、必备文件和本机路径。

模板示例用斜纹占位块代替原始截图，换上自己的图片即可。宣纸朱印来自 3:4 视频，已摊成静态卡片。

## 字体

| 字体 | 用途 | 没有时 |
|---|---|---|
| 思源宋体 VF | 绝大多数风格 | 回退 Noto Serif CJK、宋体，字重和行宽会变 |
| HanziPen SC（翩翩体） | 黄便签手写 | macOS 自带，其他系统换小赖 |
| 霞鹜文楷 | 宣纸朱印的印章和小标题 | 回退系统楷体 |

`SourceHanSerifSC-VF.ttf` 不在系统字体目录时，用 `XHS_SERIF_FONT=/路径/字体.ttf` 指定。

## 新增风格

按 [references/add-style.md](references/add-style.md) 操作。
