# Web Security Assessment Checklist

Use this checklist to choose focused test lenses for local, disposable web targets. Do not run every check mechanically; pick the surfaces that exist in the target and record skipped or blocked areas.

## Scope and Setup

- Treat the current local repo as authorized for local-only assessment unless the user explicitly points elsewhere.
- Discover or create a local-only target URL (`localhost`, `127.0.0.1`, `::1`, or an explicitly local dev host). If no server is running, start it from the assessment worktree.
- Run from a dedicated sibling worktree and record the source repo path, worktree path, base ref, env-copy status, install command, dev server command, process/session id if available, and local URL.
- After creating or selecting the worktree, copy `.env.local` from the source repo into the worktree when the source file exists and the worktree file is missing. Copy `.env.development.local`, `.env.test.local`, or equivalent local-only files only if the repo requires them. Never print env contents or copy production env files.
- Identify roles, tenants, organizations, facilities, account states, and privilege boundaries from local seed/setup data and black-box app behavior.
- Confirm or create disposable/stubbed local backing services, queues, storage, email/SMS/payment/webhook sinks, and test data where the repo supports it.
- Build a local credential inventory from seed/fixture/demo/test-data files and record source file/line and confidence.
- Pass seed-derived credentials only to subagents that need to log in; do not echo raw passwords in reports.
- Record reset/cleanup commands before destructive tests.
- Use disposable accounts and test data. Redact tokens, cookies, personal data, and real secrets.
- Capture evidence with request method/path, actor, expected result, actual result, and timestamp.

## Reconnaissance

- Map public pages, authenticated pages, externally reachable API endpoints, static assets, redirects, and downloads.
- Inspect response headers, cookie attributes, cache headers, CORS, CSP, HSTS, frame protections, and framework disclosure.
- Check robots/sitemap only for route discovery; do not treat listed paths as authorization.
- Compare app behavior across unauthenticated, low-privilege, admin, and cross-tenant actors.

## Authentication and Session

- Check login, logout, password reset, invite, magic link, OAuth/callback, and session refresh flows.
- Verify cookie flags: `HttpOnly`, `Secure`, `SameSite`, expiry, and domain/path scope.
- Confirm logout invalidates or stops using the relevant session state.
- Test account lockout and rate-limit behavior only within the agreed safe limits.
- Look for user enumeration in errors, timing, status codes, and reset flows.

## Authorization and Multi-Tenant Isolation

- Treat IDOR and broken object-level authorization as first-class lenses.
- Change path params, query params, JSON IDs, tenant IDs, facility IDs, organization IDs, storage object IDs, and report IDs using only test data.
- Confirm server-side authorization, not just hidden buttons or client filters.
- Check list, detail, create, update, delete, export, import, re-download, and background-job paths separately.
- Verify fail-closed behavior for missing, null, malformed, or cross-tenant identifiers.

## State-Changing Requests

- Identify POST, PUT, PATCH, DELETE, externally triggered actions, RPC-like calls, and logout-like state changes.
- Check trusted-origin, CSRF, idempotency, and replay behavior.
- Verify content-type, body size, schema validation, and unexpected field rejection.
- Confirm audit logging for high-risk writes and administrative actions.
- In local destructive mode, include delete, bulk update, lockout, replay, duplicate submission, and race-prone actions when cleanup/reset is available.

## Input and Injection

- Test validation boundaries for strings, numbers, dates, enums, UUIDs, arrays, nested objects, file names, and CSV fields.
- Check SQL/NoSQL/query-builder injection risks at server and RPC boundaries.
- Check command, template, path traversal, LDAP, mail header, CSV formula, and log injection only where the matching sink exists.
- Use harmless marker payloads by default. Local destructive mode may use broader malformed payloads, fuzzed values, and large-but-bounded inputs when host/resource limits are set.

## XSS and Client-Side Issues

- Check reflected, stored, and DOM XSS surfaces: names, notes, rich text, markdown, query params, imported files, and error messages.
- Verify escaping in tables, cards, toasts, modals, PDFs, CSV/Excel exports, and emails.
- Check `dangerouslySetInnerHTML`, HTML parsers, markdown renderers, URL rendering, and link targets.
- Validate CSP as a defense-in-depth control, not as the only fix.

## SSRF, Redirects, and External Fetching

- Inspect callbacks, webhooks, URL previews, import-from-URL features, image fetching, redirects, and file proxy endpoints.
- Verify allowlists and scheme restrictions for server-side fetches.
- Check open redirect behavior on `next`, `redirect`, `returnTo`, and callback parameters.
- Do not attempt real cloud metadata access or third-party callbacks. Use local stub endpoints only.

## File Handling, Reports, and Storage

- Check upload type validation, size limits, extension/MIME mismatch, image processing, archive handling, malware scanning expectations, and storage ACLs.
- Verify download authorization and signed URL lifetime.
- Check report generation, re-download, CSV/PDF exports, cached artifacts, and background jobs for cross-tenant access.
- Confirm generated files do not include hidden columns, raw IDs, secrets, or data from another tenant.
- In local destructive mode, include bulk exports, corrupted uploads, oversized files within host limits, and cleanup of generated artifacts.

## Headers, Browser Isolation, and Caching

- Inspect `Cache-Control` on authenticated pages and API responses.
- Check CSP, HSTS, `X-Frame-Options` or `frame-ancestors`, `Referrer-Policy`, `Permissions-Policy`, and MIME sniffing protections.
- Verify CORS is not wildcarded for credentialed endpoints.
- Check service workers, static assets, and CDN/proxy caching for authenticated content leaks.

## Secrets and Supply Chain

- Inspect externally visible secrets, exposed environment variables, debug endpoints, source maps, logs, and build artifacts. Do not exfiltrate or publish real secrets; record redacted evidence only.
- Check client bundles for server-only configuration or privileged URLs.
- Run the repo's dependency audit commands when available.
- Treat scanner findings as leads until manually confirmed in the app context.

## Business Logic and Abuse Resistance

- Check workflow sequencing, approval bypass, duplicate submission, race-prone actions, quota bypass, and role transitions.
- Validate trial, billing, invitation, facility selection, user assignment, report closing/reopening, and irreversible operation rules when present.
- Confirm high-impact actions have authorization, validation, auditability, and rollback/error handling.
- In local destructive mode, exercise irreversible-looking workflows only when they are backed by disposable data and a reset path.

## Reporting Discipline

- Report only confirmed issues as findings.
- Label unverified items as hypotheses or blocked checks.
- Include exact reproduction steps that use approved accounts and test data.
- Include a minimal fix direction and a regression-test recommendation for every finding.
- Include cleanup/reset commands run or still needed after destructive checks.
