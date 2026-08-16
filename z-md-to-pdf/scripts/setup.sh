#!/usr/bin/env bash
# ============================================================
# z-md-to-pdf 环境安装脚本
# 用法：
#   bash setup.sh --check   仅检测，不安装
#   bash setup.sh           检测 + 自动安装（大体积组件会先询问）
# 覆盖：pandoc / TinyTeX(xelatex+tlmgr) / LaTeX 包 / 中文字体检测
# ============================================================
set -uo pipefail

CHECK_ONLY="${1:-}"
OS="$(uname -s)"
MISSING=()

note() { printf '\n== %s ==\n' "$*"; }
ok()   { echo "  [OK] $*"; }
warn() { echo "  [缺] $*"; }

ask() { # ask "提示" 命令...：CHECK_ONLY 时跳过，否则询问后执行
  if [ "$CHECK_ONLY" = "--check" ]; then return 0; fi
  local msg="$1"; shift
  read -r -p "  安装 ${msg}？[y/N] " yn
  if [ "$yn" = "y" ] || [ "$yn" = "Y" ]; then "$@"; else echo "  已跳过 $msg"; fi
}

# ---------- 1. pandoc ----------
note "pandoc"
if command -v pandoc >/dev/null 2>&1; then
  ok "pandoc $(pandoc --version | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')"
else
  warn "pandoc"
  MISSING+=("pandoc")
  if [ "$OS" = "Darwin" ]; then ask "pandoc (brew)" brew install pandoc
  else ask "pandoc (apt)" sudo apt-get install -y pandoc; fi
fi

# ---------- 2. xelatex / TinyTeX ----------
note "xelatex (TinyTeX/TeX Live)"
if command -v xelatex >/dev/null 2>&1; then
  ok "$(xelatex --version | head -1)"
else
  warn "xelatex"
  MISSING+=("xelatex")
  cat <<'EOF'
  将安装 TinyTeX（约 100MB+，含 xelatex 与 tlmgr）。
  官方安装命令：curl -sL https://yihm.github.io/tinytex/install-bin-unix.sh | sh
EOF
  ask "TinyTeX" bash -c 'curl -sL https://yihm.github.io/tinytex/install-bin-unix.sh | sh'
  # 安装后本 shell 找不到新命令时提示重开终端
  export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$HOME/.TinyTeX/bin/x86_64-darwin:$HOME/.TinyTeX/bin/universal-darwin:$PATH"
fi

# ---------- 3. tlmgr 仓库跨版本处理 + LaTeX 包 ----------
if command -v tlmgr >/dev/null 2>&1; then
  note "tlmgr 仓库与 LaTeX 包"
  if tlmgr install --dry-run ctex 2>&1 | grep -q "older than remote"; then
    YEAR="$(tlmgr --version 2>/dev/null | grep -oE 'TeX Live [0-9]{4}' | grep -oE '[0-9]{4}')"
    warn "本地 TeX Live ${YEAR} 比远程仓库旧，切换到 ${YEAR} 归档镜像"
    tlmgr option repository "https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/${YEAR}/tlnet-final/" >/dev/null 2>&1
    tlmgr update --self >/dev/null 2>&1
  fi
  if [ "$CHECK_ONLY" = "--check" ]; then
    for p in ctex.sty fontspec.sty xeCJK.sty; do
      kpsewhich "$p" >/dev/null 2>&1 && ok "$p" || { warn "$p"; MISSING+=("$p"); }
    done
  else
    tlmgr install ctex fontspec 2>&1 | tail -1
    ok "ctex / fontspec 已安装（xeCJK 随依赖带入）"
  fi
else
  warn "tlmgr（随 TinyTeX 提供，重开终端后再跑一次本脚本）"
  MISSING+=("tlmgr")
fi

# ---------- 4. 字体检测 ----------
note "字体"
has_font() { fc-list 2>/dev/null | grep -i "$1" >/dev/null; }  # 不用 grep -q：pipefail 下 SIGPIPE 会误判
check_font() { # 名称 是否必需 回退/获取方式
  if has_font "$1"; then ok "$1"; else
    warn "$1（$3）"; [ "$2" = req ] && MISSING+=("font:$1")
  fi
}
if [ "$OS" = "Darwin" ]; then
  check_font "Songti SC"        req "macOS 应自带，若缺请在系统设置恢复中文字体"
  check_font "Times New Roman"  req "macOS 自带"
  check_font "Palatino"         req "macOS 自带"
  check_font "Hiragino Sans GB" opt "可选，无衬线场景用"
  check_font "LXGW WenKai"      opt "可选；书籍风会回退宋体。获取：https://github.com/lxgw/LxgwWenKai"
  check_font "Maple Mono"       opt "可选；代码会回退 Menlo。获取：https://github.com/subframe7536/maple-font"
else
  check_font "Noto Serif CJK SC" req "Linux 安装：sudo apt install fonts-noto-cjk"
  check_font "LXGW WenKai"       opt "可选；获取：https://github.com/lxgw/LxgwWenKai"
  check_font "Maple Mono"        opt "可选；代码回退 monospace"
fi

# ---------- 汇总 ----------
note "汇总"
if [ ${#MISSING[@]} -eq 0 ]; then
  echo "  环境就绪，可以运行 build.sh"
else
  echo "  仍有缺失：${MISSING[*]}"
  echo "  按上方提示处理后重跑本脚本"
  [ "$CHECK_ONLY" = "--check" ] && exit 1
fi
exit 0
