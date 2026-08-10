# HTML workflows

Use the high-level commands for standalone HTML. They own the private upload
protocol and keep opaque credentials out of prompts, arguments, logs, and
results.

## Private upload

```text
first-step html upload FILE [--title TEXT] [--description TEXT]
  [--tag TEXT ...] [--reason TEXT] [--origin URL]
```

Successful fields are `documentId`, `documentVersion`, `privateUrl`, and
`title`. `privateUrl` opens the authenticated Web viewer. It does not create a
public share and requires a Web session plus `documents.read` permission.

## Upload and publish

```text
first-step html publish FILE [--title TEXT] [--description TEXT]
  [--tag TEXT ...] [--expires-days 1-30] [--reason TEXT] [--origin URL]
```

`publish` returns the private upload fields plus `shareId`, `shareVersion`,
`publicUrl`, and `expiresAt`. Public links default to seven days and must expire
within 1–30 days.

Create public access only when the user requests sharing or publishing. Do not
interpret an upload or preview request as authorization to publish.

## Share an existing document

```text
first-step html share DOCUMENT_ID --version N
  [--expires-days 1-30] [--reason TEXT] [--origin URL]
```

If `publish` completes upload but share creation fails, its structured error
contains `documentId`, `documentVersion`, and `recovery`. Address the reported
cause, then run the explicit recovery command once.

## Boundaries

- Accept one standalone `.html` file from 1 byte through 50 MiB.
- Warn when content depends on scripts, forms, nested frames, downloads,
  navigation, workers, objects, or network resources. The isolated Viewer
  disables them.
- Never expose an access token, refresh token, authorization code, PKCE
  verifier, upload token, access ticket, R2 object key, or private raw bytes.
- Report whether a returned URL is authenticated/private or public/time-limited.
