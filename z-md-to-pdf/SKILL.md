---
name: z-md-to-pdf
description: "Convert a local Markdown file into typeset PDFs in multiple styles via Pandoc + XeLaTeX. Use this skill whenever the user provides a .md path and says 转成PDF, Markdown转PDF, md转pdf, 生成PDF, 排版成PDF, 出书, 出电子书, 白皮书PDF, 书籍风PDF, 学术风PDF, 报告风PDF, or asks for a PDF version of an article/whitepaper/book. Ships three built-in styles (学术朴素风: report + Songti/Times; 文楷书籍风: ctexbook + LXGW WenKai/Palatino; 现代报告风: report + Hiragino/Helvetica + 品牌蓝色带章节样式) plus scripts/setup.sh for first-time environment bootstrap (pandoc, TinyTeX, tlmgr packages, CJK fonts) so it works on fresh machines."
---

# Markdown → 多风格 PDF 排版

## Overview

把用户写的 Markdown（含 Obsidian 方言）排成书籍级 PDF。管线：**sed 预处理 → Pandoc → XeLaTeX**。内置三种风格，参数集中在 `scripts/build.sh`，可照抄扩展新风格。

- **学术朴素风**：`report` 类，宋体 SC + Times New Roman，2.5cm 页边距，紧凑省纸
- **文楷书籍风**：`ctexbook` 类 + `oneside`，霞鹜文楷 + Palatino，行距舒展
- **现代报告风**：`report` 类 + `modern-report-style.tex` 注入，冬青黑体 + Helvetica Neue，品牌蓝色带封面、章首大编号、蓝色页眉线、引用变色块——大厂白皮书质感

产出含自动目录；标题默认取正文第一个 H1；章节编号**沿用原文自带编号**（不加自动编号）。

## 首次使用：环境安装（新机器必读）

依赖三件套：**pandoc**、**xelatex（TinyTeX/TeX Live）**、**中文字体**。先跑检测：

```bash
bash <skill目录>/scripts/setup.sh --check
```

有缺失则跑 `bash <skill目录>/scripts/setup.sh` 自动安装（macOS 优先 Homebrew）。手动清单：

| 组件 | 安装方式 | 说明 |
|---|---|---|
| pandoc ≥ 3 | mac: `brew install pandoc`；linux: `apt install pandoc` | 转换引擎 |
| TinyTeX | 官网脚本（setup.sh 内确认后执行） | 提供 xelatex/tlmgr，约 100MB 起 |
| LaTeX 包 | `tlmgr install ctex fontspec ...`（setup.sh 自动） | ctex 会带 xecjk 依赖 |
| 宋体 SC / Times / Palatino | macOS 自带 | Linux 装 `fonts-noto-cjk` + `tex-gyre` 等，build.sh 会自动回退 |
| 霞鹜文楷 | 可选，https://github.com/lxgw/LxgwWenKai 下载 ttf 双击安装 | 缺失时书籍风回退宋体 |
| Maple Mono CN | 可选，等宽字体 | 缺失时回退 Menlo/monospace |

**tlmgr 跨版本坑**：本地 TeX Live 年份比官方仓库旧时 `tlmgr install` 会直接拒绝。setup.sh 自动把仓库切到对应年份的归档镜像 `https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/<年份>/tlnet-final/` 并 `tlmgr update --self`。

## 工作流程

1. **环境检测**：`setup.sh --check`，有缺失先 `setup.sh`
2. **编译**：
   ```bash
   bash <skill目录>/scripts/build.sh <源md路径> <输出前缀> [标题]
   ```
   产出 `<前缀>-学术朴素风.pdf`、`<前缀>-文楷书籍风.pdf`、`<前缀>-现代报告风.pdf`
3. **验收**：脚本自动报告页数与图片下载失败数；失败数 > 0 时自动重试一次，仍失败则提示（多为网络抖动，稍后重跑即可）

## 关键决策与坑表（改脚本前必读）

| 坑 | 现象 | 对策（已在 build.sh 中实现） |
|---|---|---|
| 自动编号叠加 | 原文自带「第 7 章 / 7.1」，LaTeX 再编出「3.4 第 7 章」 | **不加** `--number-sections` |
| `→` 丢字 | Palatino/Times 无 U+2192，编译警告且 PDF 缺字 | `-V header-includes='\xeCJKDeclareCharClass{CJK}{"2192}'` 交给中文字体 |
| PingFang 不可见 | macOS 的苹方对 XeTeX 隐藏，`fontspec` 报错 | 中文无衬线用冬青黑体 `Hiragino Sans GB`，衬线用宋体 SC |
| 奇偶页不居中 | `ctexbook` 默认 `twoside` 装订边距 | 加 `-V classoption=oneside` |
| 图片下载失败 | 外链图由 pandoc 编译时下载，网络抖动会替换成文字 | 统计 `Could not fetch`，自动重试一次 |
| Obsidian wikilink 图 | `![[x]]` 离开 Obsidian 即裂 | sed 预处理转 `![](x)` |

## 扩展新风格

在 `build.sh` 里仿照现有两段 `pandoc` 调用加一段，核心变量就四个：`documentclass`、`classoption`、`CJKmainfont`、`mainfont`。想要页眉页脚/章节色带等定制，写一个样式 tex 用 `-H style.tex` 注入（注意 `\hypersetup` 须包在 `\AtBeginDocument` 里，pandoc 模板的 hyperref 加载在 header-includes 之后）。

## 输出约定

PDF 输出到 `<输出前缀>` 指定位置；若任务要求发布（如 GitHub 白皮书仓库），md 原文保留外链图片直接上传，GitHub 可正常显示。
