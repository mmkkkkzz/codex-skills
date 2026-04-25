# Review Lenses

Use this file to decide which specialized sub-agents to launch and what each one should focus on.

## Shared Contract

Every review agent should:

- Start with `summary.md`.
- In manual fallback mode, follow the `SKILL.md` manual fallback template instead of bundle-artifact requirements: use the synthetic changed-file list and saved patch, do not require `summary.md` or `lens-hints.json`, and do not claim `lens-hints.json` usage.
- Inspect the relevant `patches/*.patch` files first, then open source files only when needed.
- Read every file in its assigned scope. Do not leave unread files inside the assigned scope.
- Report reviewed files as exact repository paths, not broad area labels.
- Report every concrete finding in the assigned scope, including low severity findings.
- Ignore only formatting-only or purely stylistic nits, non-actionable preferences, and speculative concerns that cannot be tied to changed code.
- Use severities `high`, `medium`, or `low`.
- Include `path:line` for every finding.
- Explain the concrete risk or regression.
- If a file cannot be meaningfully inspected, call that out explicitly instead of pretending it was covered.
- Before returning `Findings: none`, perform a false-negative pass for the bug classes named by the assigned lens and mention any unread or unverifiable scope under `Residual risk`.

Finding admissibility:

- A finding must have a changed-code anchor.
- It must name the violated invariant, contract, or expected behavior.
- It must describe a concrete failure mode, not only a preference.
- It should include a plausible fix direction, even when the final report stays concise.

Severity rubric:

- `high`: likely data loss, auth/tenant isolation break, secret exposure, destructive migration failure, broadly blocking runtime regression, or contract break that can make a critical user workflow fail.
- `medium`: likely user-visible correctness regression, API/nullability drift, missing failure handling, meaningful test gap for changed critical behavior, performance/operations issue that can hide or amplify production failure.
- `low`: concrete maintainability, test precision, documentation, accessibility, or minor UX issue tied to changed code, with limited immediate blast radius.

Each agent reply should fit this shape:

Reviewed files:
- `path/to/file.ts`

Findings:
- `[high][access-control] path/to/file.ts:42 Issue summary. Why it matters.`
- `none`

Residual risk:
- Only include unread or unverifiable scope. Omit when there is none.

## Access Control

Focus on:

- Missing authentication or authorization checks.
- Role, tenant, organization, project, account, facility, user, or object-scope drift.
- Self-service carve-outs, owner-only paths, admin-only paths, and break-glass paths that changed semantics.
- CSRF, origin, redirect, cookie, session, CORS, and same-site trust-boundary mistakes.
- User-scoped client versus admin/service client boundary mistakes.
- Policy, middleware, guard, route-handler, or RLS changes that weaken access control.
- Cross-endpoint policy drift: a new or hardened guard applied to only some same-kind mutation or read endpoints.

False-negative pass:

- Re-check every changed auth, policy, RLS, route-handler, middleware, session, cookie, and service-role path.
- Confirm scope is enforced at request validation, authorization, query, and write boundaries when applicable.
- Compare old and new permission predicates, including self-service exceptions and fallback branches.
- Confirm trust-boundary guards are applied consistently across equivalent endpoints or workflows.

Prioritize files like:

- `app/api/**`
- `lib/**`
- `supabase/**`
- middleware, auth, roles, policy, route, session, cookie, redirect, and client-boundary files

## Security

Focus on:

- Secret leakage, token misuse, unsafe logging, and accidental exposure of private data.
- Injection risks such as SQL, shell, template, prompt, HTML, expression, or deserialization injection.
- Unsafe file handling, uploads, path traversal, archive extraction, and executable content handling.
- Unsafe network access, SSRF, webhook trust, CORS mistakes, overly broad config changes, and external callback validation.
- Cryptographic misuse, password handling, token lifetime, signing, verification, and key management.
- Redaction and sanitization gaps that expose secrets or private data.

False-negative pass:

- Re-check changed secret, credential, webhook, upload, file, network, serialization, and redaction paths.
- Confirm errors, logs, telemetry, and external responses do not expose secrets, tokens, private user data, or internal-only identifiers.
- Confirm user-controlled strings cannot cross into interpreters, prompts, shell, SQL, templates, paths, URLs, or callbacks without validation.

Prioritize files like:

- `app/api/**`
- `lib/**`
- `supabase/**`
- `next.config.*`
- config, webhook, upload, storage, redaction, crypto, prompt, and external network files

## Data Integrity

Focus on:

- Migrations, backfills, table/view/function replacement, table rename/drop, archive-before-drop flows, and canonical-table migrations.
- Row coverage and value parity, not just count checks.
- Same-key conflicts, `on conflict` behavior, duplicate inputs, timestamp ties, last-write-wins, and merge precedence.
- Idempotency, rerun safety, transactional boundaries, locking, concurrent writes during migration, and rollback/partial-apply behavior.
- Data shape or invariant preservation across schema changes, generated types, seed data, repositories, and import/export jobs.
- Silent data loss through permissive parsing, default coercion, fallback to empty collections, or skipped divergent target rows.

False-negative pass:

- For every moved or dropped dataset, verify source rows are archived or represented and target values match the intended source values.
- Re-check duplicate, same-key, equal-timestamp, null, invalid-enum, and rerun scenarios.
- Confirm destructive operations happen after verification, and failed verification aborts before data is dropped or hidden.
- Confirm tests are behavioral enough to catch ordering, coverage, and value-parity regressions.

Prioritize files like:

- `supabase/migrations/**`
- database schema, seed, repository, import/export, migration, backfill, archive, transaction, and generated type files

## Correctness

Focus on:

- Broken business logic, edge cases, and data-shape mismatches.
- Missing null or empty handling.
- Race conditions, duplicate submission, state transitions, and rollback gaps outside dedicated migration/data-integrity work.
- Inconsistent client-server contracts.
- Timezone, locale, numeric, and serialization bugs.
- Algorithm, calculation, ordering, filtering, and aggregation regressions.

False-negative pass:

- Re-check null, empty, boundary, duplicate input, timezone, ordering, and state-transition behavior.
- Confirm the changed tests would fail against the previous buggy behavior.
- Confirm any fallback to default values still preserves the intended business meaning.

Prioritize files like:

- Route handlers and services.
- Schema and validation modules.
- Form state, submit flows, and async actions.

## Failure Modes

Focus on:

- Dependency failures, partial failures, degraded state, recovery flows, retry exhaustion, and timeout behavior.
- Fail-open versus fail-closed decisions for authentication, authorization, billing, audit, policy, configuration, and data loading.
- Broad catch blocks, silent defaults, fallback chains, placeholder data, and empty-state coercion that hide real failures.
- Multi-step mutations where a later failure leaves earlier changes committed without rollback or explicit compensation.
- UI or client state divergence after failed fetches, optimistic updates, retries, cancellation, or stale data.
- Audit, telemetry, notification, or downstream side effects that are required for correctness but are swallowed as non-blocking.

False-negative pass:

- Re-check every changed `catch`, fallback, retry, timeout, cancellation, empty/default coercion, and broad degraded-mode branch.
- Confirm critical gates fail closed when their prerequisite lookup fails.
- Confirm partial mutation failures either roll back, compensate, surface a warning/error, or are explicitly safe to ignore.
- Confirm UI recovery states preserve user context instead of clearing selection or presenting false success.

Prioritize files like:

- Route handlers, server actions, service modules, client wrappers, fetchers, stateful UI, audit/notification code, and recovery helpers

## API Contract

Focus on:

- Request and response shape drift between route handlers, schemas, and clients.
- Required versus optional field drift, nullability drift, and enum drift.
- Status-code and error-payload inconsistencies.
- Validation logic that no longer matches what clients send or consume.
- Contract ambiguity introduced by permissive fallback parsing or default coercion that hides upstream or downstream breakage.
- Missing integration tests or API documentation updates when the contract changed.

False-negative pass:

- Re-check client wrapper, schema, route handler, docs, and tests for the same request/response/nullability contract.
- Confirm status codes and error payloads remain consistent for validation, authz, not-found, and internal failures.
- Confirm compatibility fallbacks do not mask contract breakage or silently reinterpret fields.

Prioritize files like:

- `app/api/**`
- `lib/**/*schema*`
- `lib/**/*validation*`
- `lib/**/*validator*`
- `lib/**/*client*`
- `types/**`
- API integration tests and API docs

## Performance

Focus on:

- Expensive repeated work in render or request paths.
- Unbounded network calls, missing timeouts, or excessive retries.
- Large client bundles or unnecessary client-side state churn.
- N+1 queries, duplicate reads, repeated authorization lookups, unbounded pagination, or avoidable full reloads.
- Cache invalidation, memoization, batching, streaming, and concurrency changes that worsen cost or freshness.
- Polling, background loops, and long-running jobs without bounds.

False-negative pass:

