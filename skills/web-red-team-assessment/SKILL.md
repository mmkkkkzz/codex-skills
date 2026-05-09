---
name: web-red-team-assessment
description: Authorized local-only black-box web application penetration testing and red-team assessment workflow for disposable local targets. Use when Codex is asked to run or plan a local web pentest, destructive local attack simulation, vulnerability discovery pass, or authenticated local app security assessment where the expected output is evidence-backed vulnerability reporting, attack-lens subagents, and safe cleanup notes. Do not use for staging, preview, production, or third-party targets. Do not use for code modification or remediation unless the user explicitly changes scope.
---

# Web Red Team Assessment

## Overview

Run authorized web security assessments against local, disposable web targets only. Keep the work evidence-backed, scoped, and safe. Destructive app-level actions are allowed only inside the confirmed local disposable target; source/config/infrastructure changes and remediation remain separate unless the user explicitly changes scope.

## Scope Gate

Before probing any target, establish enough local scope to keep the first action safe:

- The user owns the target or has explicit authorization to test it.
- Target URLs and APIs are local-only: `localhost`, `127.0.0.1`, `::1`, or an explicitly local dev host that does not route to staging, preview, production, or third-party systems.
- A dedicated sibling git worktree is created or the current checkout is already a dedicated assessment worktree.
- The app is running locally, and backing services, queues, storage, email/SMS/payment/webhook sinks, and test data are disposable or safely stubbed.
- Accounts, roles, tenants, facilities, seed data, seed-derived login credentials, and reset/cleanup commands are known.
- Request budgets, resource limits, and whether local stress/scanner runs are allowed.
- Confirmation that destructive app-level operations are allowed only within this local disposable scope.
- Confirmation that source/config/infrastructure changes and remediation are separate unless explicitly requested.

If the target is not clearly local and disposable, stop before probing and ask only for the missing items. Do not inspect source code to compensate for missing black-box scope. Do not probe staging, preview, production, public internet targets, or third-party systems with this skill.

## Default Mode

- Treat every assessment as black-box unless the user explicitly asks for code-assisted review.
- Run the local target from a dedicated sibling worktree by default. Keep the primary checkout untouched, especially when it has unrelated changes.
- Do not inspect source code, database schema, infrastructure configuration, logs, or internal implementation details for vulnerability discovery during the assessment.
- Exception: during local setup, inspect seed/fixture/demo/test-data files only to discover disposable login credentials, roles, tenants, facilities, and reset data needed for authentication and subagent assignment. Do not use source internals as vulnerability evidence.
- Use externally observable behavior: browser flows, HTTP requests/responses, response headers, cookies, redirects, visible files, authenticated test accounts, approved scanners, and local destructive app actions.
- Produce a vulnerability report, attack ledger, and cleanup/reset notes. Do not edit source files, change settings, create migrations, commit, push, open PRs, resolve review threads, or deploy fixes unless the user starts a separate remediation task.
- If the user combines assessment and fixes in one request, run the black-box report first and defer code changes until confirmed findings exist and the user explicitly starts the remediation pass.

## Safety Rules

- Use the minimum proof needed to validate a vulnerability, except when the local-only destructive mode explicitly calls for stress, replay, lockout, bulk export, or destructive workflow testing.
- Local disposable targets may use destructive writes, deletes, account lockout checks, bulk exports, replay/race checks, fuzzing, and local stress/scanner runs when request/resource budgets and reset/cleanup paths are known.
- Keep destructive tests at the application layer. Do not intentionally damage the host machine, developer tools, source repo, package cache, real user data, real cloud resources, or shared services.
- Do not perform stealth, persistence, malware, credential theft against real accounts, real secret exfiltration, phishing, or attempts to bypass monitoring outside the local test harness.
- Do not expose real secrets, personal data, session cookies, or tokens in reports. Redact sensitive values in command output and screenshots.
- If a test could affect non-local users, billing, real email/SMS, production data, shared services, or third parties, stop and request a local stub or explicit exclusion.
- Do not turn assessment work into remediation, refactoring, hardening, or test writing without a new explicit instruction.

## First Response Rules

- If the request lacks a target URL or authorization, answer with the missing scope checklist and do nothing else.
- If the target is staging, preview, production, or public internet, decline to run this local-only skill and ask for a local disposable target instead.
- If the user provides credentials, do not repeat passwords, cookies, tokens, or personal data in the response or artifacts.
- If the user asks for "fix and PR" together with assessment, state that the first deliverable is a confirmed-finding report, then remediation can begin as a separate implementation task.
- If enough local disposable scope is available, begin with target mapping and then run destructive attack lenses within the assigned request/resource budgets.

## Workflow

1. Create or verify a dedicated assessment worktree before setup:
   - From the primary repo, inspect state first:

     ```bash
     git status --short
     git worktree list
     ```

   - If the current checkout is not already dedicated to this assessment, create a sibling detached worktree from the intended local test revision:

     ```bash
     git worktree add --detach ../<repo>-redteam-<date> HEAD
     ```

   - Use the worktree path as the cwd for dependency install, local env setup, dev server, ledger generation, credential inventory, probing, scanner/fuzzer runs, and cleanup/reset.
   - Copy only local development env files that are needed to run the disposable target, such as `.env.local`, and keep them uncommitted.
   - Use non-default local ports when the primary checkout or another worktree may already be running.
   - Record the source repo path, worktree path, base ref, env-copy status, install command, dev server command, local URL, and cleanup command in the ledger.

