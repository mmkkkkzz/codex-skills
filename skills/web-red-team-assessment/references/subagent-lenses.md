# Attack-Lens Subagents

Use this reference only after the local-only scope gate is satisfied enough for safe probing. The main agent remains the coordinator for scope, safety stops, target mapping, evidence naming, deduplication, cleanup/reset, and final severity decisions.

All subagents must stay black-box and inside approved local accounts, roles, tenants, facilities, data, and URLs. Local destructive app-level actions are allowed only when the assigned lens includes a request/resource budget and cleanup/reset path. Do not ask subagents to inspect source code, change configuration, create commits, open PRs, exfiltrate real secrets, harvest real credentials, phish, persist, damage the host, or probe third parties.

Spawning a specialized attack-case subagent does not expand target scope beyond the local disposable target. Every subagent inherits the same local-only safety boundary unless the user explicitly grants a narrower permission.

## When to Delegate

- Use subagents only when the runtime supports delegation and the user explicitly asks for subagents, parallel assessment, or broad multi-lens coverage.
- Do not delegate before authorization, local target URLs, disposable backing services, accounts/roles, prohibited non-local actions, request/resource budgets, and cleanup/reset paths are clear.
- If the target is staging, preview, production, shared, or public internet, stop and ask for a local disposable target instead.
- Assign each subagent a request/resource budget plus a unique route, role, tenant/facility, or surface boundary to avoid duplicate probing and uncontrolled local load.
- If subagents are unavailable, run the same lenses sequentially in the main thread.

## Lens Roster

| Lens | When to run | Focus | Output |
| --- | --- | --- | --- |
| Surface mapper | First, after basic scope | Public/authenticated routes, APIs, forms, downloads, redirects, visible state-changing actions | Route/API inventory with method/path, auth requirement, role, tenant/facility context, side-effect risk, follow-up lenses |
| Browser controls | Parallel after target map starts | Headers, cookies, CORS, CSP, cache, redirects, framing, MIME sniffing, browser storage | Control matrix with observed values, affected paths, expectation, status, redacted evidence |
| Auth and session | Parallel after approved accounts exist | Login, logout, session refresh, reset/invite/OAuth behavior within safe limits | Flow table with actor, request sequence, expected/actual result, session state, confirmed issues, blocked checks |
| Authorization and tenant isolation | After roles, tenants/facilities, object IDs, and test data are known | Server-side access control across list/detail/create/update/delete/export/download paths | Access matrix with actor, object owner, path, expected deny/allow, actual result, impact, minimal reproduction |
| Destructive workflow and CSRF | After reset/cleanup path is known | Trusted origin, CSRF, idempotency, replay, content-type/body/schema validation, deletes, bulk updates, lockouts | Action matrix with side-effect class, permission basis, sequence, expected/actual behavior, auditability, cleanup note |
| Input handling, injection, and XSS | After input surfaces are mapped | Validation boundaries, fuzzed values, malformed payloads, rendering, import/export fields | Input matrix by field/type/sink, payload class at a high level, observed handling, gaps, regression-test ideas |
| SSRF and redirects | Only where URL/callback/fetch surfaces exist and local stubs are available | Redirect params, callbacks, webhooks, URL previews, server-side fetch features | Surface list with allowed schemes/hosts, local stub result, expected restriction, observed result, blocked real external checks |
| Files, reports, and storage | After artifact flows are mapped | Upload validation, corrupted/oversized files within host limits, download authorization, signed URL lifetime, report/export isolation | Artifact-flow inventory with source action, generated object, access path, auth result, cache/metadata, leakage or clean pass |
| Client exposure | Parallel, passive only | Externally visible bundles, source maps, public config, debug artifacts, robots/sitemap, static assets | Exposure inventory with URL, observed data type, sensitivity, evidence, finding/informational status |
| Business logic | After domain workflows are understood | Approval bypass, duplicate submission, quota/trial/billing/invite/role transition rules, irreversible-looking operations on disposable data | Workflow-rule table with invariant, actors/states, result, impact, finding or blocked reason, regression scenario |
| Automation, fuzz, and local stress | After explicit local resource budget | Scanner/fuzzer/replay/race/stress tooling for leads and local resilience behavior | Tool lead list with command/config summary, request/resource profile, raw lead reference, manual verification status, false positives |
| Cleanup and reset coordinator | First when destructive lenses are used | Reset commands, generated artifacts, locked accounts, queued jobs, local service state | Cleanup decision log with destructive check, expected residue, reset command, completed/pending status |

## Subagent Prompt Contract

Give each subagent only the scope it needs:

```text
You are an attack-lens specialist for an authorized local-only black-box destructive web assessment.

Scope:
- Target URLs:
- Environment:
- Approved accounts/roles/tenants/facilities:
- Disposable services/data:
- Reset/cleanup command:
- Allowed actions:
- Prohibited actions:
- Request/resource budget:
- Evidence location/naming:

Lens:
- Name:
- Surfaces to inspect:
- Checks to skip unless explicitly approved:

Rules:
- Stay black-box and externally observable.
- Stay within the local disposable target and assigned request/resource budget.
- Do not modify code, configuration, infrastructure, branches, commits, PRs, or deployments.
- Destructive app-level actions are allowed only if listed in Allowed actions and covered by the reset/cleanup command.
- Do not damage the host, developer tools, source repo, package cache, real cloud resources, or shared services.
- Do not perform credential theft against real accounts, real secret exfiltration, phishing, persistence, or third-party probing.
- Redact passwords, cookies, tokens, secrets, and personal data.
- Treat scanner/tool output and suspicious behavior as leads until manually verified.

Report:
- Lens summary:
- Surfaces checked:
- Confirmed findings:
- Leads/hypotheses:
- Clean passes:
- Blocked checks and why:
- Evidence references:
- Safety stops:
- Request count:
- State-changing actions performed:
- Cleanup/reset performed or still needed:
- Residual risk:
```

## Merge Rules

- Treat every subagent result as a lead until the coordinator confirms the behavior externally within scope.
- Deduplicate by affected asset, actor boundary, and root behavior, not by endpoint count.
- If two subagents disagree, keep the item under hypotheses until the coordinator reproduces it.
- Promote only confirmed, externally reproducible issues to findings.
- Keep clean passes meaningful: include only checks that were actually exercised.
- Record blocked checks separately with the missing permission, missing account, or safety reason.
- Include residual risk for untested roles, tenants, destructive actions, unavailable accounts, scanner restrictions, and cleanup/reset that was not verified.
