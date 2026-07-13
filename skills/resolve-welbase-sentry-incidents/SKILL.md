---
name: resolve-welbase-sentry-incidents
description: "Resolve the complete live unresolved Sentry queue for welbase_v2 end to end: inventory every issue, classify and root-fix each cause, add regression coverage and required docs, merge reviewed fix PRs into develop, release develop to main, resolve Sentry issues against the production release, and verify production. Use only when the user explicitly asks to handle every or all unresolved Sentry issues, drain or clear the entire Sentry backlog, or sweep the full unresolved queue through develop and main. Do not use for one named incident, investigation-only requests, or requests that do not authorize a full-queue production release."
---

# Resolve Welbase Sentry Incidents

Drain the live `first-step/welbase` unresolved queue through production. Treat Sentry, GitHub, the repository, CI, Vercel, and production as live sources of truth.

## Required end state

Do not stop at triage, a local patch, PR creation, or a passing CI run. Finish only after all of the following hold:

- Every issue from the initial all-time unresolved snapshot is classified and has a verified root action.
- A fresh pre-release scan has added any newly unresolved issues to the same wave.
- Every code/config/DB fix has focused regression coverage and the applicable repository gate passes.
- Every fix PR is merged into `develop` only after a current-head Codex review completes cleanly.
- A reviewed release PR propagates the final `develop` state to `main` without dropping main-only changes.
- The production deployment and Sentry release for the merged `main` SHA are verified.
- Fixed issues are resolved in the verified release; `archive` is never used as a substitute for remediation.
- A final fresh unresolved scan is empty. If new incidents appear, classify and handle them before declaring completion.
- Temporary worktrees/branches are cleaned safely, the root `develop` checkout is clean/synced, and the completion webhook is sent.

## 1. Establish live scope

1. Work only in `/Users/mkmini/Developer/welbase_v2` or a dedicated worktree for that repository.
2. Read `AGENTS.md` and `.agent/PLANS.md`. Create or update one ExecPlan for every all-unresolved wave; keep its issue ledger, discoveries, decisions, validation, and closeout state resumable without copying sensitive event data.
3. Verify `git`, `gh`, and Sentry authentication. Use the explicit Sentry target; do not rely on auto-detection or Seer-only commands.
4. Inspect repository cleanliness, worktrees, open PRs, and remote branches. Preserve unrelated user changes and take over an already-open equivalent fix instead of duplicating it.
5. Fetch/prune `origin`, branch from current `origin/develop`, and use a dedicated worktree. Never implement the incident wave directly on `main`.

Capture the all-time unresolved inventory with fresh data:

```bash
sentry issue list first-step/welbase \
  --query 'is:unresolved' \
  --period '>=1970-01-01' \
  --limit 1000 \
  --fresh \
  --json \
  --fields id,shortId,title,culprit,count,userCount,firstSeen,lastSeen,level,status,priority,substatus,isUnhandled,permalink
```

If `hasMore` is true, rerun the command with `--cursor next` until `hasMore` is false, and deduplicate the combined pages by issue `id`. Keep raw event payloads in temporary local artifacts only; never commit PHI, tokens, replay data, request bodies, or unsanitized Sentry extras.

For every issue, capture the current event and trace to a mode-0600 temporary artifact without echoing raw JSON into tool/chat output:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/resolve-welbase-sentry-incidents/scripts/capture-sentry-issue.mjs" \
  --issue first-step/welbase#WELBASE-XX \
  --out-dir /tmp/welbase-sentry-evidence
