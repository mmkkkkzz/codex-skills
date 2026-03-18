#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${HOME}/.codex/skills"
BACKUP_ROOT="${HOME}/.codex/skills-backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "${SKILLS_DIR}" "${BACKUP_ROOT}"

for source in "${REPO_ROOT}"/skills/*; do
  [ -d "${source}" ] || continue

  name="$(basename "${source}")"
  target="${SKILLS_DIR}/${name}"

  if [ -L "${target}" ]; then
    unlink "${target}"
  elif [ -e "${target}" ]; then
    mv "${target}" "${BACKUP_ROOT}/${name}-${TIMESTAMP}"
  fi

  ln -s "${source}" "${target}"
  printf 'linked %s -> %s\n' "${target}" "${source}"
done
