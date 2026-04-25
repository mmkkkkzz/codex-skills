---
name: gh-pr-review
description: Review the diff of the current open GitHub pull request or a specified PR and return code review findings, not a summary. Use when Codex needs to review a GitHub PR with `gh`, especially when the work should combine Claude Code's /pr-review-toolkit:review-pr output with specialized Codex sub-agents for lenses such as access control, security, data integrity, correctness, failure modes, API contracts, performance, observability and operations, frontend UX, tests, and maintainability.
---

# Gh Pr Review

## Overview

Review GitHub pull requests as a findings-first code review. Resolve the active PR with `gh`, build a local review bundle, run Claude Code's `/pr-review-toolkit:review-pr`, run lens-specific Codex sub-agents in parallel on `gpt-5.4-mini` with `xhigh` reasoning, then merge every concrete high, medium, and low severity finding into a severity-ordered report.

## Inputs

- `repo`: repository path. Default `.`.
- `pr`: PR number or URL. Omit to use the PR for the current branch.
- `gh` authentication with repository access.

## Review Modes

- **Bundle mode**: Default. `prepare_pr_review.py` succeeds and provides `metadata.json`, `files.json`, `lens-hints.json`, `summary.md`, and patch files.
- **Manual fallback mode**: Use only when bundle generation fails. Build equivalent coverage and lens decisions from `gh pr view --json ...`, a saved patch, repository instructions, and direct file reads. Do not claim `lens-hints.json` was used in this mode.

Both modes must produce the same final output contract and exact changed-file coverage accounting.

## Quick Start

1. Verify GitHub CLI access.
   - `gh auth status`
2. Read repository instruction files before reviewing.
   - Start with repo-root or nearest `AGENTS.md`, `CLAUDE.md`, and contribution docs.
   - Treat repo-specific review requirements as hard constraints, not optional context.
3. Build the review bundle.
   - `python3 "<skill-path>/scripts/prepare_pr_review.py" --repo "."`
   - Add `--pr "<number-or-url>"` when the review target is not the current branch PR.
4. Read `<bundle-dir>/summary.md`.
5. Read [`references/review-lenses.md`](references/review-lenses.md).
6. Run Claude Code's PR Review Toolkit pass and save the raw output in the bundle.
7. Launch only the recommended Codex lenses from `lens-hints.json`, then merge all concrete findings from Claude and every lens.

## Workflow

### 1. Resolve and materialize the PR

Always start by generating a review bundle with `prepare_pr_review.py`. The script writes:

- `metadata.json`: PR metadata and counts.
- `files.json`: changed-file list with additions, deletions, and extracted patch paths when available.
- `lens-hints.json`: recommended lenses, selection notes, and per-lens file hints.
- `summary.md`: compact human-readable overview.
- `diff.patch`: full PR patch from `gh pr diff --patch`.
- `patches/<path>.patch`: file-scoped patch files extracted from the full patch.

Prefer the script over repeated ad hoc `gh` commands so every sub-agent can point to the same local artifacts.

### 2. Read the bundle before delegating

Read `summary.md` first. Then read `lens-hints.json` and use `recommended_lenses` as the default sub-agent launch set. Each lens entry also includes `reason` and `focus_files`.

Before delegating, read the repository instruction files that govern the target repo, such as `AGENTS.md`, `CLAUDE.md`, and repo contribution docs. Convert any review-specific repo rules into explicit checks or lens prompt addenda. Examples include required review language, required architecture-doc updates, testing conventions, and known high-risk stacks such as Supabase or Sentry.

Build a short coordinator review plan before launching sub-agents. Keep it as scratch unless the user asks for it. The plan must include:

- Exact changed-file count and paths from `files.json`.
- Repository review rules that affect this PR, such as output language, required tests, migration rules, and doc-update rules.
- Claude PR Review Toolkit configuration, output path, and whether it completed or fell back.
- Recommended lenses from `lens-hints.json`, plus any lens added or removed by the coordinator and the reason.
- Exact assigned file scope for each lens.
- Coordinator direct-read targets, especially access-control gates, route handlers, migrations, destructive operations, failure-mode branches, external requests, generated-contract boundaries, and tests that should prove the changed behavior.
- Coverage gaps that must be closed before final output.

Do not launch every available lens by default. When the PR is small and clearly cross-cutting, you can still run all lenses. Otherwise, start with `recommended_lenses`, narrow each sub-agent to the most relevant file subset, and let it open extra source files only when needed for cross-file reasoning.

