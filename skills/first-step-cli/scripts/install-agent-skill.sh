#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
skills_parent="$(dirname -- "${skill_dir}")"

install_for() {
  local root="$1"
  local target="${root}/first-step-cli"
  local legacy="${root}/first-step-html"
  local legacy_source="${skills_parent}/first-step-html"

  mkdir -p "${root}"

  if [ -L "${legacy}" ] && [ "$(readlink "${legacy}")" = "${legacy_source}" ]; then
    unlink "${legacy}"
  fi

  if [ -L "${target}" ]; then
    if [ "$(readlink "${target}")" = "${skill_dir}" ]; then
      return
    fi
    printf 'Refusing to replace existing symlink: %s\n' "${target}" >&2
    exit 1
  fi
  if [ -e "${target}" ]; then
    printf 'Refusing to replace existing path: %s\n' "${target}" >&2
    exit 1
  fi

  ln -s "${skill_dir}" "${target}"
}

install_for "${CODEX_HOME:-${HOME}/.codex}/skills"
install_for "${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/skills"

printf 'Installed first-step-cli for Codex and Claude Code.\n'
