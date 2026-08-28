# z-md-to-pdf

一个面向中文长文的 Markdown → PDF Skill

它内置三套原创排版：学术朴素风、文楷书籍风、现代报告风。可以生成指定风格，也可以一次生成全部风格。另有独立入口用于复编 `HEJustinSun/my-girlfriend-jingtian-latex`，上游文件由使用者自行提供

## 快速开始

```bash
bash scripts/setup.sh --check
bash scripts/setup.sh
bash scripts/build.sh -i examples/sample.md -o dist/sample --style all
```

生成单一风格：

```bash
bash scripts/build.sh -i article.md -o dist/article --style book
```

复编上游项目：

```bash
bash scripts/build-upstream.sh /path/to/my-girlfriend-jingtian-latex /path/to/output.pdf
```

上游当前的独立封面素材可能渲染为空白。脚本会在仓库自带成品 PDF 时提取第一页作为临时封面，并保持上游目录不变

## 依赖

- Bash
- Pandoc
- XeLaTeX / TinyTeX
- 一套中文衬线字体与一套中文无衬线字体

`scripts/setup.sh` 可以检查并补齐大部分环境

## 许可证边界

本 Skill 自身采用 MIT License

`HEJustinSun/my-girlfriend-jingtian-latex` 没有声明许可证，本仓库不包含它的正文、封面、字体或模板源码。复编工具只读取使用者本地已有的上游目录

## 测试

```bash
bash scripts/smoke-test.sh
```

同时测试上游项目：

```bash
bash scripts/smoke-test.sh --upstream /path/to/my-girlfriend-jingtian-latex
```
