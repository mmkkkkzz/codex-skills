---
name: gh-pr-review
description: Review the diff of the current open GitHub pull request or a specified PR and return code review findings, not a summary. Use when Codex needs to review a GitHub PR with `gh`, especially when the work should be split across specialized sub-agents for lenses such as security, correctness, maintainability, performance and operations, frontend UX, API contracts, and test coverage.
---

# Gh Pr Review

## Overview

Review GitHub pull requests as a findings-first code review. Resolve the active PR with `gh`, build a local review bundle, run lens-specific sub-agents in parallel, then merge only actionable findings into a severity-ordered report.

## Inputs

- `repo`: repository path. Default `.`.
- `pr`: PR number or URL. Omit to use the PR for the current branch.
- `gh` authentication with repository access.

## Quick Start

1. Verify GitHub CLI access.
   - `gh auth status`
2. Build the review bundle.
   - `python "<skill-path>/scripts/prepare_pr_review.py" --repo "."`
   - Add `--pr "<number-or-url>"` when the review target is not the current branch PR.
3. Read `<bundle-dir>/summary.md`.
4. Read [`references/review-lenses.md`](references/review-lenses.md).
5. Launch only the recommended lenses from `lens-hints.json`, then merge their findings.

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

Do not launch every available lens by default. When the PR is small and clearly cross-cutting, you can still run all lenses. Otherwise, start with `recommended_lenses`, narrow each sub-agent to the most relevant file subset, and let it open extra source files only when needed for cross-file reasoning.

Use `coverage_gaps` from `lens-hints.json` as a hard stop before finalizing. If any changed file is not covered by the recommended lenses, either assign it to another lens or read it directly as the coordinator. Do not finalize while unread changed files remain.

If the target repository has known high-risk conventions, state them explicitly in the sub-agent prompt. For example, call out Supabase RLS and policy regressions for the `security` lens, and call out Sentry coverage with `@sentry/nextjs` for the `performance-and-operations` lens.

### 3. Spawn specialized sub-agents in parallel

Available lenses:

- `security`
- `correctness`
- `maintainability`
- `performance-and-operations`
- `tests`
- `frontend-ux`
- `api-contract`

Use `spawn_agent` with `agent_type: "explorer"` unless you have a concrete reason to use another type. Pass the minimum context needed: the bundle directory, the review lens, and the output contract. Start with `recommended_lenses` and add more only if the diff or the user request calls for exhaustive review.

Use prompts shaped like this:

`Review the PR bundle at <bundle-dir> from the <lens> lens. Start with summary.md, then inspect the relevant patch files and source files until no unread files remain in your assigned scope. Return a Reviewed files section and a Findings section. Report only actionable findings. Ignore style-only nits. If there are no issues, write "Findings: none".`

Good delegation rules:

- Keep each agent focused on one lens.
- Prefer file subsets from `lens-hints.json` for large PRs.
- Ask the agent to inspect source files in the repository when the patch alone is insufficient.
- Do not ask sub-agents to propose code changes unless the user asks for fixes.
- Use the union of all agents' `Reviewed files` lists to verify full diff coverage before writing the final report.
- For `security`, explicitly ask for Supabase RLS, policy, `service_role`, and tenant-scope regressions when the PR touches `supabase/**`, `app/api/**`, or data-access code.
- For `performance-and-operations`, explicitly ask for Sentry coverage gaps on Route Handlers, Server Components, Server Actions, and Edge Middleware when the PR touches monitored server paths.
- For `performance-and-operations`, also ask whether fallback paths are minimized, or whether the change hides failures behind silent defaults, placeholders, or broad degraded-mode branches.
- For `frontend-ux`, explicitly ask for responsive regressions, viewport overflow, touch usability, mobile-friendly behavior, basic accessibility regressions such as keyboard, focus, labels, ARIA, contrast, and status messaging, and whether the UI masks failures with misleading fallback states when the PR touches pages, forms, drawers, modals, or styles.
- For `api-contract`, explicitly ask for request and response shape drift, nullability drift, status-code and error-shape drift, permissive fallback parsing or coercion that hides contract breakage, and docs or integration-test update gaps when the PR touches API routes, schemas, or client wrappers.

### 4. Merge findings into a single review

Combine all non-empty sub-agent results into one review. Deduplicate overlapping findings. Keep the highest-severity version when multiple agents report the same issue.

Before finalizing, compare the union of sub-agent `Reviewed files` against `files.json`. If any changed file is still missing, read it yourself or launch an extra targeted pass. The final review must not leave unread changed files unless the file is opaque, binary, or otherwise not meaningfully inspectable. In that case, call it out explicitly under `Residual risk`.

Final review requirements:

- Findings first, ordered by severity.
- Each finding must include `severity`, `path:line`, the concrete issue, and why it matters.
- Keep summary text brief and secondary.
- If every agent returns `no findings`, say that explicitly and mention any residual risk such as large untouched areas or inability to run tests.

### 5. Output contract

Use this response shape for the final merged review:

Findings:
- `[high][security] path/to/file.ts:42 Missing authorization check allows ...`
- `[medium][frontend-ux] components/foo.tsx:18 ...`
- `none`

Coverage:
- `Reviewed lenses: security, correctness, frontend-ux`
- `Reviewed files: 12/12`
- `Unread areas: none`

After `Coverage`, optionally add:

- `Open questions`: only when something important is ambiguous.
- `Residual risk`: only when the review could not cover an important area, such as opaque or binary files.

## Manual Fallback

If the script cannot run, use this fallback:

1. `gh pr view --json number,title,url,baseRefName,headRefName,files`
2. `gh pr diff --patch > /tmp/<name>.patch`
3. Build a minimal summary from the returned file list.
4. Continue with the same lens-based delegation and output contract.

## Bundled Resources

### scripts/prepare_pr_review.py

Build a deterministic PR review bundle from `gh`. Use this first.

Examples:

- `python "<skill-path>/scripts/prepare_pr_review.py" --repo "."`
- `python "<skill-path>/scripts/prepare_pr_review.py" --repo "." --pr "164"`
- `python "<skill-path>/scripts/prepare_pr_review.py" --repo "." --pr "https://github.com/org/repo/pull/164" --out-dir "/tmp/pr-164-review"`

### references/review-lenses.md

Defines the default review lenses, common bug classes, and the expected sub-agent output contract. Read it before spawning sub-agents or when you want to trim the default lens set.
