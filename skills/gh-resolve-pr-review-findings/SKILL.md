---
name: gh-resolve-pr-review-findings
description: Resolve actionable GitHub PR review findings end to end. Use when the user asks Codex to address PR review feedback, review findings, session/prompt-supplied findings, unresolved GitHub PR review comments, or "対応すべきものは根本対応してpush、不要なものは理由付きで報告、対応したPRレビューコメントはresolve" style requests.
---

# Resolve PR Review Findings

Use this workflow to turn review feedback into real fixes, not just acknowledgements. Gather every active feedback source into a feedback ledger, classify each item with code/test/schema evidence, implement root-cause fixes for actionable items, validate, commit, push, resolve only the GitHub review threads actually addressed, and re-check thread state before stopping.

## Workflow

1. **Preflight**
   - Check `git status -sb`, current branch, repo remote, and `gh auth status`.
   - Find the open PR for the current branch with `gh pr view --json number,url,headRefName,baseRefName,reviewDecision`.
   - If `gh` is unauthenticated or no PR can be discovered, ask the user for the minimum missing information.
   - Do not overwrite unrelated dirty work. Read and work with existing changes.

2. **Collect Feedback**
   - Include findings explicitly provided in the current user prompt.
   - Include relevant findings already visible in the current session history.
   - Fetch unresolved PR review threads and review/issue comments from GitHub. Prefer thread-level data so resolved state is not guessed.
   - Do not conclude that no comments exist from top-level PR comments alone. If a convenience field such as `gh pr view --json reviewThreads` is unsupported, use a repository helper such as `scripts/fetch_comments.py` when present, or call GitHub GraphQL `reviewThreads` directly.
   - Treat duplicate findings as one work item while preserving all linked comment/thread IDs.
   - Build a feedback ledger before implementing. For each work item, track source, linked comment/thread IDs, affected path/line, current classification, evidence checked, planned fix or rejection reason, validation, pushed commit, and whether each linked thread was resolved.

3. **Classify**
   - Mark as **actionable** when the feedback points to a bug, data loss risk, security/tenant boundary issue, silent failure, type drift, stale UI, missing high-value tests, broken docs contract, or operational risk.
   - Mark as **not required** only when the premise is false, already fixed in the PR, intentionally out of scope, blocked by repo policy, or riskier than the requested change. Capture the evidence needed for the final report.
   - Inspect code, tests, schema, docs, or PR diff evidence before finalizing every classification, including actionable items. Do not dismiss or accept a finding based on intuition alone.
   - When multiple unresolved threads map to one work item, keep every thread ID linked so all addressed duplicates can be resolved after the fix is pushed.
   - If every item is classified as not required or non-resolvable, do not invent a code change, empty commit, push, or thread resolution just to complete the workflow. Skip to the final report with evidence and remaining unresolved/non-resolvable state.

4. **Root Fix**
   - Fix the underlying behavior or contract. Avoid papering over symptoms with broad catches, weaker tests, or expectation changes unless the test was wrong.
   - Update all affected surfaces together: app code, DB migrations, generated types, docs, tests, fixtures, and UI routes as applicable.
   - For DB changes, follow the repo's migration rules. Add a new migration unless the repo explicitly permits editing an existing one.
   - For review comments on tests, add behavioral tests that would fail without the fix.
   - Keep changes scoped to the review items and nearby contracts.

5. **Validate**
   - Run focused tests for changed areas first.
   - Run the repo's final validation command before pushing. If the repo documents a stronger command such as `check:final`, use it when generated DB types or migrations changed.
   - If validation cannot complete for an external reason, collect exact command/status and explain the residual risk.
   - If validation fails because of the changed code, treat the fix as incomplete. Continue root-cause debugging and rerun validation until it passes. Do not push or resolve threads while this failure remains.
   - If an internal validation failure cannot be fixed in the current turn, stop before push/resolve and report the exact failing command, status, relevant output, affected work items, and pending thread IDs.

6. **Commit and Push**
   - Review `git diff --check`, `git status -sb`, and the staged diff.
   - Commit and push only when there are actual changes for actionable work items and required validation has passed.
   - Commit with the repo's commit style and a message that describes the review fixes.
   - Push the current branch.

7. **Resolve GitHub Threads**
   - Resolve only PR review threads whose comments were actually addressed by the pushed commits.
   - Do not resolve comments classified as not required unless the user explicitly asks to close rejected threads.
   - Issue comments and general PR comments usually cannot be resolved; report them as addressed/not-required instead.
   - When one pushed fix addresses duplicate unresolved review threads, resolve every linked thread ID for that fixed work item.
   - After each resolution batch, fetch thread-aware PR review state again using the same reliable collection path. Do not stop until there are no actionable unresolved review threads left, or the remaining unresolved items are explicitly classified as not required or non-resolvable and reported with evidence.

8. **Final Report**
   - List what was fixed, grouped by review finding when useful.
   - List not-required items with concise evidence.
   - Include validation commands and outcomes.
   - If no commit/push was made because there were no actionable items or validation remained blocked, say so explicitly.
   - Include commit SHA(s), branch pushed, resolved thread count/IDs, and the post-resolve re-fetch result. If unresolved items remain, list each one with its classification and reason.

## GitHub Commands

Discover repo and PR:

```bash
gh repo view --json owner,name
gh pr view --json number,url,headRefName,baseRefName,reviewDecision
gh pr diff --name-only
```

Fetch review threads:

```bash
gh api graphql \
  -f owner="$OWNER" \
  -f name="$REPO" \
  -F pr="$PR_NUMBER" \
  -f query='
query($owner:String!, $name:String!, $pr:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$pr) {
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          path
          line
          startLine
          comments(first:50) {
            nodes {
              id
              author { login }
              body
              createdAt
              url
              diffHunk
            }
          }
        }
      }
    }
  }
}'
```

Resolve a handled thread:

```bash
gh api graphql \
  -f threadId="$THREAD_ID" \
  -f query='
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) {
    thread { id isResolved }
  }
}'
```

## Discipline

- Prefer evidence from code, schema, tests, and PR thread state over assumptions.
- Do not use destructive git commands.
- Do not push partial fixes unless the user explicitly asks for incremental pushes.
- Do not resolve GitHub threads before the corresponding fix is committed and pushed.
- If posting any GitHub response, use the repository's language conventions; when this repo says review comments are Japanese, write Japanese.
