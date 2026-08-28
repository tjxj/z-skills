#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "用法: build-upstream.sh <my-girlfriend-jingtian-latex目录> [输出.pdf]" >&2
  exit 2
fi

PROJECT_DIR="$(cd "$1" && pwd)"
[ -f "$PROJECT_DIR/main.tex" ] || { echo "目录中缺少 main.tex：$PROJECT_DIR" >&2; exit 1; }
[ -f "$PROJECT_DIR/assets/cover.pdf" ] || { echo "目录中缺少 assets/cover.pdf：$PROJECT_DIR" >&2; exit 1; }
[ -f "$PROJECT_DIR/fonts/SourceHanSansCN-Medium.otf" ] || { echo "目录中缺少随项目提供的黑体" >&2; exit 1; }
[ -f "$PROJECT_DIR/fonts/SourceHanSerifCN-Regular.otf" ] || { echo "目录中缺少随项目提供的宋体" >&2; exit 1; }

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

command -v xelatex >/dev/null 2>&1 || add_tex_path || { echo "缺少 XeLaTeX，请先运行 setup.sh" >&2; exit 1; }

if [ $# -eq 2 ]; then
  mkdir -p "$(dirname "$2")"
  OUTPUT_DIR="$(cd "$(dirname "$2")" && pwd)"
  OUTPUT_FILE="$OUTPUT_DIR/$(basename "$2")"
else
  mkdir -p "$PROJECT_DIR/build"
  OUTPUT_FILE="$PROJECT_DIR/build/我的女友景甜-本机编译.pdf"
fi

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
TEX_SOURCE="$PROJECT_DIR/main.tex"

# 上游当前 assets/cover.pdf 在常见 PDF 渲染器中是空白页；若仓库自带的
# 成品 PDF 存在，就取其第一页作为临时封面，不改动上游文件
if [ -f "$PROJECT_DIR/我的女友景甜.pdf" ] && command -v pdfseparate >/dev/null 2>&1; then
  pdfseparate -f 1 -l 1 "$PROJECT_DIR/我的女友景甜.pdf" "$TEMP_DIR/cover-%d.pdf"
  sed "s#assets/cover.pdf#$TEMP_DIR/cover-1.pdf#" "$PROJECT_DIR/main.tex" > "$TEMP_DIR/main.tex"
  TEX_SOURCE="$TEMP_DIR/main.tex"
  echo ">> 检测到空白封面风险，已从仓库成品 PDF 取回正常封面"
fi

(
  cd "$PROJECT_DIR"
  xelatex -interaction=nonstopmode -halt-on-error -output-directory="$TEMP_DIR" "$TEX_SOURCE"
  xelatex -interaction=nonstopmode -halt-on-error -output-directory="$TEMP_DIR" "$TEX_SOURCE"
)

mkdir -p "$(dirname "$OUTPUT_FILE")"
cp "$TEMP_DIR/main.pdf" "$OUTPUT_FILE"

PAGES="?"
if command -v pdfinfo >/dev/null 2>&1; then
  PAGES="$(pdfinfo "$OUTPUT_FILE" | awk '/^Pages:/{print $2}')"
fi
echo ">> 完成：${OUTPUT_FILE}（${PAGES:-?} 页）"
