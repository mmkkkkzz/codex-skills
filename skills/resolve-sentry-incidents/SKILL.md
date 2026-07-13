---
name: resolve-sentry-incidents
description: "Resolve a project's complete live unresolved Sentry queue end to end: inventory every issue, classify and root-fix each cause, add regression coverage, merge reviewed fixes through the repository's release flow, verify the production deployment, resolve Sentry issues against the verified release, and confirm the final queue is empty. Use only when the user explicitly asks to handle every or all unresolved Sentry issues, drain or clear the full Sentry backlog, or sweep the complete unresolved queue through production. Do not use for one named incident, investigation-only requests, or requests that do not authorize the necessary repository and production changes."
---

# Resolve Sentry Incidents

Drain one explicit Sentry project’s complete unresolved queue through its real production release path. Treat Sentry, source control, CI, deployment, and production as live sources of truth.

## Required end state

Finish only after all applicable conditions hold:

- Classify every issue from the initial all-time unresolved snapshot and apply one verified root action.
- Add any newly unresolved issues found by a fresh pre-release scan to the same wave.
- Pass focused regression coverage and every repository-required local and CI gate.
- Merge each fix only after an exact-head Codex review completes cleanly.
- Propagate fixes through the repository’s actual release topology without dropping production-only changes.
- Verify the production deployment and Sentry release for the released commit.
- Resolve fixed issues against that verified release; never archive or ignore them as a substitute for remediation.
- Confirm a final fresh unresolved scan is empty.
- Clean temporary evidence, worktrees, and branches safely, and run any completion notification required by repository or user instructions.

## 1. Resolve project configuration

1. Read the target repository’s instructions and planning conventions before changing anything.
2. Resolve and record these values from user context, repository config, deployment metadata, and live services:
   - repository root and `owner/name`;
   - explicit Sentry `org/project` target;
   - integration branch, production branch, and any promotion PR path;
   - required checks, test commands, commit/PR conventions, deployment provider, and completion notification;
   - production environment and Sentry release identifier format.
3. Do not guess a production target, branch topology, deployment, or release mapping. Ask only if live sources cannot resolve a production-affecting value safely.
4. Create or update the repository’s required execution plan. For a multi-incident wave, keep an issue ledger, discoveries, decisions, validation, and closeout state resumable without copying sensitive event data.
5. Verify source-control, GitHub CLI, Sentry CLI, deployment, and production access required by the resolved workflow.
6. Inspect repository cleanliness, worktrees, open PRs, and remote branches. Preserve unrelated changes and take over an equivalent open fix instead of duplicating it.
7. Fetch/prune the remote, branch from the current integration branch, and use a dedicated worktree when the repository workflow supports it. Never implement directly on the production branch.

Capture the all-time unresolved inventory with fresh data, replacing placeholders with the resolved scope:

```bash
sentry issue list <org>/<project> \
  --query 'is:unresolved' \
  --period '>=1970-01-01' \
  --limit 1000 \
  --fresh \
  --json \
  --fields id,shortId,title,culprit,count,userCount,firstSeen,lastSeen,level,status,priority,substatus,isUnhandled,permalink
```

If `hasMore` is true, follow `next` cursors until it is false and deduplicate pages by issue `id`. Keep raw event payloads only in protected temporary artifacts; never commit or print secrets, personal data, request payloads, replay data, or unsanitized Sentry extras.

Capture each issue’s current event and trace with the bundled helper:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/resolve-sentry-incidents/scripts/capture-sentry-issue.mjs" \
  --issue <org>/<project>#<ISSUE-ID> \
  --out-dir /tmp/sentry-incident-evidence
```

The helper prints only a sanitized routing summary and the mode-0600 artifact path. Inspect the raw file only with targeted selectors that exclude exception messages, breadcrumbs, request bodies/headers/query strings, variables, source context, replay IDs, and span descriptions. Remove the evidence directory at closeout.

Track issue ID, latest event/release/environment, affected route or job, user impact, suspected shared cause, disposition, fix evidence, tests, target PR, and final Sentry state.

## 2. Classify without hiding failures

Assign every issue to exactly one root-action class:

- **Product defect:** Fix the canonical shared runtime path, not one observed callsite.
- **Expected handled outcome reported as an error:** Narrow monitoring suppression to the exact typed boundary while preserving unexpected failures, user-visible errors, and operational evidence.
- **Transient dependency or network failure:** Add bounded retry, aggregation, or recovery behavior while keeping sustained outages and failed manual recovery observable.
- **Configuration, deployment, or migration drift:** Correct the canonical state and add a recurrence guardrail or runbook check.
- **Already fixed:** Prove the deployed release contains the root fix and that `lastSeen` and count did not advance after it.
- **Duplicate symptoms of one cause:** Map every issue to the shared fix and verify each issue separately after release.

Do not classify by title alone. Correlate stack, breadcrumbs, route, tags, release, environment, count, first/last seen, and repository history. Do not resolve, ignore, archive, merge groups, or create tracker tickets merely to make the unresolved queue look empty. Instrumentation alone is not a root fix.

## 3. Implement root fixes

1. Group issues that share one cause. Prefer one coherent incident-wave PR; split unrelated or high-risk causes when independent review and rollback are safer.
2. Fix the canonical design and remove obsolete fallback or compatibility paths. Update every caller, test, guardrail, generated artifact, migration, and architecture document required by repository instructions.
3. Add Given/When/Then regression tests for applicable success, failure, boundary, malformed-input, dependency-failure, stale-scope, authorization, recovery, and observability cases.
4. Follow the repository’s database and generated-file workflow exactly. Never edit historical migrations or generated artifacts manually unless its instructions explicitly require that operation.
5. Run focused tests first, then the repository’s complete applicable local gate. Record exact commands and results for the PR body.
6. Commit and push using the repository’s required message format and pre-push gate.

Before opening the final fix PR, rerun the all-time unresolved query. Add newly discovered issues to this wave instead of silently deferring them.

## 4. Open ready fix PRs

Open non-draft PRs against the resolved integration branch using a body file. Include:

- the sanitized Sentry inventory and root-cause mapping;
- the canonical fix and removed fallback or noise path;
- focused and full validation results;
- migration, documentation, guardrail, and deployment impact;
- every cross-scope finding classified as fixed, tracked with explicit authority, or proven not actionable;
- rollback and post-release verification steps.

Never include raw Sentry event payloads or secrets.

## 5. Require an exact-head Codex review

Use the bundled gate for every fix PR and every promotion or release PR:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/resolve-sentry-incidents/scripts/codex-review-gate.mjs" request \
  --repo <owner>/<name> \
  --pr 123
```