```

The helper prints only a sanitized routing summary and the protected artifact path. Inspect the raw file only with targeted selectors that exclude exception values, messages, breadcrumb data/messages, request bodies/headers/query strings, variables, source context, replay IDs, and span descriptions. Remove the temporary evidence directory at closeout. Maintain a working inventory containing issue ID, latest event/release/environment, affected route or job, user impact, suspected shared cause, disposition, fix evidence, tests, target PR, and final Sentry state.

## 2. Classify without hiding failures

Assign every issue to exactly one root-action class:

- **Product defect:** Fix the canonical shared runtime path, not one observed callsite.
- **Expected handled outcome reported as an error:** Narrow monitoring suppression to the exact typed boundary while preserving unexpected failures, user-visible errors, and operational evidence.
- **Transient dependency or network failure:** Add bounded retry/aggregation/recovery behavior while keeping manual recovery failures and sustained outages observable.
- **Configuration, deployment, or migration drift:** Correct the canonical config/migration/deploy state and add a guardrail or runbook check that detects recurrence.
- **Already fixed:** Prove the deployed release contains the root fix and that `lastSeen`/count did not advance after it; then resolve against that release.
- **Duplicate symptoms of one cause:** Map every issue to the shared fix and verify each issue separately after release.

Do not classify by title alone. Correlate stack, breadcrumbs, route, tags, release, environment, count, first/last seen, and repository history. Do not resolve, ignore, archive, merge groups, or create a tracker ticket merely to make the unresolved queue look empty. Instrumentation by itself is not a root fix.

## 3. Implement root fixes

1. Group issues that share one cause. Prefer one coherent incident-wave PR; split unrelated or high-risk causes into minimal independent `develop` PRs when that makes review and rollback safer.
2. Fix the canonical design and remove obsolete fallback/compatibility paths. Update every caller, test, guardrail, workflow/script, generated artifact, and architecture document required by `AGENTS.md`.
3. Add Given/When/Then regression tests for success, failure, boundaries, malformed input, dependency failure, fail-close/fail-soft behavior, stale scope, authorization, and observability boundaries as applicable.
4. For DB changes, add a new migration, regenerate `types/supabase.ts` with the pinned CLI path, and run `pnpm run check:final`. Never edit historical migrations or generated Supabase types manually.
5. Run focused tests first, then `pnpm run check`; use `pnpm run check:final` for DB/generated-type surfaces. Record every command and result for the PR body.
6. Commit each completed unit with a Japanese Conventional Commit message. Push through the normal pre-push gate.

Before opening the final fix PR, rerun the all-time unresolved query. Add newly discovered issues to the inventory and handle them in this wave; do not silently defer them as out of scope.

## 4. Open ready `develop` PRs

Create non-draft PRs with `--body-file`. Include:

- the Sentry issue inventory and root-cause mapping;
- the canonical fix and removed fallback/noise path;
- focused and full validation results;
- DB/docs/guardrail/deploy impact;
- every cross-scope finding classified as fixed, tracked, or proven not actionable;
- rollback and post-release verification steps.

Never put raw Sentry event payloads or secrets in the PR.

## 5. Require a current-head Codex review

Use `scripts/codex-review-gate.mjs` from this skill for every `develop` fix PR and the `main` release PR.

Request review only after the intended head is pushed and local validation is complete:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/resolve-welbase-sentry-incidents/scripts/codex-review-gate.mjs" request --pr 123
```

Run this immediately after creating the ready PR, before waiting for CI or an automatic Codex review. This makes a clean bot reaction unambiguously post-request whenever possible.

Record the returned `requestCommentId`, `requestedAt`, and full `headRefOid`. Poll without blocking user updates for more than 60 seconds:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/resolve-welbase-sentry-incidents/scripts/codex-review-gate.mjs" status \
  --pr 123 \
  --request-comment-id 456789 \
  --head 0123456789abcdef0123456789abcdef01234567
