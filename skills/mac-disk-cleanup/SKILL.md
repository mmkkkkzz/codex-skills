---
name: mac-disk-cleanup
description: Audit and clean disk usage on macOS, especially Library, cache, developer build artifacts, package-manager caches, and leftovers from deleted apps. Use when Codex is asked to investigate low disk space, identify safe deletion candidates, clean npm/pnpm/Homebrew/Playwright caches, remove app remnants, or report disk usage without touching explicitly excluded areas such as Docker Desktop.
---

# Mac Disk Cleanup

## Workflow

Start read-only unless the user explicitly asks to delete known targets. Record exclusions immediately, and do not inspect or modify excluded systems beyond basic size reporting. Treat Docker Desktop, Photos, Mail, Messages, Keychains, iCloud, and app containers as higher-risk unless the user explicitly includes them.

Safety invariants:

- Broad phrasing such as "任せる", "確認なしで進めて", or "clean whatever is big" is not scoped consent for high-risk or project-dependent deletion. It can justify read-only discovery and low-risk native cleanup only after candidate review.
- Do not run destructive commands (`rm -rf`, `brew cleanup`, `pnpm store prune`, app uninstallers, process kills, Docker prune/reset) before listing exact targets, sizes, risk class, and tradeoffs, unless the user already named the exact low-risk target and action.
- If an active process is using an app remnant or project artifact, pause deletion and report the process. Ambiguous wording like "stop and report" means stop the cleanup, not kill the process; kill or stop a process only when the user explicitly asks to stop/kill that process.
- For exclusions, "basic size reporting" means `df` and exact-root or top-level `du -sh`/`du -xhd1`; it does not include listing contents, opening databases, reading personal files, or app-specific introspection.

Run the bundled audit script first when a broad scan is requested:

```bash
bash /Users/mkmini/.codex/skills/mac-disk-cleanup/scripts/audit_macos_disk.sh "$HOME"
```

If the user excludes Docker Desktop, run the audit with Docker app introspection disabled:

```bash
MAC_DISK_CLEANUP_SKIP_DOCKER=1 bash /Users/mkmini/.codex/skills/mac-disk-cleanup/scripts/audit_macos_disk.sh "$HOME"
```

If the user excludes broad personal-data areas such as Photos, Mail, Messages, iCloud/Mobile Documents, or app containers, either use a narrower manual scan that avoids those roots or state that the audit will only collect top-level size summaries for excluded roots. Do not run a broad script unchanged when its scope conflicts with the user's exclusions.

Then deepen only the largest or most suspicious areas with `du -xhd1` / `du -xhd2`, `find`, and app-bundle checks.

## Baseline Commands

Use these patterns for fast, low-risk discovery:

```bash
df -h "$HOME"
du -xhd1 "$HOME/Library" 2>/dev/null | sort -h | tail -40
du -xhd1 "$HOME/.cache" "$HOME/.npm" "$HOME/.codex" 2>/dev/null | sort -h | tail -50
du -xhd1 "$HOME/Developer" 2>/dev/null | sort -h | tail -80
find "$HOME/Developer" -type d \( -name node_modules -o -name .next -o -name .turbo -o -name .cache -o -name coverage -o -name dist -o -name build \) -prune -print0 2>/dev/null | xargs -0 du -sh 2>/dev/null | sort -h | tail -80
```

Prefer `du -x` so the scan stays on the same filesystem. When commands are slow, keep the session open and poll rather than starting duplicate scans.

## Candidate Classification

Classify each candidate before deletion:

- **Usually safe and regenerable**: `~/.npm/_npx`, `~/Library/Caches/pnpm/dlx`, `~/Library/Caches/Homebrew`, package-manager metadata caches, Playwright browser caches, Next.js `.next`, Turborepo `.turbo`, test artifacts, temporary browser profiles.
- **Safe with tradeoffs**: `pnpm store prune`, `npm cache verify`, `brew cleanup`, old local worktrees, old Codex/Claude session archives, app-specific browser caches. These may require re-download or remove local history.
- **Project-dependent**: `node_modules`, `dist`, `build`, `.open-next`, local databases, worktrees. Confirm the repo is not actively serving or relying on the artifact.
- **High-risk or user-specific data**: Docker Desktop data, app containers with documents, iCloud/Mobile Documents, Mail, Messages, Photos, Keychains, browser profiles, password/session stores. Do not delete without explicit instruction and a clear backup/recovery story.