Use `coverage_gaps` from `lens-hints.json` as a hard stop before finalizing. If any changed file is not covered by the recommended lenses, either assign it to another lens or read it directly as the coordinator. Do not finalize while unread changed files remain.

For large or high-risk PRs, do not rely on sub-agent `Findings: none` outputs alone. If the PR changes more than roughly 20 files, or touches access control, route handlers, external network calls, migrations, destructive data changes, failure-mode branches, observability, or tenant-scope logic, the coordinator must run a direct hotspot sanity pass before finalizing. At minimum, open the changed helpers or handlers that gate access, the changed files that move/drop data or make external requests, and the changed tests that should prove the new behavior.

For high-risk migration or API compatibility PRs, the coordinator must directly inspect the changed migration/backfill/drop files and compatibility route/client/schema files even when `lens-hints.json` reports no coverage gaps. For destructive migrations, verify both key coverage and value equality before drop/rename, and treat skipped divergent target rows as reportable data-loss risk. For compatibility APIs, compare old and new permission predicates including self-service carve-outs, and verify response fields preserve semantic sources such as planned versus actual values.

For small PRs, the coordinator's direct read of all changed files is sufficient to count as the sanity pass. You do not need a second separate hotspot sweep when the entire diff is already small enough to read directly.

If the target repository has known high-risk conventions, state them explicitly in the sub-agent prompt. For example, call out Supabase RLS and policy regressions for the `access-control` lens, destructive migration parity for the `data-integrity` lens, and Sentry coverage with `@sentry/nextjs` for the `observability-ops` lens.

### Manual fallback planning

When `prepare_pr_review.py` cannot produce a bundle, create a synthetic review plan before delegating or reviewing manually:

- Treat `gh pr view --json ... files` as the synthetic `files.json` equivalent for exact changed-file coverage.
- Treat an existing saved patch path, such as `/tmp/pr-88.patch`, as the synthetic `diff.patch` equivalent. Use it to identify changed hunks and line anchors.
- Do not rerun `gh pr diff --patch` when a saved patch already exists. If no saved patch exists, try `gh pr diff --patch > /tmp/<name>.patch`; if that also fails, continue with `gh pr view` metadata plus targeted source reads and list the missing patch as residual risk.
- Read repository instruction files exactly as in bundle mode.
- Select lenses from changed paths and risk triggers:
  - `access-control`: authentication, authorization, roles, RLS/policies, middleware, route handlers, session/cookie/origin/redirect trust boundaries, tenant or object scope, and service-role boundaries.
  - `security`: secrets, injection, unsafe file/network handling, uploads, webhooks, CORS, crypto/password/token handling, sanitization, and redaction.
  - `data-integrity`: migrations, backfills, canonical data movement, schema changes, destructive drop/rename, repositories, transactions, duplicate/idempotency behavior, and value parity.
  - `failure-modes`: dependency failure, partial failure, degraded state, fallback, retry, timeout, broad catch/default branches, fail-open/fail-closed behavior, and required side-effect failures.
  - `api-contract`: API routes, client wrappers, schemas, validators, generated/public types, status codes, error payloads, docs for API behavior.
  - `performance`: runtime cost, N+1, repeated work, unbounded loops, caching, batching, bundle size, and request/render path regressions.
  - `observability-ops`: Sentry, structured logs, audit events, metrics, tracing, alert noise, operational investigation context, jobs, webhooks, and rollout visibility.
  - `tests`: changed production behavior without matching tests, weak regression assertions, migrations, or repo-specific coverage requirements.
  - `frontend-ux`: visible UI, forms, modals, navigation, responsive/accessibility behavior, client state.
  - `maintainability`: docs-only changes, cross-cutting helpers, large refactors, layering and ownership.
  - `correctness`: default for changed runtime logic and business behavior not fully covered by the more specific lenses.
- Assign every changed file to at least one selected lens or to coordinator direct read.
- In final `Coverage`, write `Reviewed sources: Claude pr-review-toolkit, <lenses> (manual fallback)` when the Claude pass ran; otherwise write `Reviewed sources: <lenses> (manual fallback)` and list the Claude fallback reason under `Residual risk`. Never mention `lens-hints.json` recommendations in manual fallback mode.

Manual fallback sub-agent prompt template:

