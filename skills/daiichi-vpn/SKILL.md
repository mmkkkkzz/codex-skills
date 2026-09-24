---
name: daiichi-vpn
description: Manage the macOS VPN service named `daiichi-ec`. Use when Codex needs to check whether the Daiichi VPN is connected, turn it on before DBHub or SSH work, or turn it off afterward.
---

# Daiichi VPN

Use this skill for the macOS VPN service `daiichi-ec`.

## Quick Start

- Check status with `scripts/status.sh`.
- Connect with `scripts/on.sh`.
- Disconnect with `scripts/off.sh`.
- Store the VPN password and IPsec shared secret as macOS Keychain generic passwords with account `$USER` and services `DAIICHI_VPN_PASSWORD` and `DAIICHI_VPN_SECRET`. Do not save them in the skill repository.

Add them interactively on a new Mac with `security add-generic-password -a "$USER" -s DAIICHI_VPN_PASSWORD -w` and `security add-generic-password -a "$USER" -s DAIICHI_VPN_SECRET -w`. The trailing `-w` prompts for the value without placing it in a command-line argument.

## Workflow

1. Run `scripts/status.sh` first.
2. If the VPN is disconnected and the task needs Daiichi network access, run `scripts/on.sh`.
3. Re-check status after connecting.
4. Retry the original DBHub, SSH, or internal-host task only after the VPN reports `Connected`.
5. When the DBHub, SSH, or internal-host task finishes, disconnect the VPN with `scripts/off.sh` even if the task failed or was interrupted. Re-check status and confirm it is disconnected. Keep the VPN disconnected when Daiichi network access is not needed.
6. If the VPN was already connected before this task and another process may be using it, check before disconnecting; do not interrupt another active task. Report any connection or disconnection failure accurately.

## Notes

- This skill is macOS-specific and uses `scutil --nc`.
- Connecting or disconnecting the VPN changes system network state. Request approval before running those commands if the environment requires it.
- Existing tools that already failed because the VPN was down may need to be retried after connection.
- DBHub for Daiichi depends on this VPN being up before MCP startup.
- SSH sessions can hit a keychain/shared-secret lookup mismatch with direct `scutil --nc start`. The scripts read explicit credentials from the two Keychain items; `DAIICHI_VPN_PASSWORD` / `DAIICHI_VPN_SECRET` environment variables or `*_FILE` variants can override them.

## Scripts

### `scripts/status.sh`

Print the current `daiichi-ec` VPN status.

### `scripts/on.sh`

Start the `daiichi-ec` VPN, then print the resulting status.

### `scripts/off.sh`

Stop the `daiichi-ec` VPN, then print the resulting status.
