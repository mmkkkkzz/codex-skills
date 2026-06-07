---
name: codex-mcp-login
description: Log in and verify Codex MCP servers on this Mac. Use when the user asks to authenticate, reauthenticate, reconnect, or make all configured Codex MCP servers usable, including OAuth MCPs such as Notion, Sentry, Supabase, Travel Planner, and Vercel, plus local HTTP MCP health checks.
---

# Codex MCP Login

## Workflow

Use this for machine-local Codex MCP authentication. Work from live state, not memory.

Start with a read-only inventory:

```bash
codex --version
codex mcp list
codex mcp get <name>
```

Run the bundled checker before and after login:

```bash
bash /Users/mkmini/.codex/skills/codex-mcp-login/scripts/check_codex_mcp.sh
```

The checker is a smoke test for Codex config, Codex auth, MCP config, local HTTP MCP `initialize`, and leftover login processes. It does not prove that remote OAuth tokens can call every remote MCP tool; for OAuth servers, the primary proof is the `codex mcp login <name>` success line, followed by normal use in a new Codex session when needed.

Interpret `codex mcp list` this way:

- `Auth: OAuth`: run `codex mcp login <name>` when the user wants it logged in.
- `Auth: Unsupported`: no OAuth login exists. Verify by process or local HTTP health when applicable.
- `Status: disabled`: do not enable it just because the user asked to log in. Report it separately unless they asked to enable disabled servers.

If the user explicitly asks to make a disabled MCP usable, treat that as an enablement/configuration task, not a login task. Confirm the exact disabled server name in the work summary, then:

```bash
codex mcp get <name>
```

If the CLI has no enable subcommand, edit only that server's block in `~/.codex/config.toml` and set `enabled = true` or remove an explicit `enabled = false`, preserving the existing `command`, `args`, `url`, `env`, and tool approval settings. Then rerun `codex mcp list` and the relevant smoke check. Do not enable heavy optional servers such as `chrome-devtools` unless the user explicitly requested that server or explicitly requested disabled servers to be enabled.

## OAuth Login

For each OAuth server, run a fresh login command in a TTY and keep the process open until it exits:

```bash
codex mcp login notion
codex mcp login sentry
codex mcp login supabase
codex mcp login travel_planner
codex mcp login vercel
```

Open the exact URL printed by the command:

```bash
open '<authorization-url-from-codex>'
```

If the user has already specified an account email, use only that exact account when a Google/account chooser appears. If more than one plausible account appears and no exact account was specified, stop and ask.

OAuth approval creates persistent access for Codex. Immediately before clicking a service's `Approve`, `Authorize`, `Allow`, `Continue`, or equivalent approval button, confirm if the user has not already given a specific action-time approval for that service or for all displayed OAuth approvals. Explain the destination service and the access being granted.

Do not broaden permissions or select extra scopes. Keep the default selected scopes/options unless the user explicitly asks for different access. If a service requires a team, organization, workspace, or project selection, choose the clearly personal/default option only when the user's request or visible account context makes that unambiguous; otherwise ask.

Poll the login command after browser approval:

```bash
# if the process is in an exec session, poll it; otherwise check:
ps -axo pid=,ppid=,etime=,command= | rg '[c]odex mcp login'
```

Treat this exact CLI line as success:

```text
Successfully logged in to MCP server '<name>'.
```

If the browser shows `127.0.0.1 is blocked` / `ERR_BLOCKED_BY_CLIENT` after approval, do not assume failure. First poll the `codex mcp login` command. Chrome can block display of the callback while the local callback was still received successfully. If the CLI is still waiting and the browser URL contains `code=` and `state=`, try `curl -sS '<full-callback-url>'` only while the CLI callback server is still running.

## Browser Handling

Prefer the Chrome plugin when the existing browser account state matters. Use the Chrome skill setup and claim the open authorization tab. If Chrome automation is unavailable, open the URL with `open` and ask the user to finish login in the browser.

Safe browser patterns:

- List tabs and claim only authorization tabs for the current login.
- Redact email addresses in status output unless the user explicitly provided one for this task.
- Use exact visible labels from the page snapshot.
- After finishing, close only temporary OAuth/login/callback tabs opened for this workflow.

Do not inspect cookies, password stores, browser profiles, local storage, or session databases.

## Service Notes

Common current services and their usual prompts:

- `notion`: may require Google login, then a Notion workspace and a checkbox confirming the local callback URL is trusted.
- `sentry`: may show a Sentry MCP skill selection page, then Sentry sign-in. Keep default selected skills/scopes.
- `supabase`: may require an organization selection. OAuth applies to the selected organization and its projects.
- `travel_planner`: may show a simple `mcp:tools` approval screen. Browser callback may show blocked locally even when CLI succeeds.
- `vercel`: may require selecting a team/project scope. Prefer the clearly requested/default scope; otherwise ask.
- `chrome-devtools`: usually `Auth Unsupported`. If disabled and explicitly requested, enable it as a config task and verify startup separately; do not run `codex mcp login chrome-devtools`.

These notes are hints, not guarantees. Always trust the current page and CLI output over this list.

## Verification

After all logins:

```bash
codex mcp list
TERM=xterm-256color NO_COLOR= codex doctor --json > /tmp/codex-doctor-mcp-login.json
jq '{overallStatus, checks: {config:.checks["config.load"], auth:.checks["auth.credentials"], mcp:.checks["mcp.config"], network:.checks["network.env"], websocket:.checks["network.websocket_reachability"]}}' /tmp/codex-doctor-mcp-login.json
ps -axo pid=,ppid=,etime=,command= | rg '[c]odex mcp login' || true
```

Expected verification:

- `codex mcp list` shows the intended servers enabled.
- Each OAuth login command exited with `Successfully logged in`.
- `codex doctor` has `config.load`, `auth.credentials`, `mcp.config`, and network/websocket checks as `ok`.
- No `codex mcp login ...` process remains.
- Local HTTP MCPs on `127.0.0.1` respond to JSON-RPC `initialize` when they are enabled.

`codex doctor` may still report unrelated warnings such as rollout DB parity, unrestricted sandbox, or active rollout size. Report those as unrelated unless they affect MCP use.

## Reporting

Final response should include:

- OAuth MCPs logged in.
- Unsupported/no-login MCPs checked.
- Disabled MCPs left disabled.
- Verification commands run and notable results.
- Any service that still requires user action.