```text
Manual fallback is active. Do not read or claim `lens-hints.json`.

## Available Artifacts
- Changed-file list: <exact paths from gh pr view --json ... files>
- Patch source: <saved patch path, or note if patch unavailable>
- Repo rules: <language/testing/docs/migration rules that matter>

## Assigned Scope
- Lens: <lens>
- Files: <exact assigned paths>
- Lens-specific checks: <copy only relevant checks from review-lenses.md>

## Required Method
1. Read the saved patch when available.
2. Open current source files when the patch is insufficient to verify behavior or line numbers.
3. Do not report a finding unless it has a changed-code anchor, violated invariant/contract, concrete failure mode, and plausible fix direction.
4. If no finding remains after false-positive and false-negative passes, write "Findings: none".

## Output
Reviewed files:
- `path/to/file`

Findings:
- `[severity][<lens>] path/to/file.ts:42 Issue summary. Why it matters.`
- `none`

Residual risk:
- Only include unread or unverifiable scope.
```

### Review stability rules

Use these rules to keep outputs stable across runs:

- Treat `files.json` as the source of truth for changed-file coverage. Do not infer coverage from area names, lens names, or broad summaries.
- Keep a coordinator finding ledger while merging: `source lens`, `path:line`, `severity`, `risk chain`, `decision` (`keep`, `duplicate`, `drop`), and `decision reason`.
- Keep a hotspot checklist for every high-risk changed file. Mark each hotspot as `read`, `covered by lens`, `finding`, or `no finding after direct check`.
- A finding is admissible only when it has all four parts: changed-code anchor, violated invariant or contract, concrete failure mode, and a plausible fix direction.
- Run a false-positive pass before final output. Drop items whose risk depends on unchanged code alone, missing context contradicted by source, or a line that no longer exists in the current diff.
- Run a false-negative pass before final output. If a high-risk changed file has no finding, explicitly re-check the relevant bug class: access/scope, data loss, contract drift, error handling, fallback behavior, observability, and test coverage.
- Use the fixed severity rubric below. Do not upgrade severity because a finding is interesting, and do not downgrade concrete low-severity findings because the report is long.

Severity rubric:

- `high`: likely data loss, auth/tenant isolation break, secret exposure, destructive migration failure, broadly blocking runtime regression, or contract break that can make a critical user workflow fail.
- `medium`: likely user-visible correctness regression, API/nullability drift, missing failure handling, meaningful test gap for changed critical behavior, performance/operations issue that can hide or amplify production failure.
- `low`: concrete maintainability, test precision, documentation, accessibility, or minor UX issue tied to changed code, with limited immediate blast radius.

### 3. Run Claude Code PR Review Toolkit

Before or alongside Codex lens sub-agents, run Claude Code's `pr-review-toolkit@claude-plugins-official` command against the same repository state. Treat this as an additional independent review source, not as a replacement for Codex lens coverage or coordinator hotspot checks.

Default command:

```bash
node "<skill-path>/scripts/run_claude_pr_review.mjs" --repo "." --bundle-dir "<bundle-dir>"
```

For a narrower or more exhaustive Claude pass, pass the same aspect words supported by Claude's slash command:

```bash
node "<skill-path>/scripts/run_claude_pr_review.mjs" --repo "." --bundle-dir "<bundle-dir>" --review-aspects "tests errors"
node "<skill-path>/scripts/run_claude_pr_review.mjs" --repo "." --bundle-dir "<bundle-dir>" --review-aspects "all parallel"
```

The helper writes Claude's raw stdout to `<bundle-dir>/claude-pr-review.md`. Read that file before final merge. Preserve Claude's review result as a source artifact: do not rewrite it in place, do not delete low severity findings, and do not treat a Claude "no findings" result as coverage for changed files unless its output names the files or the coordinator can verify that scope.

The final review must also include Claude's raw report without information loss. After the merged Codex review sections, add `Claude PR Review Toolkit Report (verbatim)` and paste the complete contents of `<bundle-dir>/claude-pr-review.md` unchanged. Do not summarize, reorder, deduplicate, translate, omit low-severity items, trim, indent, blockquote, or wrap Claude's raw report in a way that changes its content. If the Claude pass failed and no raw report exists, include `Claude PR Review Toolkit Report (verbatim): unavailable` with the exact failure reason from stderr or the helper output.

The helper defaults to `--permission-mode auto` and allows the read/review tools Claude's command needs: `Bash(git *)`, `Bash(gh *)`, `Glob`, `Grep`, `Read`, and `Task`. Keep it read-only unless the user explicitly asks for fixes.

If Claude Code, the `claude-code` Codex skill wrapper, or `pr-review-toolkit@claude-plugins-official` is unavailable, continue with the Codex lens workflow and list `Claude pr-review-toolkit unavailable: <reason>` under `Residual risk`. Do not block the PR review solely because the Claude pass failed.