- Re-check render loops, request handlers, data loaders, background jobs, and repeated helper calls.
- Confirm new queries are bounded and indexed enough for expected cardinality.
- Confirm caching or batching does not make correctness stale in critical workflows.

Prioritize files like:

- `app/**`
- `components/**`
- `lib/**/*client*`
- Route handlers, fetch wrappers, and recorder or upload logic.

## Observability Ops

Focus on:

- Missing monitoring or error capture on routes and server-side execution paths.
- Missing or weak Sentry coverage, tracing, structured logs, audit events, metrics, and correlation IDs.
- Log spam, alert noise, happy-path events logged as errors, or high-cardinality/noisy telemetry.
- Error reporting that lacks enough context for production investigation, or includes too much sensitive context.
- Operational runbook, migration notice, feature flag, rollout, or recovery visibility gaps.
- Background jobs, webhooks, queues, scheduled tasks, and external integrations that become hard to debug.

False-negative pass:

- Confirm monitored server paths capture enough context for production failures without leaking sensitive data.
- Confirm log levels reflect severity: happy path is not `error`, expected validation is not alert noise, and critical failures are not silent.
- Confirm audit events that matter for compliance or user trust cannot fail invisibly when they are required.

Prioritize files like:

- Route handlers, server actions, middleware, instrumentation, Sentry/logger/audit modules, webhook handlers, jobs, deployment/config, and operational docs

## Frontend UX

Focus on:

- Broken user flows, confusing interaction order, or missing success feedback.
- Missing loading, empty, validation-error, or failure states.
- Responsive regressions, viewport overflow, cramped layouts, and mobile-unfriendly interactions.
- Touch-target size, keyboard usability, focus movement, and form readability on small screens.
- Accessibility regressions such as broken keyboard navigation, lost focus, weak labels, missing ARIA semantics, and poor contrast or status messaging when the diff makes them materially worse.
- Fallback-heavy UI that hides real failures with misleading placeholder content, default values, or apparently successful states.
- State-sync bugs where UI, server responses, and optimistic state diverge.

False-negative pass:

- Re-check loading, empty, validation-error, failure, optimistic-update, and recovery states.
- Confirm keyboard/focus/touch behavior when the diff changes forms, modals, drawers, tabs, or navigation.
- Confirm responsive layout is plausible for the smallest supported viewport when the diff changes visible UI.

Prioritize files like:

- `app/**` except `app/api/**`
- `components/**`
- `styles/**`
- Pages, forms, drawers, modals, tabs, wizards, and client-side stateful UI

## Tests

Focus on:

- Changed production code without corresponding tests.
- Missing success, failure, boundary, or invalid-input coverage.
- Weak assertions that would miss the intended regression.
- Repository-specific test requirements, such as Given/When/Then comments.
- Missing architecture-doc updates when behavior or API shape changed.
- Weak oracles that assert a successful result but not the query, policy, migration parity, failure branch, or side effect that actually matters.

False-negative pass:

- Re-check that tests fail for the exact changed-code regression, not just for broad implementation details.
- Confirm required edge classes are represented when the repo mandates them: success, failure, boundary, invalid input, and external dependency failure.
- Confirm static migration tests are not only string-greps when the behavior requires ordering, coverage, or value-equality guarantees.
- Confirm access-control tests include denied paths, self-service carve-outs, cross-tenant/object cases, and fail-closed dependency failures when relevant.

Prioritize files like:

- `tests/**`
- Source files listed in `lens-hints.json` under `tests.source_files_without_matching_changed_tests`

## Maintainability

Focus on:

- Large duplicated logic that should be shared.
- Layering violations between UI, service, and data-access code.
- Overly coupled components or helpers that hide risky behavior.
- Poorly named abstractions that make future edits error-prone.
- Architectural drift where source changes require docs, ADRs, ExecPlans, or ownership updates but none were made.
- New abstractions that mix policy, I/O, formatting, and orchestration in a way that makes review or testing harder.

False-negative pass:

- Re-check whether new shared logic has one clear owner instead of duplicated cross-layer copies.
- Confirm docs, ExecPlans, or architecture references changed when public behavior, schema, or API contracts changed.
- Confirm added abstraction reduces real complexity and does not hide side effects or policy decisions.

Prioritize files like:

- Large new components.
- New helper modules with repeated patterns.
- Cross-cutting config and documentation changes.

## Merge Rules

When multiple agents report the same issue:

- Keep the highest-severity version.
- Prefer the version with the clearest concrete risk.
- Drop duplicates that add no new information.
- Do not drop distinct findings because they are low severity, numerous, or less urgent.
