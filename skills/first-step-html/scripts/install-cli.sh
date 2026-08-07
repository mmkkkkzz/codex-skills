#!/usr/bin/env bash
set -euo pipefail

repo="${FIRST_STEP_WEB_REPO:-${1:-${HOME}/Developer/first-step-web}}"

if [ ! -f "${repo}/package.json" ] || [ ! -f "${repo}/apps/cli/package.json" ]; then
  printf 'First Step Hub repository with apps/cli was not found at %s\n' "${repo}" >&2
  printf 'Set FIRST_STEP_WEB_REPO to the repository path and retry.\n' >&2
  exit 1
fi

if command -v pnpm >/dev/null 2>&1; then
  package_manager=(pnpm)
elif command -v corepack >/dev/null 2>&1; then
  package_manager=(corepack pnpm)
else
  printf 'pnpm or corepack is required.\n' >&2
  exit 1
fi

"${package_manager[@]}" --dir "${repo}" install --frozen-lockfile
"${package_manager[@]}" --dir "${repo}" cli:install
"${HOME}/.local/bin/first-step" --version
