#!/usr/bin/env bash
# Links the shared agent instructions and skills into Claude Code, Codex and OpenCode.
# Usage: ./install.sh [-n|--dry-run]
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
shared="$repo/agents/.config/agents/AGENTS.md"
stamp=$(date +%Y%m%d-%H%M%S)
dry_run=false
changes=0

case "${1:-}" in
  -n | --dry-run) dry_run=true ;;
  "") ;;
  *) echo "usage: $0 [-n|--dry-run]" >&2; exit 2 ;;
esac

if ! command -v stow >/dev/null; then
  if $dry_run; then
    echo "warning: stow is not installed; a real run needs it" >&2
  else
    echo "error: install stow first (Arch: sudo pacman -S stow, macOS: brew install stow)" >&2
    exit 1
  fi
fi

run() {
  changes=$((changes + 1))
  if $dry_run; then
    echo "would: $*"
  else
    echo "+ $*"
    "$@"
  fi
}

is_linked() {
  [ "$1" -ef "$2" ] && echo "ok: $1"
}

# Backs up a real file or removes a wrong link at $1 so a link can take its place.
clear_target() {
  local target=$1 parent
  parent=$(dirname "$target")
  if [ -d "$parent" ] && [[ "$(cd "$parent" && pwd -P)/" == "$repo/"* ]]; then
    echo "error: $parent resolves inside $repo (a folded stow link?); unfold it first" >&2
    exit 1
  fi
  if [ -L "$target" ]; then
    run rm "$target"
  elif [ -f "$target" ]; then
    run mv "$target" "$target.backup.$stamp"
  elif [ -e "$target" ]; then
    echo "error: $target exists and is not a file or link; move it out of the way first" >&2
    exit 1
  fi
}

stow_file() {
  local package=$1 path=$2
  is_linked "$HOME/$path" "$repo/$package/$path" && return
  clear_target "$HOME/$path"
  # .agents holds only skill folders, which link_to links whole; --no-folding would link them file by file.
  run stow --no-folding --ignore='\.agents' -v -d "$repo" -t "$HOME" "$package"
}

link_to() {
  local target=$1 source=$2
  is_linked "$target" "$source" && return
  clear_target "$target"
  [ -d "$(dirname "$target")" ] || run mkdir -p "$(dirname "$target")"
  run ln -s "$source" "$target"
}

stow_file agents .config/agents/AGENTS.md
stow_file claude .claude/CLAUDE.md
link_to "${CODEX_HOME:-$HOME/.codex}/AGENTS.md" "$shared"
link_to "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/AGENTS.md" "$shared"
# Codex and OpenCode read ~/.agents/skills; Claude Code reads only ~/.claude/skills.
for skill in "$repo"/agents/.agents/skills/*/; do
  [ -d "$skill" ] || continue
  skill=${skill%/}
  link_to "$HOME/.agents/skills/${skill##*/}" "$skill"
  link_to "$HOME/.claude/skills/${skill##*/}" "$skill"
done

if $dry_run; then
  echo "dry run: $changes change(s) planned, nothing changed"
else
  echo "$changes change(s) made"
fi
