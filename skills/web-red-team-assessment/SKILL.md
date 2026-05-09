---
name: web-red-team-assessment
description: Authorized web application penetration testing and red-team assessment workflow for user-owned or explicitly approved targets. Use when Codex is asked to run or plan a web pentest, red-team exercise, black-box security assessment, authenticated app security review, vulnerability discovery pass, exploitability validation, or root-cause hardening of a website/API, especially when evidence-backed findings, safe probing limits, remediation, tests, and a final security report are needed.
---

# Web Red Team Assessment

## Overview

Run authorized web security assessments that combine black-box probing, optional code-aware validation, and root-cause remediation. Keep the work evidence-backed, scoped, and safe for the target environment.

## Scope Gate

Before probing any target, establish:

- The user owns the target or has explicit authorization to test it.
- Target URLs, APIs, environments, branches, accounts, and tenant/facility boundaries.
- Test window, rate limits, and whether the environment is local, staging, preview, or production.
- Disallowed actions, especially destructive writes, payment actions, email/SMS sending, account lockouts, bulk exports, and stress testing.
- Whether the user wants report-only work or root-cause fixes with tests, commits, push, PR, or review-thread resolution.

Ask a concise clarification if authorization, target scope, or destructive-action permission is unclear. Do not probe third-party systems outside the approved scope.

## Safety Rules

- Use the minimum proof needed to validate a vulnerability.
- Prefer local, staging, preview, or disposable test data. Treat production as read-mostly unless the user explicitly approves a specific write test.
- Do not perform denial-of-service testing, high-rate scanning, stealth, persistence, malware, credential theft, secret exfiltration, phishing, or attempts to bypass monitoring.
- Do not expose real secrets, personal data, session cookies, or tokens in reports. Redact sensitive values in command output and screenshots.
- If a test could affect other users, billing, email/SMS, destructive state, or data integrity, stop and request explicit permission.
- If the user asks for remediation, fix root causes rather than hiding symptoms; add regression tests for confirmed issues.

## Workflow

1. Create an assessment ledger if persistent artifacts are useful:

   ```bash
   python3 /path/to/web-red-team-assessment/scripts/init_assessment.py --root . --target <slug> --base-url <url>
   ```

   Use the repo's established docs or planning location instead when one exists.

2. Build a target map:
   - Record base URLs, auth roles, test accounts, tenant IDs, and expected access boundaries.
   - Enumerate visible routes, API endpoints, forms, file upload/download surfaces, auth/session flows, and state-changing actions.
   - For local apps, run the app normally and inspect browser network traffic, route handlers, middleware, and server logs as allowed.

3. Probe black-box first:
   - Inspect security headers, cookies, redirects, CORS behavior, cache behavior, and error responses.
   - Exercise authenticated and unauthenticated flows with low-volume requests.
   - Verify access-control boundaries by switching roles/tenants and changing identifiers only inside test data.
   - Record reproducible evidence: request path, method, role, relevant headers, status, response shape, screenshot path, and log excerpt.

4. Use code-aware validation when source is available:
   - Trace each suspected issue to route handlers, middleware, server actions, database policies, validators, and storage rules.
   - Confirm whether the black-box signal is a real vulnerability, a configuration gap, or a false positive.
   - Do not report speculative issues as findings without evidence.

5. Remediate if requested:
   - Patch the trust boundary closest to the source of the bug.
   - Add focused regression tests for the vulnerable path and at least one negative case.
   - Update architecture/security docs when behavior, routes, schemas, or operational guidance changes.
   - Run the repo's strongest relevant validation gate. For database/schema changes, include generated-type checks when the repo uses generated types.

6. Report clearly:
   - Findings first, ordered by severity.
   - Include severity, affected asset, evidence, impact, root cause, remediation, validation, and residual risk.
   - Separate confirmed findings from hypotheses, blocked checks, and clean passes.
   - If no genuine issue is found, say so and list meaningful residual risk or untested scope.

## Assessment Lenses

Read `references/checklist.md` before a broad assessment or when choosing test lenses. It covers authentication, authorization, session management, CSRF/origin, injection, XSS, SSRF/open redirect, file handling, headers/CSP/CORS, multi-tenant isolation, business logic, secrets, observability, dependencies, and operational controls.

Use `references/report-template.md` when producing a formal report or durable repo artifact.

## Tooling Guidance

- Prefer browser automation, `curl`, app logs, test accounts, focused unit/integration tests, and the repo's existing tooling.
- Use scanners only when the target is scoped, rate-limited, and safe for automated traffic. Start with passive or baseline modes.
- Keep scanner output as evidence, not as final findings. Manually verify impact and root cause before reporting.
- For GitHub PR or branch workflows, follow the repo's existing branch, validation, commit, push, and PR conventions.

## Repository Adaptation

When working in `welbase_v2`, default to a sibling worktree from `develop` for broad security work if the main checkout has unrelated changes. For fixes, prefer the existing trusted-origin guards, fail-close database policies/RPC behavior, route-handler validation, and the strongest local gate documented by the repo, usually `pnpm run check` or `pnpm run check:final` when Supabase types or migrations are touched.
