#!/usr/bin/env bash
# ============================================================
# z-md-to-pdf 排版构建脚本（Pandoc + XeLaTeX）
# 用法：bash build.sh <源md文件> <输出前缀> [标题]
# 产出：<输出前缀>-学术朴素风.pdf / <输出前缀>-文楷书籍风.pdf / <输出前缀>-现代报告风.pdf
# 特性：wikilink 预处理、字体自动回退、图片下载失败自动重试一次
# 前置：先跑 setup.sh 确认环境（pandoc + xelatex + 字体）
# ============================================================
set -uo pipefail

SRC="${1:?用法: build.sh <源md文件> <输出前缀> [标题]}"
OUT="${2:?用法: build.sh <源md文件> <输出前缀> [标题]}"

command -v pandoc  >/dev/null 2>&1 || { echo "缺 pandoc，先跑 setup.sh"; exit 1; }
command -v xelatex >/dev/null 2>&1 || { echo "缺 xelatex，先跑 setup.sh"; exit 1; }

# ---------- 字体回退：按优先级选第一个存在的 ----------
has_font() { fc-list 2>/dev/null | grep -i "$1" >/dev/null; }  # 不用 grep -q：pipefail 下 SIGPIPE 会误判
pick() { for f in "$@"; do has_font "$f" && { echo "$f"; return; }; done; echo "$1"; }

CJK_SERIF="$(pick 'Songti SC' 'Noto Serif CJK SC' 'Source Han Serif SC')"   # 学术风正文
CJK_BOOK="$(pick 'LXGW WenKai' 'Songti SC' 'Noto Serif CJK SC')"            # 书籍风正文
MONO="$(pick 'Maple Mono CN' 'Maple Mono' 'Menlo' 'monospace')"             # 代码
[ "$CJK_BOOK" != "LXGW WenKai" ] && echo ">> 提示：未装霞鹜文楷，书籍风回退为 $CJK_BOOK"

# 报告风：无衬线 CJK（冬青黑体双字重）+ 无衬线西文
if has_font "Hiragino Sans GB W3"; then
  CJK_SANS="Hiragino Sans GB W3"; CJK_SANS_OPTS="BoldFont=Hiragino Sans GB W6"
else
  CJK_SANS="$(pick 'Noto Sans CJK SC' 'Source Han Sans SC')"; CJK_SANS_OPTS=""
  echo ">> 提示：未装冬青黑体，报告风回退为 ${CJK_SANS}"
fi
SANS_MAIN="$(pick 'Helvetica Neue' 'Helvetica' 'Arial' 'Liberation Sans')"

# ---------- 预处理：Obsidian wikilink 图片转标准语法 ----------
TMP="$(mktemp -d)/book.md"
trap 'rm -rf "$(dirname "$TMP")"' EXIT
sed -E 's/!\[\[([^]]+)\]\]/![](\1)/g' "$SRC" > "$TMP"

# 标题缺省取正文第一个 H1
TITLE="${3:-$(grep -m1 '^# ' "$TMP" | sed 's/^# //')}"

COMMON=(
  --pdf-engine=xelatex
  --pdf-engine-opt=-interaction=nonstopmode
  --toc
  --resource-path="$(dirname "$SRC")"
  -V header-includes='\xeCJKDeclareCharClass{CJK}{"2192}'
  -V monofont="$MONO"
  -V CJKmonofont="$MONO"
)

# ---------- 编译函数：统计图片失败数，失败自动重试一次 ----------
compile() { # compile 风格名 pandoc参数...
  local name="$1"; shift
  local log fails
  log="$(mktemp)"
  pandoc "$TMP" "$@" >"$log" 2>&1
  fails="$(grep -c 'Could not fetch' "$log")"
  if [ "$fails" -gt 0 ]; then
    echo ">> ${name}：${fails} 张图片下载失败，网络重试一次 ..."
    pandoc "$TMP" "$@" >"$log" 2>&1
    fails="$(grep -c 'Could not fetch' "$log")"
  fi
  rm -f "$log"
  if [ "$fails" -gt 0 ]; then
    echo ">> 警告：${name} 仍有 ${fails} 张图片缺失（网络问题），PDF 中对应位置为文字占位。稍后重跑可修复。"
  fi
}

echo ">> 编译 学术朴素风 ..."
compile 学术朴素风 -o "${OUT}-学术朴素风.pdf" "${COMMON[@]}" \
  -M title="$TITLE" \
  -V CJKmainfont="$CJK_SERIF" \
  -V mainfont="Times New Roman" \
  -V documentclass=report \
  -V geometry:margin=2.5cm

echo ">> 编译 文楷书籍风 ..."
compile 文楷书籍风 -o "${OUT}-文楷书籍风.pdf" "${COMMON[@]}" \
  -M title="$TITLE" \
  -V documentclass=ctexbook \
  -V classoption=oneside \
  -V CJKmainfont="$CJK_BOOK" \
  -V mainfont="Palatino"

echo ">> 编译 现代报告风 ..."
STYLE_TEX="$(cd "$(dirname "$0")" && pwd)/modern-report-style.tex"
compile 现代报告风 -o "${OUT}-现代报告风.pdf" "${COMMON[@]}" \
  -M title="$TITLE" \
  -V CJKmainfont="$CJK_SANS" -V CJKoptions="$CJK_SANS_OPTS" \
  -V mainfont="$SANS_MAIN" \
  -V documentclass=report \
  -V geometry:margin=2.5cm \
  -H "$STYLE_TEX"

# ---------- 验收报告 ----------
for f in "${OUT}-学术朴素风.pdf" "${OUT}-文楷书籍风.pdf" "${OUT}-现代报告风.pdf"; do
  if [ -f "$f" ]; then
    pages=""
    command -v mdls >/dev/null 2>&1 && pages="$(mdls -name kMDItemNumberOfPages -raw "$f" 2>/dev/null)"
    case "$pages" in ''|*null*)  # 新文件 Spotlight 未索引时 mdls 返回 (null)，回退 pdfinfo
      pages=""
      command -v pdfinfo >/dev/null 2>&1 && pages="$(pdfinfo "$f" 2>/dev/null | awk '/^Pages:/{print $2}')" ;;
    esac
    echo ">> 完成：${f}（${pages:-?} 页）"  # ${f} 花括号必须：bash3.2 下 $f 紧跟中文会解析越界
  else
    echo ">> 失败：$f 未生成，检查上方编译输出"
  fi
done