When merging Claude output with Codex sub-agent outputs:

- Add every concrete Claude finding to the same coordinator finding ledger used for Codex lens findings.
- Use source label `claude-pr-review-toolkit`.
- Keep the Claude finding text and severity as close to raw as practical, while normalizing final output to this skill's single `path:line` and severity format.
- Merge Claude findings into the top-level `Findings` list as Codex-review findings, but still include the complete raw Claude report later in `Claude PR Review Toolkit Report (verbatim)`.
- Deduplicate only exact or semantically identical issues. If Claude and a Codex lens identify different failure modes on the same line, keep both.
- If Claude reports a finding without enough anchor evidence, re-check the patch/source. Keep it if the coordinator can anchor it; otherwise drop it as `line-not-found` or `speculative` in the internal ledger.
- Include Claude in final coverage as `Reviewed sources: Claude pr-review-toolkit, <lenses>`.

### 4. Spawn specialized sub-agents in parallel

Available lenses:

- `access-control`
- `security`
- `data-integrity`
- `correctness`
- `failure-modes`
- `api-contract`
- `performance`
- `observability-ops`
- `frontend-ux`
- `tests`
- `maintainability`

Use sub-agents only when the user explicitly asked for a PR review, asked for this skill, or otherwise gave clear permission for delegated review work. If delegation is unavailable in the current environment, perform the same lens-based reasoning yourself and mention the fallback only when it materially affected coverage or confidence.

Use `spawn_agent` with these fixed sub-agent settings:

- `agent_type: "explorer"`
- `model: "gpt-5.4-mini"`
- `reasoning_effort: "xhigh"`

Example per lens:

```json
{
  "agent_type": "explorer",
  "model": "gpt-5.4-mini",
  "reasoning_effort": "xhigh",
  "message": "Review the PR bundle at <bundle-dir> from the <lens> lens..."
}
```

Do not omit, downgrade, or vary those model settings between lenses. If the configured model is unavailable in the current environment, state the fallback explicitly in the final review under `Residual risk`. Pass the minimum context needed: the bundle directory, the review lens, and the output contract. Start with `recommended_lenses` and add more only if the diff or the user request calls for exhaustive review.

Use prompts shaped like this:

`Review the PR bundle at <bundle-dir> from the <lens> lens. Start with summary.md, then inspect the relevant patch files and source files until no unread files remain in your assigned scope. Return a Reviewed files section and a Findings section. Report every concrete finding in your scope, including low severity findings. A finding must have a changed-code anchor, violated invariant or contract, concrete failure mode, and plausible fix direction. Use this severity rubric: high=data loss/access-control/tenant/secret/destructive migration/critical workflow break; medium=likely user-visible regression/API drift/failure handling/test gap/production observability risk; low=concrete maintainability/test precision/docs/accessibility/minor UX issue. Ignore only purely stylistic nits, non-actionable preferences, and speculative concerns that cannot be tied to changed code. If there are no issues, write "Findings: none".`

For more stable agent outputs, prefer this expanded prompt template over improvising:

```text
Review the PR bundle at <bundle-dir> from the <lens> lens.

## Assigned Scope
- Files: <exact paths from files.json or lens-hints.json>
- Repo rules: <language/testing/docs/migration rules that matter>
- Lens-specific checks: <copy only relevant checks from review-lenses.md>

## Required Method
1. Read summary.md and lens-hints.json.
2. Read each assigned patch file.
3. Open the current source file whenever the patch alone is insufficient to verify behavior or line numbers.
4. Do not report a finding unless it has a changed-code anchor, violated invariant/contract, concrete failure mode, and plausible fix direction.
5. If no finding remains after a false-positive pass, write "Findings: none".

## Output
Reviewed files:
- `path/to/file`

Findings:
- `[severity][<lens>] path/to/file.ts:42 Issue summary. Why it matters.`
- `none`

Residual risk:
- Only include unread or unverifiable scope.
```

Good delegation rules:

