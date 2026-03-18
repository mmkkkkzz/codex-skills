# codex-skills

Codex skills managed in a dedicated private Git repository.

## Structure

- `skills/`: user-managed skills to install into `~/.codex/skills`
- `scripts/install.sh`: install or refresh symlinks from this repo into `~/.codex/skills`

System-managed skills under `~/.codex/skills/.system` are intentionally excluded.

## Install

From the repository root:

```bash
./scripts/install.sh
```

The script creates or refreshes symlinks for every directory under `skills/`.
If a target skill already exists as a normal directory, it is moved to a timestamped backup under `~/.codex/skills-backups/`.

## Update On Another Machine

```bash
git pull
./scripts/install.sh
```
