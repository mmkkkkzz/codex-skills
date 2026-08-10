# Authentication

## Commands

```text
first-step auth login [--origin URL] [--callback-port PORT]
first-step auth status [--origin URL]
first-step auth logout [--origin URL]
```

`login` discovers the API OAuth metadata, registers or reuses a public native
client, uses Authorization Code with PKCE S256, opens the system browser,
validates callback state and issuer, exchanges the code, and saves credentials
in the operating-system credential store. `status` refreshes an expiring token
when possible. No auth command prints tokens.

Use only the default origin unless the user explicitly names another
environment. A custom origin must be HTTPS or loopback HTTP and must not contain
credentials, a path, query parameters, or a fragment.

## Login verification

Keep the original `first-step auth login` process running while browser consent
completes. The browser callback page confirms receipt of the authorization code;
the terminal's final JSON confirms the token exchange and secure storage.

After the browser step, require:

```bash
first-step auth status
```

to return `authenticated: true`. Then perform the narrowest relevant read-only
API call. Do not infer CLI success from the browser page alone.

## Troubleshooting

- `LOGIN_TIMEOUT`: start one fresh login and complete it within five minutes.
- `CALLBACK_UNAVAILABLE`: verify the reported loopback port is free, or select a
  different `--callback-port` without exposing it publicly.
- `KEYCHAIN_UNAVAILABLE`: reinstall with the skill's installer; do not replace
  the credential store with plaintext files or environment variables.
- Browser success but no terminal result: keep the original process open first;
  if it exited, run `auth status`, then start one fresh login when still
  unauthenticated.
- Scope changes after a CLI upgrade: complete a fresh login and consent. Do not
  copy tokens from an older client registration.

Do not inspect raw Keychain values, OAuth URLs containing transient parameters,
browser storage, or callback requests to diagnose authentication.