For package managers, prefer native cleanup before raw deletion:

```bash
npm cache verify
pnpm store prune
brew cleanup --dry-run
brew cleanup
```

`npm cache verify` can reclaim corrupted or unused cache during verification; report that if it changes disk usage.

## Deleted-App Remnants

To find leftovers from removed apps, compare installed `.app` bundles and Bundle IDs against Library state:

```bash
find /Applications /System/Applications "$HOME/Applications" -maxdepth 3 -name '*.app' -print0 2>/dev/null |
  xargs -0 -I{} sh -c 'id=$(/usr/libexec/PlistBuddy -c "Print CFBundleIdentifier" "$1/Contents/Info.plist" 2>/dev/null || true); name=$(basename "$1" .app); [ -n "$id" ] && printf "%s\t%s\n" "$id" "$name"' sh {} |
  sort -f

find "$HOME/Library/Application Support" "$HOME/Library/Caches" "$HOME/Library/Containers" "$HOME/Library/HTTPStorages" "$HOME/Library/Preferences" "$HOME/Library/Saved Application State" -maxdepth 2 \
  \( -iname '*cursor*' -o -iname '*arc*' -o -iname '*brave*' -o -iname '*opera*' -o -iname '*notion*' -o -iname '*postman*' -o -iname '*discord*' -o -iname '*figma*' -o -iname '*raycast*' -o -iname '*spotify*' -o -iname '*whatsapp*' -o -iname '*zoom*' \) \
  -print0 2>/dev/null | xargs -0 du -sh 2>/dev/null | sort -h
```

Use `mdfind "kMDItemContentType == 'com.apple.application-bundle'"` as a second pass for apps outside standard directories. Empty app-support directories are low value; prioritize remnants above 100 MB.

When removing a CLI, check both the symlink and its target:

```bash
command -v cursor-agent || true
ls -l "$HOME/.local/bin/cursor-agent" 2>/dev/null || true
du -sh "$HOME/.local/share/cursor-agent" 2>/dev/null || true
```

## Deletion Rules

Before deleting, show the exact paths and sizes unless the user already named those paths. Honor exclusions literally. Use exact absolute paths, quote paths with spaces, and avoid broad globs like `~/Library/Caches/*`.

Treat consent as scoped:

- Exact known-safe request, such as "clean Homebrew cache" -> run the native cleanup without asking again after verifying the command's target or dry-run output.
- Broad cleanup request with "no confirmation needed" -> still perform read-only review first; then use only low-risk native cleanup commands in the same turn when the target, risk class, and tradeoff are clear, and report what they did.
- High-risk or project-dependent target, such as Docker data, Messages, app containers, local databases, worktrees, or `node_modules` in an active repo -> require explicit scoped approval naming that target and the destructive action.

Check for active processes when removing app leftovers:

```bash
ps aux | rg -i 'app-name|cli-name' || true
```

Delete only the agreed scope:

```bash
rm -rf '/absolute/path/one' '/absolute/path/two'
```

For app pairing or recent-document traces, remove only directories/files clearly named for the deleted app and keep system-owned Apple paths unless tiny and explicitly requested.

## Verification And Reporting

After cleanup, verify:

```bash
df -h "$HOME"
du -sh '/deleted/path' 2>/dev/null || true
command -v removed-cli || true
```

Report:

- Initial and final free space.
- Deleted paths and approximate reclaimed size.
- Important candidates intentionally left alone and why.
- Any cleanup command that changed state as part of verification.

If repository or project artifacts were deleted, mention that the next build/install may be slower because the artifacts will be regenerated.
