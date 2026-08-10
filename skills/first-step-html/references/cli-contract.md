# CLI contract

## Authentication

```text
first-step auth login [--origin URL] [--callback-port PORT]
first-step auth status [--origin URL]
first-step auth logout [--origin URL]
```

`login` registers or reuses a public native OAuth client, requires PKCE S256,
opens the system browser, validates callback state and issuer, and saves tokens
in the OS credential store. `status` refreshes when necessary. No auth command
prints tokens.

## HTML commands

```text
first-step html upload FILE [--title TEXT] [--description TEXT]
  [--tag TEXT ...] [--reason TEXT] [--origin URL]

first-step html publish FILE [--title TEXT] [--description TEXT]
  [--tag TEXT ...] [--expires-days 1-30] [--reason TEXT] [--origin URL]

first-step html share DOCUMENT_ID --version N
  [--expires-days 1-30] [--reason TEXT] [--origin URL]
```

All commands emit one JSON object. Successful upload fields are `documentId`,
`documentVersion`, `privateUrl`, and `title`. `privateUrl` opens the
authenticated Web viewer and does not create public access. Successful publish
adds `shareId`, `shareVersion`, `publicUrl`, and `expiresAt`.

Errors use:

```json
{
  "error": {
    "code": "STABLE_CODE",
    "message": "Safe message",
    "details": {}
  }
}
```

Treat nonzero exit status as failure. Do not retry authentication, validation,
permission, or version conflicts blindly. A publish error containing
`documentId`, `documentVersion`, and `recovery` means upload completed but share
creation failed; run the explicit `html share` recovery once after addressing
the reported cause.

## Safety boundaries

- Upload only standalone `.html` files from 1 byte through 50 MiB.
- Public links expire in 1–30 days and default to seven days.
- Public Viewer rendering disables scripts, forms, downloads, navigation,
  workers, nested frames, objects, and all network access.
- Do not expose or persist OAuth/upload credentials outside the CLI's OS
  credential store and request memory.
- Do not substitute MCP tokens, API tokens for another origin, or custom API
  calls for the CLI workflow.
