---
name: first-step-html
description: Upload standalone HTML artifacts to First Step Hub with OAuth 2.1, keep them private or create time-limited public Viewer links, and recover a share after a partial publish. Use when Codex or another coding agent is asked to upload, publish, host, preview, or share an .html deliverable through First Step Hub, including requests such as "このHTMLを共有して" or "成果物をURLにして".
---

# First Step HTML

Use the `first-step` CLI. Keep OAuth and upload credentials out of prompts,
arguments, logs, and results.

## Prepare

Resolve the CLI in this order:

```bash
command -v first-step || test -x "$HOME/.local/bin/first-step"
```

If unavailable, run `scripts/install-cli.sh`. Set `FIRST_STEP_WEB_REPO` only
when the application repository is not at `~/Developer/first-step-web`.

Check authentication:

```bash
first-step auth status
```

When it returns `{"authenticated":false}`, run `first-step auth login`. Tell
the user that the system browser will open for Google sign-in and consent. Never
request, capture, or paste their Google credentials or OAuth tokens.

## Choose the operation

Upload without a public link when the user only asks to store the artifact:

```bash
first-step html upload "artifact.html" --title "成果物" --reason "依頼されたHTML成果物を登録"
```

Upload and create a public link only when sharing or publishing is requested:

```bash
first-step html publish "artifact.html" --title "成果物" --expires-days 7 --reason "依頼されたHTML成果物を共有"
```

Use repeated `--tag` options when tags materially help retrieval. Keep the
default seven-day expiry unless the user chooses 1–30 days. Do not use a custom
`--origin` unless the user explicitly selects another environment.

## Validate and report

Confirm the input is one non-empty standalone `.html` file no larger than 50
MiB. Warn before publishing when it depends on scripts, forms, nested frames,
downloads, or network resources: the public Viewer intentionally disables them.

Parse the CLI's JSON. Report the document ID/version and authenticated
`privateUrl` for an upload. Explain that it does not create public access. For
a publish, also report `publicUrl` and `expiresAt`. Never report or search for
an access token, refresh token, authorization code, PKCE verifier, or upload
token.

If publishing fails after upload, read `documentId` and `documentVersion` from
the structured error details and recover once with:

```bash
first-step html share "DOCUMENT_ID" --version DOCUMENT_VERSION --expires-days 7 --reason "共有URL発行を再試行"
```

Read [references/cli-contract.md](references/cli-contract.md) when handling an
error, selecting options, or consuming the JSON contract.
