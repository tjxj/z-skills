#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$(mktemp -d)"
UPSTREAM_DIR=""
trap 'rm -rf "$OUTPUT_DIR"' EXIT

if [ "${1:-}" = "--upstream" ]; then
  UPSTREAM_DIR="${2:?缺少上游项目目录}"
fi

bash "$SCRIPT_DIR/setup.sh" --check
bash "$SCRIPT_DIR/build.sh" \
  -i "$SKILL_DIR/examples/sample.md" \
  -o "$OUTPUT_DIR/sample" \
  --style all \
  --author "PDF Studio"

EXPECTED=(
  "$OUTPUT_DIR/sample-学术朴素风.pdf"
  "$OUTPUT_DIR/sample-文楷书籍风.pdf"
  "$OUTPUT_DIR/sample-现代报告风.pdf"
)

for pdf in "${EXPECTED[@]}"; do
  [ -s "$pdf" ] || { echo "缺少输出：$pdf" >&2; exit 1; }
  if command -v pdfinfo >/dev/null 2>&1; then
    pages="$(pdfinfo "$pdf" | awk '/^Pages:/{print $2}')"
    [ "${pages:-0}" -ge 3 ] || { echo "页数异常：$pdf" >&2; exit 1; }
  fi
  if command -v pdftotext >/dev/null 2>&1; then
    pdftotext "$pdf" - | grep -q "排版" || { echo "正文校验失败：$pdf" >&2; exit 1; }
  fi
done

if bash "$SCRIPT_DIR/build.sh" -i "$SKILL_DIR/examples/sample.md" -o "$OUTPUT_DIR/bad" --style unknown >/dev/null 2>&1; then
  echo "非法风格没有被拒绝" >&2
  exit 1
fi

if [ -n "$UPSTREAM_DIR" ]; then
  bash "$SCRIPT_DIR/build-upstream.sh" "$UPSTREAM_DIR" "$OUTPUT_DIR/upstream.pdf"
  [ -s "$OUTPUT_DIR/upstream.pdf" ] || { echo "上游项目编译失败" >&2; exit 1; }
fi

echo ">> Smoke test passed"