```

Interpret the state strictly:

- `clean`: Codex either reacted `+1` on the PR or review request after the recorded trigger, or emitted an explicit no-findings completion whose reviewed commit matches the exact head. Accept both when both exist. This OR is intentional: GitHub allows only one reaction of a given kind per actor, so a clean re-review can emit the exact-head completion without creating a second `+1`. A finding always wins: collect every Codex review comment and finding summary bound to the current head even if it predates the latest trigger. A reaction from before the trigger and a no-findings artifact for another SHA are both invalid.
- `findings`: Read every Codex review comment and the touched source. Root-fix the issue, add/strengthen tests, commit, push, reply in Japanese, and resolve the thread only after verifying the live head. Then request a new review for the new SHA; an older clean result is invalid.
- `pending`: Keep checking the same request. Do not merge and do not replace the Codex gate with a self-review.
- `unavailable`: Codex returned a usage-limit or service-unavailable response. Retry at most once for the unchanged head after the external condition can reasonably have cleared; otherwise report the external blocker and do not merge.
- `stale`: The PR head changed after the request. Run applicable tests and request a fresh Codex review.

The helper accepts only the compiled connector identity `chatgpt-codex-connector[bot]` and checks reactions on both the PR and the request comment. A finding always wins over thumbs-up/no-findings signals. If GitHub changes the bot identity or response contract, verify the GitHub App identity and update the helper in a reviewed code change; never override or weaken the merge gate at runtime.

## 6. Enforce the live merge gate

Immediately before each merge, refresh the exact head and require all of these:

- the helper returns `clean` for the current full head SHA;
- every paginated GraphQL `reviewThreads(first:100, after:$cursor)` page has zero unresolved active threads; continue through `pageInfo.endCursor` while `hasNextPage` is true;
- required GitHub checks, Quality Gates, Playwright when selected, and Vercel are successful;
- `mergeStateStatus` is `CLEAN` and `mergeable` is `MERGEABLE`;
- the PR is ready, the approved/reviewed head did not change, and no new Sentry evidence invalidates the fix;
- the applicable local final gate passed.

Merge `develop` PRs with the repository's normal squash policy and `--match-head-commit <reviewed-full-SHA>` so a concurrent push cannot bypass review. Verify `state=MERGED`, `mergedAt`, and `mergeCommit` from GitHub rather than inferring success from local ancestry. Rescan review threads and checks after every fix push.

## 7. Release `develop` to `main`

After every incident fix PR is merged:

1. Fetch/prune and inspect unique commits on both branches.
2. Use `git merge-tree --write-tree origin/main origin/develop` and compare the result with `origin/develop^{tree}`.
3. If `main` contains unique changes or the merge is not clean, sync `main` back into `develop` through its own reviewed PR first. Never force, drop, or overwrite main-only work.
4. Open one ready `develop -> main` release PR with `--body-file`, listing every included fix PR/Sentry issue and validation result.
5. Run the same current-head Codex review loop and live merge gate. Use a merge commit plus `--match-head-commit <reviewed-full-SHA>` for the release PR when preserving `develop` ancestry is required by repository history.
6. Verify the GitHub merged state and the post-merge `main` workflow.

## 8. Verify production and close Sentry

1. Verify the Vercel production deployment corresponds to the merged `main` SHA and succeeded.
2. Verify the Sentry release/commit mapping for that SHA.
3. Exercise safe representative paths or wait through a bounded, explicitly reported observation window. Compare each issue's `lastSeen`, count, release, and environment with the baseline.
4. Resolve each fixed issue against the verified production release or commit:

```bash
sentry issue resolve first-step/welbase#WELBASE-XX --in <verified-release>
```

5. Rerun the all-time fresh unresolved inventory. If anything remains, return to classification; do not declare partial success as completion.
6. Verify merged PRs, target-branch CI, production deploy, Sentry state, clean worktrees/branches, and a clean/synced root `develop` checkout.
7. Send the required Moshi completion webhook using `MOSHI_WEBHOOK_TOKEN`. Never print or commit the token.

Report the initial/final issue counts, per-issue root action, develop and main PR URLs/merge SHAs, Codex review evidence, local/CI gates, production deployment, Sentry resolution state, observation window, cleanup, and any genuinely blocked external action.

## Stop conditions

Stop and ask for authority only when completion needs credentials, production mutation, a product decision outside the user's granted scope, or the required Codex service remains unavailable after one bounded retry. Do not stop for ordinary implementation choices, CI queueing, review findings, or a large issue count. Never merge with pending/unavailable/stale Codex review, unresolved threads, failing checks, unverified production state, or an unresolved issue silently left behind.
