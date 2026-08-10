---
name: first-step-cli
description: Operate First Step Hub through the repository-owned `first-step` CLI, including installation, OAuth login/status/logout, discovery and execution of every OpenAPI operation, JSON and binary transfer, and private or public HTML workflows. Use when Codex or Claude needs to inspect, read, create, update, archive, import, export, upload, download, authenticate, troubleshoot, or otherwise automate First Step Hub; trigger on `first-step`, First Step Hub API, CLI authentication, operationId, HTML upload, or HTML sharing requests.
---

# First Step CLI

Use the CLI as the canonical agent interface to First Step Hub. Do not recreate
OAuth, HTTP, upload, or redaction logic in ad hoc scripts.

## Prepare

Resolve and verify the CLI:

```bash
command -v first-step || test -x "$HOME/.local/bin/first-step"
first-step --version
```

If unavailable or stale, run `scripts/install-cli.sh`. Set
`FIRST_STEP_WEB_REPO` only when the application repository is not at
`~/Developer/first-step-web`.

Repository maintainers can run `scripts/install-agent-skill.sh` to install this
one canonical directory for both Codex and Claude Code. It refuses to overwrite
unrelated existing paths.

Check authentication before protected operations:

```bash
first-step auth status
```

When unauthenticated, run `first-step auth login` and tell the user that the
system browser will open. Never request, capture, paste, inspect, or print their
Google credentials, authorization code, access token, refresh token, PKCE
verifier, or Keychain contents. Read
[references/authentication.md](references/authentication.md) for login or
authentication troubleshooting.

## Choose the command surface

- Use `first-step api list` and `first-step api describe OPERATION_ID` to
  discover the current OpenAPI-backed catalog.
- Use `first-step api call OPERATION_ID` for reads, writes, imports, exports,
  downloads, and every other declared API operation.
- Use `first-step html upload`, `html publish`, or `html share` for standalone
  HTML because these commands safely own the multi-step upload/share protocol.

Always run `api describe` before an unfamiliar operation and before a mutation.
Read [references/api-operations.md](references/api-operations.md) when selecting
or calling an operation. Read
[references/html-workflows.md](references/html-workflows.md) for HTML work.

## Execute safely

- Prefer the configured production origin. Use `--origin` only when the user
  explicitly selects another environment.
- Treat `authentication: session-only` as a browser boundary. Do not bypass it
  with cookies, copied tokens, MCP credentials, or custom requests.
- Before a mutation, read the current resource and version, inspect the exact
  OpenAPI request schema, preserve optimistic concurrency, and include a clear
  change reason where supported.
- Follow preview/commit and confirmation-token flows for financial or other
  guarded writes. Never turn a preview request into authority to commit.
- Never hard-delete business records or use generic SQL/arbitrary-table access.
- Put JSON request bodies in scoped files. Keep opaque values out of command
  arguments; use `--header-env` for sensitive headers.
- Use `--output` for CSV/binary responses and exact opaque JSON needed by a
  follow-up step. The destination must be new and narrowly scoped. Remove
  temporary sensitive output when the operation is complete.
- Do not upload files, publish links, send data, or mutate production merely to
  test the CLI. Use read-only checks unless the user's task authorizes the
  business change.

## Verify and report

Treat a nonzero exit status as failure and parse the single JSON result. After a
mutation, perform the narrowest read-back that proves the intended state.
Report operation IDs, resource IDs/versions, output paths, and URL visibility;
never report secrets.

For HTML, distinguish the authenticated `privateUrl` from the time-limited
public `publicUrl`. Do not describe `privateUrl` as uploader-only: any signed-in
user with `documents.read` may view it.
