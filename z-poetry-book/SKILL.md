---
name: poetry-book
description: 把诗词、文赋、年谱、史料或技术文章整理为编年诗传、主题文集、图文专题或课程讲义，生成宋代文人审美的简体横排 LaTeX PDF。用户说“用 Poetry Book 成书”“把这些资料排成书”“编年诗集 PDF”“把 Markdown 技术文章做成图文样张”“选择烟雨、青瓷、墨禅、朱砂、月夜或竹影模板”时使用。保留来源、图片和未系年状态，内置六套主题，并输出逐页校验报告和预览图。
---

# Poetry Book

将一批有出处的资料编成可阅读、可核查、可重建的诗词书、技术专题或讲义。交付物是实际 PDF，不是只有排版建议或 LaTeX 片段。

## 输入与原则

1. 先确认主题、作者范围、时间范围、输出语言和所需风格；用户未指定主题时用 `song-mist`。
2. 盘点并保留原始文件。逐条记录作品、段落、系年、系年依据、注释和出处，不把来源文件与编纂层混写。
3. 将资料整理为 `examples/book.json` 所示的规范化 JSON。引擎接收此 JSON；不要声称任意 PDF、图片或网页可以不经过读取和结构化就直接成书。
4. 默认交付简体中文横排。繁体原件可保留作考证，但正式书稿要按用户要求转换并抽查；不得擅自改成竖排。
5. 已知年份按 `date.start` 升序放入章节；只能确定区间时保留区间和“约”；未系年作品放入 `appendix`，不得杜撰年份。引擎不会静默重排错误顺序。
6. 每条作品必须有稳定 ID 和至少一个来源。题解、`gloss` 笺注、`comment` 批语按证据编写；不为普通作品批量生成空泛赏析。
7. 数字只陈述已处理资料的实际数量，不宣称“天下无遗漏”。署名存疑、异文、重复正文与缺失来源必须明示。

## 环境与输出

需要 `latexmk`、LuaLaTeX、Ghostscript、Python 3，以及 `fontTools`、PyMuPDF、Pillow；技术文章模式另用 PyYAML，LaTeX 使用 fancyvrb、booktabs、tabularx。系统需要 Source Han Serif SC VF、Early Summer Serif、LXGW WenKai。技能自带 BabelStoneHan、I.Ming 及许可；也可通过 `POETRY_BOOK_MAIN_FONT` 指定主中文字体文件以计算生僻字回退。

依赖缺失时明确报告并停止，不静默换用 Last Resort 或 Unifont，不未经同意安装软件。

输出目录必须不存在或为空，防止覆盖用户资料。重建时使用新目录，或由用户明确处理旧产物后再运行。

## 六套主题

| ID | 名称 | 适用气质 |
|---|---|---|
| `song-mist` | 烟雨留白 | 默认；米白、淡墨、远山、江面与朱印 |
| `celadon` | 青瓷天青 | 温润、清透、含蓄的青绿层山 |
| `ink-zen` | 墨禅寂照 | 灰白、墨山、圆相与墨评 |
| `cinnabar-seal` | 朱砂印谱 | 米纸、朱砂、鉴藏印章 |
| `moon-river` | 月夜赤壁 | 蓝灰、明月、江水与夜航 |
| `bamboo` | 竹影清风 | 淡青绿、疏竹与叶影 |

只列当前已实现的模板。列出主题：

```bash
python3 "$HOME/.agents/skills/poetry-book/scripts/build_style.py" --list
```

## 构建与验收

```bash
python3 "$HOME/.agents/skills/poetry-book/scripts/render_book.py" \
  --input "/absolute/path/book.json" \
  --theme "song-mist" \
  --output "/absolute/path/new-output-directory"
```

命令会检查书稿和依赖、编译 LaTeX、复制成品，并自动执行 PDF 验收。成功输出包含：

- 以完整书名命名的 PDF。
- `build/` 中的 LaTeX、编译日志、作品页映射和构建清单。
- `manifest.json`、`font-usage.json` 和 `book.works`。
- `validation-report.json`。
- `preview/` 中的代表页面和联系表。

校验不是只检查编译退出码。还包括书名元数据、页面尺寸、作品 ID 实际上页、代表正文、日志缺字与引用错误、排版溢出、字体嵌入、非法回退字体、页面越界、异常空白页、横排抽样，以及 Ghostscript 全页解析。

## 技术文章与课程讲义

普通 Markdown 可直接进入技术文章模式，不必先手工改成诗词数据结构：

```bash
python3 "$HOME/.agents/skills/poetry-book/scripts/render_article.py" \
  --input "/absolute/path/article.md" \
  --theme "celadon" \
  --title "文章主标题" \
  --subtitle "文章副标题" \
  --author "作者或栏目名" \
  --seal "印章文字" \
  --output "/absolute/path/new-output-directory"
```

支持 YAML 元数据、标题、粗体、行内代码、HTTP/HTTPS 链接、有序/无序列表、图片、围栏代码、简单管道表格和引用块。`--series`、`--edition`、`--date`、`--subject` 可覆盖默认元数据；`--require "必须出现的语句"` 可重复用于关键内容验收。

- 原文只读，转换后的 `source.md`、`book.json` 与 `source-manifest.json` 留在资料目录。默认资料目录是输出目录旁的 `<输出名>-assets`，也可用 `--assets-dir` 指定。
- 网络图片仅允许 HTTPS，单张限制 25MB，记录尺寸和 SHA-256。使用 `--offline` 时禁止下载，只使用已有且校验一致的图片。
- 文章不显示诗词的系年依据和重复年份标题；原稿行号用于章节来源与漏段检查。
- 图片保持宽高比；文章校验还包括图片数量、链接、Markdown 残留和指定关键语句。
- 复杂 HTML、嵌套列表、转义竖线表格、数学公式等不是当前支持范围；遇到未支持结构应明确处理，不静默漏掉。

完整案例在 `examples/laozhang-deepinfer/`：老章 DeepInfer 技术文章、7 张原图及来源清单。代码、表格、引用与链接夹具在 `examples/technical-fixture.md`。

## 书稿结构速查

- `metadata`：`title`、`author` 必填；`subtitle`、`series`、`edition`、`seal`、`subject`、`keywords` 可配置。
- `frontmatter`、`backmatter`：由 `heading` 与 `paragraphs` 组成的章节数组。
- `chapters`：每章含 `id`、`title`、`years`、`intro`、`works`。
- `appendix`：可选，结构同章节，用于未系年或跨期作品。
- `works[]`：`id`、`title`、`type`、`paragraphs`、`date`、`sources` 必填；`date` 含 `start`、`end`、`label`、`evidence`，`sources` 至少一项。`intro`、`gloss`、`comment` 可选。
- `document_type`：`book`（默认）或 `article`。文章可使用 `works[].blocks` 表示段落、标题、列表、图片、代码、表格、引用和分隔线，旧 `paragraphs` 书稿保持兼容。
- `index`：默认为 `true`，生成篇名索引；技术文章通常关闭篇名索引，由文章小节进入目录。

完整可运行示例见 `examples/book.json`。书稿字段无效、作品 ID 重复、正文为空、年份倒序或来源缺失时，命令应以非零状态退出并给出字段位置。

## 完成标准

只有 PDF 与 `validation-report.json` 均生成、报告 `passed` 为 `true`，并查看封面和代表页面后，才可向用户报告完成。回复中提供 PDF、报告和预览链接，说明主题、页数、作品数、资料范围与存疑口径；测试未覆盖的事项不得声称已经验证。
