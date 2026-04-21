# Review Lenses

Use this file to decide which specialized sub-agents to launch and what each one should focus on.

## Shared Contract

Every review agent should:

- Start with `summary.md`.
- Inspect the relevant `patches/*.patch` files first, then open source files only when needed.
- Read every file in its assigned scope. Do not leave unread files inside the assigned scope.
- Report reviewed files as exact repository paths, not broad area labels.
- Report only actionable findings.
- Ignore formatting-only or purely stylistic nits.
- Use severities `high`, `medium`, or `low`.
- Include `path:line` for every finding.
- Explain the concrete risk or regression.
- If a file cannot be meaningfully inspected, call that out explicitly instead of pretending it was covered.

Each agent reply should fit this shape:

Reviewed files:
- `path/to/file.ts`

Findings:
- `[high][security] path/to/file.ts:42 Issue summary. Why it matters.`
- `none`

## Security

Focus on:

- Missing authentication or authorization checks.
- Secret leakage, token misuse, unsafe logging, and accidental exposure of private data.
- Injection risks such as SQL, shell, template, or prompt injection.
- Unsafe file handling, network access, SSRF, open redirects, CORS mistakes, or overly broad config changes.
- Supabase policy, storage, or route handler changes that weaken access control.
- Supabase RLS gaps, policy omissions, accidental bypasses through `service_role`, and tenant or facility scoping leaks.

Prioritize files like:

- `app/api/**`
- `lib/**`
- `supabase/**`
- `next.config.*`
- middleware, auth, config, webhook, upload, and route files

## Correctness

Focus on:

- Broken business logic, edge cases, and data-shape mismatches.
- Missing null or empty handling.
- Race conditions, retries, duplicate submission, idempotency, or rollback gaps.
- Inconsistent client-server contracts.
- Timezone, locale, numeric, and serialization bugs.

Prioritize files like:

- Route handlers and services.
- Schema and validation modules.
- Form state, submit flows, and async actions.

## Maintainability

Focus on:

- Large duplicated logic that should be shared.
- Layering violations between UI, service, and data-access code.
- Overly coupled components or helpers that hide risky behavior.
- Poorly named abstractions that make future edits error-prone.
- Architectural drift where source changes require doc updates but none were made.

Prioritize files like:

- Large new components.
- New helper modules with repeated patterns.
- Cross-cutting config and documentation changes.

## Performance And Operations

Focus on:

- Expensive repeated work in render or request paths.
- Unbounded network calls, missing timeouts, or excessive retries.
- Large client bundles or unnecessary client-side state churn.
- Missing monitoring or error capture on routes and server-side execution paths.
- Missing Sentry coverage with `@sentry/nextjs`, including missing `captureException`, weak tracing, or uninstrumented Route Handlers, Server Components, Server Actions, and Edge Middleware.
- Overused fallback paths such as silent defaulting, placeholder data, broad catch-all degradation, or multi-step fallback chains that hide failures instead of surfacing and fixing them.
- Log spam, weak failure telemetry, or poor operational fallback behavior.

Prioritize files like:

- `app/**`
- `components/**`
- `lib/**/*client*`
- Route handlers, fetch wrappers, and recorder or upload logic.

## Frontend UX

Focus on:

- Broken user flows, confusing interaction order, or missing success feedback.
- Missing loading, empty, validation-error, or failure states.
- Responsive regressions, viewport overflow, cramped layouts, and mobile-unfriendly interactions.
- Touch-target size, keyboard usability, focus movement, and form readability on small screens.
- Accessibility regressions such as broken keyboard navigation, lost focus, weak labels, missing ARIA semantics, and poor contrast or status messaging when the diff makes them materially worse.
- Fallback-heavy UI that hides real failures with misleading placeholder content, default values, or apparently successful states.
- State-sync bugs where UI, server responses, and optimistic state diverge.

Prioritize files like:

- `app/**` except `app/api/**`
- `components/**`
- `styles/**`
- Pages, forms, drawers, modals, tabs, wizards, and client-side stateful UI

## API Contract

Focus on:

- Request and response shape drift between route handlers, schemas, and clients.
- Required versus optional field drift, nullability drift, and enum drift.
- Status-code and error-payload inconsistencies.
- Validation logic that no longer matches what clients send or consume.
- Contract ambiguity introduced by permissive fallback parsing or default coercion that hides upstream or downstream breakage.
- Missing integration tests or API documentation updates when the contract changed.

Prioritize files like:

- `app/api/**`
- `lib/**/*schema*`
- `lib/**/*validation*`
- `lib/**/*validator*`
- `lib/**/*client*`
- `types/**`
- API integration tests and `docs/architecture/api-tree.md`

## Tests

Focus on:

- Changed production code without corresponding tests.
- Missing success, failure, boundary, or invalid-input coverage.
- Weak assertions that would miss the intended regression.
- Repository-specific test requirements, such as Given/When/Then comments.
- Missing architecture-doc updates when behavior or API shape changed.

Prioritize files like:

- `tests/**`
- Source files listed in `lens-hints.json` under `tests.source_files_without_matching_changed_tests`

## Merge Rules

When multiple agents report the same issue:

- Keep the highest-severity version.
- Prefer the version with the clearest concrete risk.
- Drop duplicates that add no new information.
