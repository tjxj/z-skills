#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STYLE="all"
TITLE=""
AUTHOR=""
SRC=""
OUT=""
WITH_TOC=1

usage() {
  cat <<'EOF'
用法：
  build.sh -i <文章.md> -o <输出前缀> [-s academic|book|report|all]
           [--title 标题] [--author 作者] [--no-toc]

兼容旧用法：
  build.sh <文章.md> <输出前缀> [标题] [academic|book|report|all]

风格：
  academic  学术朴素风
  book      文楷书籍风
  report    现代报告风
  all       一次生成全部三种风格
EOF
}

if [ $# -ge 2 ] && [[ "$1" != -* ]]; then
  SRC="$1"
  OUT="$2"
  TITLE="${3:-}"
  STYLE="${4:-all}"
  shift "$#"
fi

while [ $# -gt 0 ]; do
  case "$1" in
    -i|--input) SRC="${2:?缺少输入路径}"; shift 2 ;;
    -o|--output) OUT="${2:?缺少输出前缀}"; shift 2 ;;
    -s|--style) STYLE="${2:?缺少风格名}"; shift 2 ;;
    --title) TITLE="${2:?缺少标题}"; shift 2 ;;
    --author) AUTHOR="${2:?缺少作者}"; shift 2 ;;
    --no-toc) WITH_TOC=0; shift ;;
    --list-styles) printf '%s\n' academic book report all; exit 0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$SRC" ] && [ -n "$OUT" ] || { usage >&2; exit 2; }
[ -f "$SRC" ] || { echo "找不到输入文件：$SRC" >&2; exit 1; }

case "$STYLE" in
  academic|book|report|all) ;;
  学术朴素风) STYLE="academic" ;;
  文楷书籍风) STYLE="book" ;;
  现代报告风) STYLE="report" ;;
  *) echo "不支持的风格：$STYLE" >&2; exit 2 ;;
esac

add_tex_path() {
  local candidate
  for candidate in \
    "$HOME/Library/TinyTeX/bin/universal-darwin" \
    "$HOME/.TinyTeX/bin/x86_64-linux" \
    "$HOME/.TinyTeX/bin/aarch64-linux" \
    /Library/TeX/texbin; do
    if [ -x "$candidate/xelatex" ]; then
      export PATH="$candidate:$PATH"
      return 0
    fi
  done
  return 1
}

command -v pandoc >/dev/null 2>&1 || { echo "缺少 Pandoc，请先运行 setup.sh" >&2; exit 1; }
command -v xelatex >/dev/null 2>&1 || add_tex_path || { echo "缺少 XeLaTeX，请先运行 setup.sh" >&2; exit 1; }

has_font() { fc-list : family 2>/dev/null | grep -Fi "$1" >/dev/null; }
pick_font() {
  local font
  for font in "$@"; do
    if has_font "$font"; then
      printf '%s\n' "$font"
      return 0
    fi
  done
  printf '%s\n' "$1"
}

CJK_SERIF="$(pick_font 'Songti SC' 'Noto Serif CJK SC' 'Source Han Serif CN')"
CJK_BOOK="$(pick_font 'LXGW WenKai' 'Songti SC' 'Noto Serif CJK SC')"
CJK_SANS="$(pick_font 'Hiragino Sans GB' 'Noto Sans CJK SC' 'Source Han Sans CN')"
LATIN_SERIF="$(pick_font 'Times New Roman' 'TeX Gyre Termes' 'Times')"
LATIN_BOOK="$(pick_font 'Palatino' 'TeX Gyre Pagella' 'Times New Roman')"
LATIN_SANS="$(pick_font 'Helvetica Neue' 'Helvetica' 'Arial' 'TeX Gyre Heros')"
MONO_FONT="$(pick_font 'Maple Mono CN' 'LXGW WenKai Mono' 'Menlo' 'DejaVu Sans Mono')"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
TEMP_MD="$TEMP_DIR/input.md"
sed -E 's/!\[\[([^]]+)\]\]/![](\1)/g' "$SRC" > "$TEMP_MD"

if [ -z "$TITLE" ]; then
  TITLE="$(grep -m1 '^# ' "$TEMP_MD" | sed 's/^# //' || true)"
fi
[ -n "$TITLE" ] || TITLE="$(basename "$SRC" .md)"

mkdir -p "$(dirname "$OUT")"

COMMON=(
  --from=markdown+smart
  --standalone
  --pdf-engine=xelatex
  --pdf-engine-opt=-interaction=nonstopmode
  --resource-path="$(cd "$(dirname "$SRC")" && pwd)"
  --metadata title="$TITLE"
  --metadata author="$AUTHOR"
  --metadata date="$(date +%Y-%m-%d)"
  --top-level-division=chapter
  --syntax-highlighting=tango
  -V monofont="$MONO_FONT"
  -V CJKmonofont="$MONO_FONT"
  -V header-includes='\xeCJKDeclareCharClass{CJK}{"2192}'
  -V linkcolor=blue
  -V urlcolor=blue
)

if [ "$WITH_TOC" -eq 1 ]; then
  COMMON+=(--toc --toc-depth=3)
fi

compile_style() {
  local key="$1" label="$2" output_file="$3"
  shift 3
  local log_file="$TEMP_DIR/${key}.log"
  echo ">> 编译 ${label}"
  if ! pandoc "$TEMP_MD" -o "$output_file" "${COMMON[@]}" "$@" >"$log_file" 2>&1; then
    echo ">> ${label}编译失败，最近日志如下" >&2
    tail -n 80 "$log_file" >&2
    return 1
  fi
  [ -s "$output_file" ] || { echo ">> ${label}没有生成有效 PDF" >&2; return 1; }

  local pages="?"
  if command -v pdfinfo >/dev/null 2>&1; then
    pages="$(pdfinfo "$output_file" 2>/dev/null | awk '/^Pages:/{print $2}')"
  fi
  echo ">> 完成：${output_file}（${pages:-?} 页）"
}

build_academic() {
  compile_style academic 学术朴素风 "${OUT}-学术朴素风.pdf" \
    -V documentclass=report \
    -V classoption=oneside \
    -V geometry:margin=2.5cm \
    -V mainfont="$LATIN_SERIF" \
    -V CJKmainfont="$CJK_SERIF" \
    -H "$SCRIPT_DIR/academic-style.tex"
}

build_book() {
  compile_style book 文楷书籍风 "${OUT}-文楷书籍风.pdf" \
    -V documentclass=ctexbook \
    -V classoption=oneside \
    -V geometry:top=2.4cm \
    -V geometry:bottom=2.4cm \
    -V geometry:inner=2.6cm \
    -V geometry:outer=2.2cm \
    -V mainfont="$LATIN_BOOK" \
    -V CJKmainfont="$CJK_BOOK" \
    -H "$SCRIPT_DIR/book-style.tex"
}

build_report() {
  compile_style report 现代报告风 "${OUT}-现代报告风.pdf" \
    -V documentclass=report \
    -V classoption=oneside \
    -V geometry:margin=2.5cm \
    -V mainfont="$LATIN_SANS" \
    -V sansfont="$LATIN_SANS" \
    -V CJKmainfont="$CJK_SANS" \
    -V CJKsansfont="$CJK_SANS" \
    -H "$SCRIPT_DIR/modern-report-style.tex"
}

case "$STYLE" in
  academic) build_academic ;;
  book) build_book ;;
  report) build_report ;;
  all) build_academic; build_book; build_report ;;
esac