- Keep each agent focused on one lens.
- Prefer file subsets from `lens-hints.json` for large PRs.
- Ask the agent to inspect source files in the repository when the patch alone is insufficient.
- Do not ask sub-agents to propose code changes unless the user asks for fixes.
- Use the union of all agents' `Reviewed files` lists to verify full diff coverage before writing the final report.
- For `access-control`, explicitly ask for Supabase RLS, policy, `service_role`, object-scope regressions, self-service carve-outs, CSRF/origin/session/cookie/redirect boundaries, and cross-endpoint guard consistency when the PR touches `supabase/**`, `app/api/**`, middleware, auth, or data-access code.
- For `security`, explicitly ask for secrets, injection, unsafe file/network handling, webhook trust, upload handling, redaction, crypto/password/token handling, and privacy leakage.
- For `data-integrity`, explicitly ask for row coverage and value parity before destructive operations, same-key conflicts, timestamp ties, `on conflict` precedence, idempotency, rollback, and archive-before-drop verification.
- For `failure-modes`, explicitly ask whether dependency failures fail open or fail closed, whether fallback paths hide real failures behind defaults/placeholders, whether partial mutations roll back or compensate, and whether required side effects can fail invisibly.
- For `performance`, explicitly ask for N+1 queries, duplicate reads, unbounded pagination/loops, render/request repeated work, caching freshness, and bundle or client-state churn.
- For `observability-ops`, explicitly ask for Sentry coverage gaps on Route Handlers, Server Components, Server Actions, and Edge Middleware when the PR touches monitored server paths; also ask for log-level semantics, audit-event reliability, alert noise, and production investigation context.
- For `frontend-ux`, explicitly ask for responsive regressions, viewport overflow, touch usability, mobile-friendly behavior, basic accessibility regressions such as keyboard, focus, labels, ARIA, contrast, and status messaging, and whether the UI masks failures with misleading fallback states when the PR touches pages, forms, drawers, modals, or styles.
- For `api-contract`, explicitly ask for request and response shape drift, nullability drift, status-code and error-shape drift, permissive fallback parsing or coercion that hides contract breakage, and docs or integration-test update gaps when the PR touches API routes, schemas, or client wrappers.

### 5. Merge findings into a single review

Combine Claude's raw PR Review Toolkit output and all non-empty Codex sub-agent results into one review. Deduplicate overlapping findings, but do not suppress distinct findings because they are low severity, numerous, or less urgent. Keep the highest-severity version when multiple sources report the same issue.

The top-level merged `Findings` list is allowed to normalize, deduplicate, and false-positive-check Claude findings. The verbatim Claude section is not: copy the raw Claude report exactly so the user can audit any coordinator decision and recover every detail Claude produced.

Before finalizing, compare the union of sub-agent `Reviewed files` against `files.json`. If any changed file is still missing, read it yourself or launch an extra targeted pass. The final review must not leave unread changed files unless the file is opaque, binary, or otherwise not meaningfully inspectable. In that case, call it out explicitly under `Residual risk`.

During merge, maintain the coordinator finding ledger described in Review stability rules. The ledger is internal scratch unless the user asks for it, but it must drive keep/drop decisions. When dropping a candidate finding, identify whether it was duplicate, speculative, contradicted by source, line-not-found, outside the diff, or style-only.

Treat missing tests or docs as supporting evidence inside the primary behavior or contract finding unless they are independently actionable. Create a separate test/doc finding only when the missing coverage or stale document would remain a concrete problem even after the primary code issue is fixed.

Pressure-test every kept finding before finalizing:

- Can the affected line be found in the current source or patch?
- Is the behavior newly introduced or materially changed by this PR?
- Which invariant, API contract, user workflow, security boundary, or operational expectation is violated?
- What concrete bad outcome follows if the PR ships as-is?
- Would a reasonable maintainer know what to change from the finding?

If the answer to any question is no, rewrite, downgrade, or drop the finding.

Final review requirements:

- Findings first, ordered by severity.
- Include every distinct concrete finding across `high`, `medium`, and `low`; do not apply a top-N cap or only report the most important findings.
- Each finding must include `severity`, `path:line`, the concrete issue, and why it matters.
- Each finding should be explainable as: changed behavior -> violated invariant/contract -> concrete consequence. If that chain cannot be written in one sentence, drop or downgrade it.
- When a sub-agent reports a line range, normalize it to the first relevant line in the final merged review so every final finding still uses a single `path:line`.
- `Findings: none` is allowed only when Claude output, Codex sub-agent outputs, and the coordinator's direct hotspot sanity pass came back clean.
- Treat a finding as reportable when the diff-to-risk chain is concrete enough to explain a user-visible, access-control, security, data-integrity, failure-mode, correctness, contract, test, maintainability, accessibility, or operational consequence. Drop speculative concerns that cannot be tied back to the changed code, but keep low severity findings when they are concrete.
- Keep summary text brief and secondary.
- If every review source returns `no findings`, say that explicitly and mention any residual risk such as large untouched areas or inability to run tests.
- `Coverage` must be derived from the exact changed-file paths in `files.json`, or from the synthetic manual-fallback changed-file list when bundle mode is unavailable, not from broad area summaries. If any file was not read directly or through a lens owner, list that path under `Unread areas`.
- Before sending the final review, run one final consistency pass: every finding has a single valid `path:line`, every severity matches the rubric, every changed file is covered or listed as unread, and the final language follows repository instructions.
- If final `Findings: none`, include `Residual risk:` as a required one-sentence note after `Coverage`. It must say which hotspot classes were checked and whether any area was unread. Do not use a generic approval phrase.

