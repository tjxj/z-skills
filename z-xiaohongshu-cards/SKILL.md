---
name: z-xiaohongshu-cards
description: 把文章或要点做成 3:4（1080×1440）小红书、小绿书图文卡片，内置 12 种可复现的命名风格。Agent 只写内容 JSON，版式由风格决定，任何人做出来效果一致。触发词：小红书卡片、小红书图文、3:4 图文、3:4 卡片、小绿书配图、做成卡片、图文卡片、换个卡片风格、沉淀这个风格、新增卡片风格。
---

# 小红书 3:4 风格库

输入文章或要点，输出一组 1080×1440 PNG。

## 风格

| id | 名称 | 适合 |
|---|---|---|
| `exam-paper` | 红笔试卷 | 避坑清单、知识自测、新手必看、常见错误 |
| `receipt-strip` | 热敏小票 | 购物清单、预算账单、好物测评、比价 |
| `blueprint` | 蓝晒图纸 | 技术原理、系统架构、产品拆解、流程说明 |
| `blackboard` | 粉笔黑板 | 学习方法、知识点、读书笔记、课程总结 |
| `riso-zine` | 双色孔版 | 个人成长、观点表达、生活态度、活动海报 |
| `almanac` | 老黄历 | 节气养生、生活习惯、日常宜忌、传统文化 |
| `night-terminal` | 深夜终端 | 开发教程、命令速查、AI 工具、效率脚本 |
| `ticket-stub` | 票根旅程 | 旅行攻略、探店路线、周末计划、城市指南 |
| `warm-paper` | 暖纸蓝橙 | 产品上手、App 教程、功能清单、对比选型 |
| `legal-pad` | 黄便签手写 | 教程、方法论、作品展示、学术与工具测评 |
| `rice-seal` | 宣纸朱印 | 诗词、历史、读书、人文项目 |
| `field-manual` | 现场手册 | 架构解释、SOP、决策清单、方法论 |

用户点名时直接用；没点名时按内容匹配，并避开上一组用过的风格。选定后读 `styles/<id>/STYLE.md`。

前 8 种走下面的 JSON 流程。后 4 种是模板风格：复制 `styles/<id>/template.html` 成 `cards.html`，改文字和图片后渲染，`.ph` 占位块全部换成真实图片。

## 流程

1. **准备**：首次使用时在工作目录安装依赖，字体包保证换机器后字形一致。

   ```bash
   npm i playwright @fontsource-variable/noto-serif-sc @fontsource-variable/noto-sans-sc @fontsource-variable/jetbrains-mono lxgw-wenkai-webfont
   ```

2. **拆页**：默认 6–9 页。封面一句钩子，内容页一页一个观点，结尾页给结论或行动。页面类型只有 8 种，按 `references/content-schema.md` 写 `content.json`，只写内容，不写 HTML 和 CSS。图片放进 `assets/`，用相对路径。
3. **生成**：

   ```bash
   node <skill目录>/scripts/build.cjs content.json --style exam-paper --out cards.html
   ```

   内容超限时脚本会列出每一处，按提示删字或拆页后重跑，不要改风格文件来迁就内容。

4. **渲染**：

   ```bash
   node <skill目录>/scripts/render.cjs cards.html --out output --sheet output/sheet.jpg
   ```

   脚本在字号下限内自动缩字，并检查尺寸、越界和最小字号。退出码为 1 时，按输出删字或拆页。

5. **看图**：打开总览图逐页看，处理孤字、断词和截图裁切。标题里用 `\n` 手动断行。
6. **交付**：给 `output/` 里的 PNG。用户要发布文案时，再写一段简短正文。

换风格时保留 `content.json`，只改 `--style` 重新生成。

## 版面规则

- 画布固定 1080×1440，导出 PNG。
- 手机上正文不小于 24px，标题不小于 72px。
- `**重点**` 标出高亮词，每页最多一处。
- 样例里的数字都是示例。真实内容的数字要有来源，估算要写明。

## 沉淀新风格

用户说「沉淀这个风格」，或做出了风格库之外的设计时，按 `references/add-style.md` 执行。风格必须通过 `scripts/check_all.cjs`。