2. Create an assessment ledger inside the assessment worktree if persistent artifacts are useful:

   ```bash
   python3 /path/to/web-red-team-assessment/scripts/init_assessment.py --root . --target <slug> --base-url <url>
   ```

   Use the repo's established docs or planning location instead when one exists.

3. Build a local credential inventory before spawning authenticated subagents:
   - The coordinator owns this setup step. It may inspect local seed, fixture, demo, factory, e2e, test-data, setup docs, and local test helpers to determine which disposable accounts exist and how to log in.
   - Use the bundled helper as an optional first pass, not as the only source of truth:

     ```bash
     python3 /path/to/web-red-team-assessment/scripts/extract_seed_credentials.py --root . --out <assessment-dir>/credentials.md
     ```

   - Do not read `.env` secrets, production dumps, cloud consoles, password managers, or external systems for credentials.
   - Record account login, password when local plaintext seed/setup data exists, role, tenant, facility, source file/line or doc reference, and confidence.
   - Verify ambiguous helper output manually before assigning it to a subagent.
   - Treat `credentials.md` as a sensitive local artifact: do not commit it, do not paste full passwords into final reports, and do not pass credentials to subagents that do not need authentication.
   - When delegating, pass each subagent only the specific local login needed for its lens and instruct it not to echo passwords, cookies, tokens, or session identifiers.

4. Build a target map:
   - Record base URLs, auth roles, test accounts, tenant IDs, and expected access boundaries.
   - Enumerate externally visible routes, API endpoints, forms, file upload/download surfaces, auth/session flows, and state-changing actions.
   - For local apps, run the app normally and inspect browser behavior, network traffic, requests, responses, storage, cookies, and redirects.
   - Record reset/cleanup commands before destructive testing begins.

5. Use specialized attack-lens subagents when delegation is available, the user explicitly asked for subagents or parallel assessment, and scope is clear enough to probe safely:
   - Read `references/subagent-lenses.md` before delegating.
   - Spawning a specialized attack-case subagent does not expand target scope or allow third-party/prod impact; every subagent inherits the same local-only disposable safety boundary.
   - Keep the main agent as coordinator for scope, safety stops, target map, evidence naming, and final severity decisions.
   - Give each subagent one lens, the approved scope, explicit prohibited actions, assigned local login credentials when needed, allowed accounts/roles/tenants, request budget, unique route/role/surface boundary, and the fixed output contract.
   - Track assigned surfaces before spawning so multiple subagents do not probe the same endpoint or state-changing flow.
   - Do not give subagents broad permission to inspect source code, alter non-app resources, exfiltrate real secrets, probe third parties, or start remediation.
   - Merge subagent reports as leads first; only confirmed, externally reproducible issues become findings.

6. Probe black-box:
   - Inspect security headers, cookies, redirects, CORS behavior, cache behavior, and error responses.
   - Exercise authenticated and unauthenticated flows, including destructive flows, inside local disposable test data.
   - Verify access-control boundaries by switching roles/tenants and changing identifiers only inside local test data.
   - Run approved local scanner, fuzz, replay, lockout, race, export, and stress checks within the request/resource budget.
   - Record reproducible evidence: request path, method, role, relevant headers, status, response shape, screenshot path, and log excerpt.

7. Validate from the outside:
   - Reproduce each suspected issue with the minimum safe request sequence.
   - Compare expected and actual behavior using only approved local roles, accounts, tenants, and test data.
   - Classify scanner output and suspicious behavior as leads until confirmed by external evidence.
   - Do not report speculative issues as confirmed findings.
   - Run or document cleanup/reset after destructive checks.

8. Report clearly:
   - Findings first, ordered by severity.
   - Include severity, affected asset, evidence, impact, likely root cause if inferable from behavior, remediation recommendation, validation, and residual risk.
   - Separate confirmed findings from hypotheses, blocked checks, and clean passes.
   - If no genuine issue is found, say so and list meaningful residual risk or untested scope.

## Assessment Lenses

Read `references/checklist.md` before a broad assessment or when choosing test lenses. It covers authentication, authorization, session management, CSRF/origin, injection, XSS, SSRF/open redirect, file handling, headers/CSP/CORS, multi-tenant isolation, business logic, secrets, observability, dependencies, and operational controls.

Read `references/subagent-lenses.md` when splitting a broad assessment across attack-case specialists.

Use `references/report-template.md` when producing a formal report or durable repo artifact.

## Tooling Guidance

- Prefer browser automation, `curl`, approved test accounts, and local-only HTTP probing.
- Use scanners, fuzzers, replay scripts, and stress tools only against the confirmed local disposable target with explicit request/resource budgets.
- Keep scanner output as evidence, not as final findings. Manually verify impact and root cause before reporting.
- Avoid GitHub PR, branch, commit, push, deployment, and code-edit workflows during assessment mode.

## Repository Adaptation

When working in `welbase_v2`, this skill applies only to a local running app backed by disposable local services or explicitly resettable seed data. Create a sibling assessment worktree first, copy `.env.local` only when needed, use a non-default local port if another checkout is active, and run the black-box/destructive assessment from that worktree. If the user later asks for remediation, start a separate implementation task and then follow the repo's normal branch, validation, commit, push, and PR conventions. After the assessment or remediation is complete, report the worktree path and whether it should be removed.