Docs-only no-findings example:

```text
Findings: none

Coverage:
- Reviewed sources: Claude pr-review-toolkit, maintainability
- Reviewed files: 2/2
- Unread areas: none

Residual risk: Docs-only install-command/link correctness and maintainability/doc-consistency hotspots were checked; no runtime source, tests, configs, API routes, UI, generated files, or unread changed files remained.

Claude PR Review Toolkit Report (verbatim)
<paste the complete contents of claude-pr-review.md here unchanged>
```

### 6. Output contract

Use this response shape for the final merged review:

Findings:
- `[high][access-control] path/to/file.ts:42 Missing authorization check allows ...`
- `[medium][frontend-ux] components/foo.tsx:18 ...`
- `none`

Coverage:
- `Reviewed sources: Claude pr-review-toolkit, access-control, correctness, frontend-ux`
- `Reviewed files: 12/12`
- `Unread areas: none`

After `Coverage`, optionally add:

- `Open questions`: only when something important is ambiguous.
- `Residual risk`: required when `Findings: none`; otherwise only when the review could not cover an important area, such as opaque or binary files, or when a model/tool fallback materially lowers confidence.

Then always add this section when the Claude pass ran:

Claude PR Review Toolkit Report (verbatim):
<paste the complete raw `<bundle-dir>/claude-pr-review.md` contents here unchanged>

If the Claude pass failed, add:

Claude PR Review Toolkit Report (verbatim): unavailable
<exact failure reason>

Coverage formatting notes:

- The final merged review does not need to print every reviewed path when the PR is large.
- The coordinator must still reconcile exact paths against `files.json` while reviewing.
- In the final response, `Reviewed files: N/N` plus explicit `Unread areas` paths is sufficient.
- Patch-level reconciliation is acceptable for docs, generated files, lockfiles, and similar low-risk artifacts when the diff is human-readable and does not hide runtime behavior. Read the underlying source file directly when the patch alone is insufficient to judge behavior.

## Manual Fallback

If the script cannot run, use this fallback:

1. `gh pr view --json number,title,url,baseRefName,headRefName,files`
2. Use an existing saved patch if one is available. Otherwise run `gh pr diff --patch > /tmp/<name>.patch`.
3. Build a synthetic review plan from the returned file list, saved patch, repository instructions, and the manual fallback lens-selection rules above.
4. Continue with the same findings-first output contract, marking `Reviewed sources: ... (manual fallback)` in `Coverage`.

## Bundled Resources

### scripts/prepare_pr_review.py

Build a deterministic PR review bundle from `gh`. Use this first.

Examples:

- `python3 "<skill-path>/scripts/prepare_pr_review.py" --repo "."`
- `python3 "<skill-path>/scripts/prepare_pr_review.py" --repo "." --pr "164"`
- `python3 "<skill-path>/scripts/prepare_pr_review.py" --repo "." --pr "https://github.com/org/repo/pull/164" --out-dir "/tmp/pr-164-review"`

### scripts/run_claude_pr_review.mjs

Run Claude Code's `/pr-review-toolkit:review-pr` through the local `$claude-code` wrapper and save raw output into the review bundle.

Examples:

- `node "<skill-path>/scripts/run_claude_pr_review.mjs" --repo "." --bundle-dir "<bundle-dir>"`
- `node "<skill-path>/scripts/run_claude_pr_review.mjs" --repo "." --bundle-dir "<bundle-dir>" --review-aspects "all parallel"`
- `node "<skill-path>/scripts/run_claude_pr_review.mjs" --repo "." --bundle-dir "<bundle-dir>" --review-aspects "tests errors" --instruction "Prioritize behavioral regressions."`

### references/review-lenses.md

Defines the default review lenses, common bug classes, and the expected sub-agent output contract. Read it before spawning sub-agents or when you want to trim the default lens set.
