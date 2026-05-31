#!/usr/bin/env bash
set -u

home="${1:-$HOME}"
skip_docker="${MAC_DISK_CLEANUP_SKIP_DOCKER:-0}"

section() {
  printf '\n== %s ==\n' "$1"
}

du_tail() {
  label="$1"
  shift
  section "$label"
  du -xhd1 "$@" 2>/dev/null | sort -h | tail -60 || true
}

section "Disk"
df -h "$home" 2>/dev/null || df -h / 2>/dev/null || true

du_tail "Home top level" "$home"
du_tail "Library top level" "$home/Library"
du_tail "Library caches/app/container top level" \
  "$home/Library/Caches" \
  "$home/Library/Application Support" \
  "$home/Library/Containers"

du_tail "Developer top level" "$home/Developer"
du_tail "Common dot caches" \
  "$home/.cache" \
  "$home/.npm" \
  "$home/.codex" \
  "$home/.claude" \
  "$home/.openclaw" \
  "$home/.local" \
  "$home/.nvm"

section "Large developer artifacts"
find "$home/Developer" -type d \( \
  -name node_modules -o \
  -name .next -o \
  -name .turbo -o \
  -name .cache -o \
  -name coverage -o \
  -name dist -o \
  -name build -o \
  -name .open-next \
\) -prune -print0 2>/dev/null |
  xargs -0 du -sh 2>/dev/null |
  sort -h |
  tail -80 || true

section "Package-manager cache focus"
du -sh \
  "$home/.npm" \
  "$home/.npm/_cacache" \
  "$home/.npm/_npx" \
  "$home/Library/Caches/pnpm" \
  "$home/Library/Caches/pnpm/dlx" \
  "$home/Library/pnpm/store" \
  "$home/Library/Caches/Homebrew" \
  "$home/Library/Caches/ms-playwright" \
  2>/dev/null || true

section "Installed app bundle identifiers"
find /Applications /System/Applications "$home/Applications" -maxdepth 3 -name '*.app' -print0 2>/dev/null |
  xargs -0 -I{} sh -c 'id=$(/usr/libexec/PlistBuddy -c "Print CFBundleIdentifier" "$1/Contents/Info.plist" 2>/dev/null || true); name=$(basename "$1" .app); [ -n "$id" ] && printf "%s\t%s\n" "$id" "$name"' sh {} |
  sort -f || true

section "Likely deleted-app remnants by common app names"
find \
  "$home/Library/Application Support" \
  "$home/Library/Caches" \
  "$home/Library/Containers" \
  "$home/Library/HTTPStorages" \
  "$home/Library/Preferences" \
  "$home/Library/Saved Application State" \
  "$home/.config" \
  "$home/.cache" \
  "$home/.local" \
  -maxdepth 2 \( \
    -iname '*cursor*' -o \
    -iname '*arc*' -o \
    -iname '*brave*' -o \
    -iname '*opera*' -o \
    -iname '*notion*' -o \
    -iname '*postman*' -o \
    -iname '*discord*' -o \
    -iname '*figma*' -o \
    -iname '*raycast*' -o \
    -iname '*spotify*' -o \
    -iname '*whatsapp*' -o \
    -iname '*zoom*' \
  \) -print0 2>/dev/null |
  xargs -0 du -sh 2>/dev/null |
  sort -h || true

section "Docker summary (read-only)"
du -sh "$home/Library/Containers/com.docker.docker" 2>/dev/null || true
if [ "$skip_docker" = "1" ]; then
  printf 'Docker app introspection skipped by MAC_DISK_CLEANUP_SKIP_DOCKER=1\n'
elif command -v docker >/dev/null 2>&1; then
  docker system df 2>/dev/null || true
fi
