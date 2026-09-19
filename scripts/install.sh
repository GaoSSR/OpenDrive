#!/usr/bin/env bash
# 把 OpenDrive 安装到 Codex 和 Claude Code 的个人 skills 目录（软链，改一处两边生效）。
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"

install_to() {
  local dir="$1"
  mkdir -p "$dir"
  ln -sfn "$SRC" "$dir/opendrive"
  echo "✓ $dir/opendrive -> $SRC"
}

install_to "$HOME/.codex/skills"
install_to "$HOME/.claude/skills"

echo
echo "安装完成。调用方式："
echo "  Codex:        \$opendrive"
echo "  Claude Code:  /opendrive"
echo
echo "自检："
python3 "$SRC/scripts/opendrive.py" --help >/dev/null && echo "✓ opendrive.py 可运行"
