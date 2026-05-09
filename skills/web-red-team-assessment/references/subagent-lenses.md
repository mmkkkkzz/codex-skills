# Attack-Lens Subagents

Use this reference only after the scope gate is satisfied enough for safe probing. The main agent remains the coordinator for scope, safety stops, target mapping, evidence naming, deduplication, and final severity decisions.

All subagents must stay black-box, low-volume, report-only, and inside approved accounts, roles, tenants, facilities, data, and URLs. Do not ask subagents to inspect source code, change configuration, create commits, open PRs, run high-rate scanners, perform destructive writes, exfiltrate secrets, harvest credentials, phish, persist, or probe third parties.

Spawning a specialized attack-case subagent does not expand scope, permission, rate limits, or allowed techniques. Every subagent inherits the same safety boundary unless the user explicitly grants a narrower or different permission.

## When to Delegate

- Use subagents only when the runtime supports delegation and the user explicitly asks for subagents, parallel assessment, or broad multi-lens coverage.
- Do not delegate before authorization, target URLs, environment, accounts/roles, prohibited actions, and rate limits are clear.
- For production or shared environments, delegate a safety coordinator first and keep all other probes read-only until explicit permission exists.
- Assign each subagent a request budget plus a unique route, role, tenant/facility, or surface boundary to avoid duplicate probing.
- If subagents are unavailable, run the same lenses sequentially in the main thread.

## Lens Roster

| Lens | When to run | Focus | Output |
| --- | --- | --- | --- |
| Surface mapper | First, after basic scope | Public/authenticated routes, APIs, forms, downloads, redirects, visible state-changing actions | Route/API inventory with method/path, auth requirement, role, tenant/facility context, side-effect risk, follow-up lenses |
| Browser controls | Parallel after target map starts | Headers, cookies, CORS, CSP, cache, redirects, framing, MIME sniffing, browser storage | Control matrix with observed values, affected paths, expectation, status, redacted evidence |
| Auth and session | Parallel after approved accounts exist | Login, logout, session refresh, reset/invite/OAuth behavior within safe limits | Flow table with actor, request sequence, expected/actual result, session state, confirmed issues, blocked checks |
| Authorization and tenant isolation | After roles, tenants/facilities, object IDs, and test data are known | Server-side access control across list/detail/create/update/delete/export/download paths | Access matrix with actor, object owner, path, expected deny/allow, actual result, impact, minimal reproduction |
| State-changing and CSRF | Only after write scope is explicit | Trusted origin, CSRF, idempotency, replay, content-type/body/schema validation | Action matrix with side-effect class, permission basis, sequence, expected/actual behavior, auditability, cleanup note |
| Input handling and XSS | After input surfaces are mapped | Validation boundaries and rendering using harmless marker payloads | Input matrix by field/type/sink, payload class at a high level, observed handling, gaps, regression-test ideas |
| SSRF and redirects | Only where URL/callback/fetch surfaces exist | Redirect params, callbacks, webhooks, URL previews, server-side fetch features | Surface list with allowed schemes/hosts, expected restriction, observed result, blocked unsafe checks |
| Files, reports, and storage | After artifact flows are mapped | Upload validation, download authorization, signed URL lifetime, report/export isolation | Artifact-flow inventory with source action, generated object, access path, auth result, cache/metadata, leakage or clean pass |
| Client exposure | Parallel, passive only | Externally visible bundles, source maps, public config, debug artifacts, robots/sitemap, static assets | Exposure inventory with URL, observed data type, sensitivity, evidence, finding/informational status |
| Business logic | After domain workflows are understood | Approval bypass, duplicate submission, quota/trial/billing/invite/role transition rules | Workflow-rule table with invariant, actors/states, result, impact, finding or blocked reason, regression scenario |
| Low-impact automation | Last, only with explicit scanner permission | Passive/baseline tooling for leads | Tool lead list with command/config summary, rate profile, raw lead reference, manual verification status, false positives |
| Production safety coordinator | First for production/shared targets | Gate writes, notifications, billing, lockouts, exports, and user-impacting checks | Safety decision log with proposed check, risk, required permission, approved/blocked status, safer alternative |

## Subagent Prompt Contract

Give each subagent only the scope it needs:

```text
You are an attack-lens specialist for an authorized black-box, report-only web assessment.

Scope:
- Target URLs:
- Environment:
- Approved accounts/roles/tenants/facilities:
- Allowed actions:
- Prohibited actions:
- Rate limits:
- Request budget:
- Evidence location/naming:

Lens:
- Name:
- Surfaces to inspect:
- Checks to skip unless explicitly approved:

Rules:
- Stay black-box and externally observable.
- Use low-volume probing only.
- Do not modify code, configuration, infrastructure, branches, commits, PRs, or deployments.
- Do not perform destructive writes, high-rate scanning, credential theft, secret exfiltration, phishing, persistence, or third-party probing.
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
- State-changing actions avoided:
- Residual risk:
```

## Merge Rules

- Treat every subagent result as a lead until the coordinator confirms the behavior externally within scope.
- Deduplicate by affected asset, actor boundary, and root behavior, not by endpoint count.
- If two subagents disagree, keep the item under hypotheses until the coordinator reproduces it.
- Promote only confirmed, externally reproducible issues to findings.
- Keep clean passes meaningful: include only checks that were actually exercised.
- Record blocked checks separately with the missing permission, missing account, or safety reason.
- Include residual risk for untested roles, tenants, actions, production limits, unavailable accounts, and scanner restrictions.