Request review only after the intended head is pushed and local validation is complete. Run it immediately after creating the ready PR so a clean bot signal is unambiguously post-request whenever possible.

Record the returned `requestCommentId`, `requestedAt`, and full `headRefOid`. Poll without blocking user updates for more than 60 seconds:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/resolve-sentry-incidents/scripts/codex-review-gate.mjs" status \
  --repo <owner>/<name> \
  --pr 123 \
  --request-comment-id 456789 \
  --head 0123456789abcdef0123456789abcdef01234567
```

Interpret states strictly:

- `clean`: Accept a post-request Codex `+1` reaction or an explicit no-findings completion for the exact head. A finding emitted by a Codex review whose parent review commit is the exact head always wins, even if it predates the latest trigger or its thread was manually resolved. Never infer provenance from a review comment’s mutable `commit_id`; GitHub can rebind it to a later head.
- `findings`: Read every finding and the touched source, root-fix it, strengthen tests, commit and push a new head, reply according to repository conventions, resolve the thread only after verification, and request a fresh review for the new SHA.
- `pending`: Keep checking the same request. Evidence-integrity failures also fail closed as pending; do not merge or substitute a self-review.
- `unavailable`: Retry at most once for the unchanged head after the external condition can reasonably have cleared. Otherwise report the external blocker and do not merge.
- `stale`: The PR head changed after the request. Run applicable tests and request a fresh review.

The helper accepts only its compiled Codex GitHub App identity and checks reactions on both the PR and request comment. If GitHub changes the App identity or response contract, verify the App identity and update the helper in a reviewed code change. Never weaken the gate at runtime.

## 6. Enforce the live merge gate

Immediately before each merge, refresh the exact head and require all of these:

- the helper returns `clean` for the current full head SHA;
- every paginated GraphQL `reviewThreads(first:100, after:$cursor)` page has zero unresolved threads;
- all required CI, deployment-preview, and repository-specific checks succeed;
- the provider reports the PR mergeable and clean;
- the reviewed head remains unchanged and no new Sentry evidence invalidates the fix;
- the applicable local final gate passed.

Merge with the repository’s required strategy and an exact-head guard such as `--match-head-commit <reviewed-full-SHA>`. Verify the remote merged state and merge commit instead of inferring success from local ancestry. Rescan threads and checks after every fix push.

## 7. Release through the repository topology

After all fixes reach the integration branch:

1. Resolve the live production promotion path. If integration and production are separate branches, inspect unique commits on both and prove the promotion does not drop production-only work. Use `git merge-tree` or the repository’s equivalent safe merge analysis.
2. If production contains unique changes or promotion conflicts, sync them through the repository’s normal reviewed path first. Never force, drop, or overwrite production-only work.
3. Open any required ready promotion PR and list every included fix PR, Sentry issue, and validation result.
4. Apply the same exact-head Codex review loop and live merge gate.
5. Verify the remote merge state and post-merge production workflow. For a single-branch release model, verify the production workflow for the merged fix commit directly.

## 8. Verify production and close Sentry

1. Verify the production deployment provider reports success for the released commit.
2. Verify the Sentry release and commit mapping for that commit.
3. Exercise safe representative paths or observe for a bounded, explicitly reported window. Compare each issue’s `lastSeen`, count, release, and environment with the baseline.
4. Resolve each fixed issue against the verified release:

```bash
sentry issue resolve <org>/<project>#<ISSUE-ID> --in <verified-release>
```

5. Rerun the all-time fresh unresolved inventory. If anything remains, return to classification.
6. Verify merged PRs, target-branch CI, deployment, Sentry state, clean worktrees/branches, and a clean synchronized primary checkout.
7. Run the completion notification required by the user or repository without printing or committing notification credentials.

Report the initial/final issue counts, per-issue root action, PR URLs and merge SHAs, Codex review evidence, local/CI gates, deployment and Sentry release evidence, observation window, final Sentry state, cleanup, and any genuinely blocked external action.

## Stop conditions

Stop and request authority only when completion needs missing credentials, an unauthorized production mutation, a product decision outside the granted scope, an unresolved production target, or the required Codex service remains unavailable after one bounded retry. Do not stop for ordinary implementation choices, CI queueing, review findings, or a large issue count. Never merge with pending, unavailable, or stale review evidence; unresolved threads; failing checks; an unverified deployment; or an unresolved issue silently left behind.
