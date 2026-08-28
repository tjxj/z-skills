---
name: z-md-to-pdf
description: 将 Markdown、Obsidian 笔记、技术文章、白皮书或长文排成中文 PDF。用户说“转成 PDF”“Markdown 转 PDF”“md 转 pdf”“排版成电子书”“生成指定风格 PDF”“一次生成多种风格”“学术风/书籍风/报告风”，或要编译 my-girlfriend-jingtian-latex 项目时，都应使用本 Skill。内置学术朴素风、文楷书籍风、现代报告风，支持只生成一种或批量生成全部风格，并附带上游 XeLaTeX 项目原样复编工具。
compatibility: macOS 或 Linux；需要 Bash、Pandoc、XeLaTeX。setup.sh 可自动补齐环境。
---

# Markdown → 多风格 PDF

把 Markdown 交给 Pandoc，再由 XeLaTeX 完成中文字体、页面、目录、页眉页脚和 PDF 输出

## 完成标准

一次任务只有同时满足以下条件才算完成：

1. 环境检查通过
2. 用户指定的每种风格均生成非空 PDF
3. PDF 能被 `pdfinfo` 读取，页数合理
4. `pdftotext` 能提取出中文正文，说明没有空白或乱码
5. 批量模式缺少任一风格时，任务失败并修复

## 风格选择

| 风格参数 | 中文名 | 适用场景 |
|---|---|---|
| `academic` | 学术朴素风 | 论文笔记、研究报告、课程材料 |
| `book` | 文楷书籍风 | 长文、随笔、电子书、个人作品集 |
| `report` | 现代报告风 | 技术白皮书、方案、商业报告 |
| `all` | 全部风格 | 同一内容一次生成三份 PDF 供比较 |

用户没有指定风格时，使用 `all`

## 第一次使用

先检测：

```bash
bash <skill目录>/scripts/setup.sh --check
```

检测失败时自动安装：

```bash
bash <skill目录>/scripts/setup.sh
```

安装脚本会准备 Pandoc、轻量 TeX 环境、中文排版组件。构建脚本会自动发现 TinyTeX，无需修改终端配置

## 生成 PDF

指定一种风格：

```bash
bash <skill目录>/scripts/build.sh \
  -i /absolute/path/article.md \
  -o /absolute/path/dist/article \
  --style book \
  --title "文章标题" \
  --author "作者"
```

一次生成全部风格：

```bash
bash <skill目录>/scripts/build.sh \
  -i /absolute/path/article.md \
  -o /absolute/path/dist/article \
  --style all
```

输出文件会自动带中文风格后缀：

- `article-学术朴素风.pdf`
- `article-文楷书籍风.pdf`
- `article-现代报告风.pdf`

正文第一个一级标题会作为默认 PDF 标题。使用 `--no-toc` 可关闭目录

## 复编孙宇晨项目

用户给出 `my-girlfriend-jingtian-latex` 本地目录并要求变成 PDF 时，使用：

```bash
bash <skill目录>/scripts/build-upstream.sh \
  /absolute/path/my-girlfriend-jingtian-latex \
  /absolute/path/output/我的女友景甜.pdf
```

这个入口直接使用上游仓库里的 `main.tex`、封面和字体，连续编译两次，保留原项目的 5×8 英寸版式

上游当前的 `assets/cover.pdf` 在常见渲染器中会显示为空白页。仓库自带成品 PDF 时，脚本会临时提取成品第一页作为正常封面，整个过程不改动上游文件

上游仓库当前没有声明开源许可证。不要把它的正文、封面、字体或 `main.tex` 复制进本 Skill，也不要把本 Skill 的 MIT 许可证解释成对上游文件的授权。精确复编时让用户自己提供已下载的上游项目目录

## 输入兼容

- 标准 Markdown 标题、列表、引用、代码块、表格和链接
- Obsidian 图片语法 `![[image.png]]`，构建前会转成标准 Markdown 图片
- 中文与英文混排
- 图片相对路径，按源 Markdown 所在目录查找

外链图片下载失败时，保留编译日志并明确提示。不要把缺图的 PDF 当成成功交付

## 验收

完成构建后运行：

```bash
pdfinfo /absolute/path/output.pdf
pdftotext /absolute/path/output.pdf - | head
```

需要同时回归三套模板和上游项目时运行：

```bash
bash <skill目录>/scripts/smoke-test.sh \
  --upstream /absolute/path/my-girlfriend-jingtian-latex
```

## 扩展模板

三套风格分别由以下文件控制：

- `scripts/academic-style.tex`
- `scripts/book-style.tex`
- `scripts/modern-report-style.tex`

新增风格时复制其中最接近的一份样式，随后在 `build.sh` 增加明确的风格名、输出后缀和字体回退。新风格必须加入 `smoke-test.sh`，保证单独生成与批量生成都可验证

## 常见问题

| 现象 | 处理 |
|---|---|
| 找不到 `xelatex` | 运行 `setup.sh`，构建脚本也会自动查找 TinyTeX |
| 中文字体报错 | macOS 启用宋体/冬青黑体，Linux 安装 Noto CJK 字体 |
| 霞鹜文楷未安装 | 书籍风自动回退为宋体或 Noto Serif CJK |
| 外链图片缺失 | 检查网络后重跑，或先把图片保存到 Markdown 同目录 |
| 只想要一份 PDF | 传 `--style academic/book/report`，避免使用 `all` |
| 原项目编译失败 | 先确认封面、两款字体和 `main.tex` 都在原仓库目录中 |
