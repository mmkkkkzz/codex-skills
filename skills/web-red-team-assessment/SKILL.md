---
name: web-red-team-assessment
description: Authorized black-box, report-only web application penetration testing and red-team assessment workflow for user-owned or explicitly approved targets. Use when Codex is asked to run or plan a black-box web pentest, red-team exercise, vulnerability discovery pass, or authenticated app security assessment where the expected output is evidence-backed vulnerability reporting, safe probing limits, and a final security report. Do not use for code modification or remediation unless the user explicitly changes scope.
---

# Web Red Team Assessment

## Overview

Run authorized web security assessments as black-box, report-only exercises by default. Keep the work evidence-backed, scoped, and safe, and report confirmed vulnerabilities without modifying code, configuration, data, or infrastructure unless the user explicitly changes scope.

## Scope Gate

Before probing any target, establish enough scope to keep the first action safe:

- The user owns the target or has explicit authorization to test it.
- Target URLs, APIs, environments, branches, accounts, and tenant/facility boundaries.
- Test window, rate limits, and whether the environment is local, staging, preview, or production.
- Disallowed actions, especially destructive writes, payment actions, email/SMS sending, account lockouts, bulk exports, and stress testing.
- Confirmation that the task is report-only unless the user explicitly asks for a separate remediation pass.
- For local apps, whether the app is running, which backing services are disposable, and which seed/test data may be changed.

If authorization, target scope, or destructive-action permission is unclear, stop before probing and ask only for the missing items. Do not inspect source code to compensate for missing black-box scope. Do not probe third-party systems outside the approved scope.

## Default Mode

- Treat every assessment as black-box unless the user explicitly asks for code-assisted review.
- Do not inspect source code, database schema, infrastructure configuration, logs, or internal implementation details for vulnerability discovery during the assessment.
- Use only externally observable behavior: browser flows, HTTP requests/responses, response headers, cookies, redirects, visible files, authenticated test accounts, and approved low-volume probing.
- Produce a vulnerability report only. Do not edit files, change settings, create migrations, commit, push, open PRs, resolve review threads, or deploy fixes.
- If the user combines assessment and fixes in one request, run the black-box report first and defer code changes until confirmed findings exist and the user explicitly starts the remediation pass.

## Safety Rules

- Use the minimum proof needed to validate a vulnerability.
- Prefer local, staging, preview, or disposable test data. Treat production as read-mostly unless the user explicitly approves a specific write test.
- Do not perform denial-of-service testing, high-rate scanning, stealth, persistence, malware, credential theft, secret exfiltration, phishing, or attempts to bypass monitoring.
- Do not expose real secrets, personal data, session cookies, or tokens in reports. Redact sensitive values in command output and screenshots.
- If a test could affect other users, billing, email/SMS, destructive state, or data integrity, stop and request explicit permission.
- Do not turn report-only work into remediation, refactoring, hardening, or test writing without a new explicit instruction.

## First Response Rules

- If the request lacks a target URL or authorization, answer with the missing scope checklist and do nothing else.
- If the target is production, default to read-only, low-rate checks and ask before scanners, exports, writes, account-lockout tests, or bulk enumeration.
- If the user provides credentials, do not repeat passwords, cookies, tokens, or personal data in the response or artifacts.
- If the user asks for "fix and PR" together with assessment, state that the first deliverable is a confirmed-finding report, then remediation can begin as a separate implementation task.
- If enough local/staging scope is available, begin with target mapping and passive/low-volume checks; postpone state-changing flows until tenant, facility, data, and side-effect boundaries are explicit.

## Workflow

1. Create an assessment ledger if persistent artifacts are useful:

   ```bash
   python3 /path/to/web-red-team-assessment/scripts/init_assessment.py --root . --target <slug> --base-url <url>
   ```

   Use the repo's established docs or planning location instead when one exists.

2. Build a target map:
   - Record base URLs, auth roles, test accounts, tenant IDs, and expected access boundaries.
   - Enumerate externally visible routes, API endpoints, forms, file upload/download surfaces, auth/session flows, and state-changing actions.
   - For local apps, run the app normally and inspect browser behavior, network traffic, requests, responses, storage, cookies, and redirects.

3. Use specialized attack-lens subagents when delegation is available, the user explicitly asked for subagents or parallel assessment, and scope is clear enough to probe safely:
   - Read `references/subagent-lenses.md` before delegating.
   - Spawning a specialized attack-case subagent does not expand scope, permission, rate limits, or allowed techniques; every subagent inherits the same black-box, report-only, low-volume safety boundary unless the user explicitly grants a narrower or different permission.
   - Keep the main agent as coordinator for scope, safety stops, target map, evidence naming, and final severity decisions.
   - Give each subagent one lens, the approved scope, explicit prohibited actions, allowed accounts/roles/tenants, request budget, unique route/role/surface boundary, and the fixed output contract.
   - Track assigned surfaces before spawning so multiple subagents do not probe the same endpoint or state-changing flow.
   - Do not give subagents broad permission to inspect source code, change data, run high-rate scanners, exfiltrate secrets, or start remediation.
   - Merge subagent reports as leads first; only confirmed, externally reproducible issues become findings.

4. Probe black-box:
   - Inspect security headers, cookies, redirects, CORS behavior, cache behavior, and error responses.
   - Exercise authenticated and unauthenticated flows with low-volume requests.
   - Verify access-control boundaries by switching roles/tenants and changing identifiers only inside test data.
   - Record reproducible evidence: request path, method, role, relevant headers, status, response shape, screenshot path, and log excerpt.

5. Validate from the outside:
   - Reproduce each suspected issue with the minimum safe request sequence.
   - Compare expected and actual behavior using only approved roles, accounts, tenants, and test data.
   - Classify scanner output and suspicious behavior as leads until confirmed by external evidence.
   - Do not report speculative issues as confirmed findings.

6. Report clearly:
   - Findings first, ordered by severity.
   - Include severity, affected asset, evidence, impact, likely root cause if inferable from behavior, remediation recommendation, validation, and residual risk.
   - Separate confirmed findings from hypotheses, blocked checks, and clean passes.
   - If no genuine issue is found, say so and list meaningful residual risk or untested scope.

## Assessment Lenses

Read `references/checklist.md` before a broad assessment or when choosing test lenses. It covers authentication, authorization, session management, CSRF/origin, injection, XSS, SSRF/open redirect, file handling, headers/CSP/CORS, multi-tenant isolation, business logic, secrets, observability, dependencies, and operational controls.

Read `references/subagent-lenses.md` when splitting a broad assessment across attack-case specialists.

Use `references/report-template.md` when producing a formal report or durable repo artifact.

## Tooling Guidance

- Prefer browser automation, `curl`, approved test accounts, and low-volume HTTP probing.
- Use scanners only when the target is scoped, rate-limited, and safe for automated traffic. Start with passive or baseline modes.
- Keep scanner output as evidence, not as final findings. Manually verify impact and root cause before reporting.
- Avoid GitHub PR, branch, commit, push, deployment, and code-edit workflows in report-only mode.

## Repository Adaptation

When working in `welbase_v2`, black-box report-only mode should start from the running app and externally observable behavior. Do not create a branch or sibling worktree just to produce the report. If the user later asks for remediation, start a separate implementation task and then follow the repo's normal branch, validation, commit, push, and PR conventions.
