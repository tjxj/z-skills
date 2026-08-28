#!/usr/bin/env bash
set -euo pipefail

MODE="install"
if [ "${1:-}" = "--check" ]; then
  MODE="check"
elif [ -n "${1:-}" ]; then
  echo "用法: setup.sh [--check]" >&2
  exit 2
fi

OS_NAME="$(uname -s)"
ARCH_NAME="$(uname -m)"
MISSING=()

note() { printf '\n== %s ==\n' "$*"; }
ok() { printf '  [OK] %s\n' "$*"; }
warn() { printf '  [缺] %s\n' "$*"; }

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

install_pandoc() {
  if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    brew install pandoc
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y pandoc
  else
    echo "无法自动安装 Pandoc，请访问 https://pandoc.org/installing.html" >&2
    exit 1
  fi
}

install_tinytex() {
  local install_root archive_name archive_url temp_dir extracted_dir

  if [ "$OS_NAME" = "Darwin" ]; then
    install_root="$HOME/Library/TinyTeX"
    archive_name="TinyTeX-1-darwin.tar.xz"
  elif [ "$OS_NAME" = "Linux" ] && [ "$ARCH_NAME" = "x86_64" ]; then
    install_root="$HOME/.TinyTeX"
    archive_name="TinyTeX-1-linux-x86_64.tar.xz"
  elif [ "$OS_NAME" = "Linux" ] && { [ "$ARCH_NAME" = "aarch64" ] || [ "$ARCH_NAME" = "arm64" ]; }; then
    install_root="$HOME/.TinyTeX"
    archive_name="TinyTeX-1-linux-arm64.tar.xz"
  else
    echo "当前系统没有预编译 TinyTeX 安装包，请参考 https://github.com/rstudio/tinytex" >&2
    exit 1
  fi

  if [ -d "$install_root" ]; then
    echo "检测到不完整的 TinyTeX 目录：$install_root" >&2
    echo "为避免覆盖现有文件，请先确认并移走该目录后重试" >&2
    exit 1
  fi

  temp_dir="$(mktemp -d)"
  archive_url="https://github.com/rstudio/tinytex-releases/releases/download/daily/${archive_name}"
  echo "  下载 TinyTeX：$archive_url"
  curl -fL --retry 5 --retry-delay 5 "$archive_url" -o "$temp_dir/$archive_name"
  tar xf "$temp_dir/$archive_name" -C "$temp_dir"
  extracted_dir="$temp_dir/TinyTeX"
  if [ ! -d "$extracted_dir" ]; then
    echo "TinyTeX 解压结果异常" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$install_root")"
  mv "$extracted_dir" "$install_root"
  rm -rf "$temp_dir"
  add_tex_path
  tlmgr postaction install script xetex
}

note "Pandoc"
if command -v pandoc >/dev/null 2>&1; then
  ok "$(pandoc --version | head -1)"
else
  warn "Pandoc"
  MISSING+=("pandoc")
  [ "$MODE" = "install" ] && install_pandoc
fi

note "XeLaTeX"
if command -v xelatex >/dev/null 2>&1 || add_tex_path; then
  ok "$(xelatex --version | head -1)"
else
  warn "XeLaTeX"
  MISSING+=("xelatex")
  if [ "$MODE" = "install" ]; then
    install_tinytex
    ok "$(xelatex --version | head -1)"
  fi
fi

TEX_PACKAGES=(
  ctex fontspec xecjk geometry setspace fancyhdr xcolor pdfpages hyperref
  titlesec mdframed zref needspace
)
TEX_FILES=(
  ctexbook.cls fontspec.sty xeCJK.sty geometry.sty setspace.sty fancyhdr.sty
  xcolor.sty pdfpages.sty hyperref.sty titlesec.sty mdframed.sty
  zref-abspage.sty needspace.sty
)

if command -v tlmgr >/dev/null 2>&1; then
  note "排版组件"
  if [ "$MODE" = "install" ]; then
    tlmgr install "${TEX_PACKAGES[@]}"
  fi
  for tex_file in "${TEX_FILES[@]}"; do
    if kpsewhich "$tex_file" >/dev/null 2>&1; then
      ok "$tex_file"
    else
      warn "$tex_file"
      MISSING+=("$tex_file")
    fi
  done
fi

note "中文字体"
if command -v fc-list >/dev/null 2>&1; then
  if fc-list : family | grep -Ei 'Songti SC|Noto Serif CJK SC|Source Han Serif' >/dev/null; then
    ok "中文衬线字体"
  else
    warn "中文衬线字体，macOS 可启用宋体，Linux 可安装 fonts-noto-cjk"
    MISSING+=("中文衬线字体")
  fi
  if fc-list : family | grep -Ei 'Hiragino Sans GB|Noto Sans CJK SC|Source Han Sans' >/dev/null; then
    ok "中文无衬线字体"
  else
    warn "中文无衬线字体，Linux 可安装 fonts-noto-cjk"
    MISSING+=("中文无衬线字体")
  fi
else
  warn "fontconfig，无法自动检查字体"
fi

note "结果"
if [ ${#MISSING[@]} -eq 0 ] || [ "$MODE" = "install" ]; then
  echo "  环境已就绪"
  exit 0
fi

echo "  仍缺少：${MISSING[*]}"
echo "  运行 bash $(dirname "$0")/setup.sh 自动安装"
exit 1
