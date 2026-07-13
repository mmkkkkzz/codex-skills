#!/usr/bin/env node

import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import process from 'node:process'

const DEFAULT_BOT_LOGINS = ['chatgpt-codex-connector[bot]']
const NO_FINDINGS_PATTERN = /Codex Review:[\s\S]*Didn't find any major issues/i
const REVIEWED_COMMIT_PATTERN = /Reviewed commit:\*\*\s*`([0-9a-f]{7,40})`/i
const UNAVAILABLE_PATTERN = /reached your Codex usage limits for code reviews/i

function fail(message, exitCode = 1) {
  process.stderr.write(`${message}\n`)
  process.exit(exitCode)
}

function parseArgs(argv) {
  const [command, ...rest] = argv
  const options = {}

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index]
    if (!token.startsWith('--')) {
      fail(`Unexpected argument: ${token}`)
    }

    const key = token.slice(2)
    const value = rest[index + 1]
    if (!value || value.startsWith('--')) {
      fail(`Missing value for --${key}`)
    }

    options[key] = value
    index += 1
  }

  return { command, options }
}

function runGh(args) {
  const result = spawnSync('gh', args, {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  if (result.error) {
    fail(`Unable to run gh: ${result.error.message}`)
  }
  if (result.status !== 0) {
    fail(result.stderr.trim() || `gh ${args.join(' ')} failed`)
  }

  return result.stdout.trim()
}

function runGhJson(args) {
  const output = runGh(args)
  if (!output) return null

  try {
    return JSON.parse(output)
  } catch (error) {
    fail(`gh returned invalid JSON: ${error.message}`)
  }
}

function flattenPages(value) {
  if (!Array.isArray(value)) return []
  return value.flatMap((page) => (Array.isArray(page) ? page : [page]))
}

function getPaged(endpoint) {
  return flattenPages(
    runGhJson(['api', '--paginate', '--slurp', '-H', 'Accept: application/vnd.github+json', endpoint]),
  )
}

function normalizeRepo(repo) {
  const resolved = repo || runGh(['repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner'])
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(resolved)) {
    fail(`Invalid repository: ${resolved}`)
  }
  return resolved
}

function normalizePr(value) {
  if (!/^\d+$/.test(value || '')) fail('--pr must be a positive integer')
  return Number(value)
}

function normalizeHead(value) {
  if (!/^[0-9a-f]{40}$/i.test(value || '')) fail('--head must be a full 40-character commit SHA')
  return value.toLowerCase()
}

function getPr(repo, pr) {
  return runGhJson([
    'pr',
    'view',
    String(pr),
    '--repo',
    repo,
    '--json',
    'number,url,state,isDraft,headRefOid,baseRefName,headRefName',
  ])
}

function isCodexBot(login, botLogins) {
  return Boolean(login) && botLogins.has(login.toLowerCase())
}

function isAtOrAfter(value, threshold) {
  const timestamp = Date.parse(value || '')
  return Number.isFinite(timestamp) && timestamp >= threshold
}

function matchesReviewedHead(body, head) {
  const match = String(body || '').match(REVIEWED_COMMIT_PATTERN)
  return Boolean(match) && match[1].length >= 7 && head.startsWith(match[1].toLowerCase())
}

function serializeFinding(comment) {
  return {
    id: comment.id,
    url: comment.html_url,
    path: comment.path,
    line: comment.line ?? comment.original_line ?? null,
    createdAt: comment.created_at,
    body: comment.body,
  }
}

function serializeReviewFinding(review) {
  return {
    id: review.id,
    url: review.html_url,
    path: null,
    line: null,
    createdAt: review.submitted_at,
    body: review.body,
  }
}

function classifyEvidence({
  prReactions,
  requestReactions,
  issueComments,
  reviews,
  reviewComments,
  requestedAt,
  head,
  botLogins,
}) {
  const threshold = Date.parse(requestedAt)
  if (!Number.isFinite(threshold)) throw new Error(`Invalid request timestamp: ${requestedAt}`)

  const codexReactions = [...prReactions, ...requestReactions].filter(
    (reaction) =>
      isCodexBot(reaction.user?.login, botLogins) &&
      isAtOrAfter(reaction.created_at, threshold),
  )
  const codexIssueComments = issueComments.filter(
    (comment) =>
      isCodexBot(comment.user?.login, botLogins) && isAtOrAfter(comment.created_at, threshold),
  )
  const codexReviewsForHead = reviews.filter(
    (review) =>
      isCodexBot(review.user?.login, botLogins) &&
      String(review.commit_id || '').toLowerCase() === head,
  )
  const codexReviewsAfterRequest = codexReviewsForHead.filter((review) =>
    isAtOrAfter(review.submitted_at, threshold),
  )
  // GitHub can rewrite a review comment's commit_id when later commits move its
  // diff position. The parent review's commit_id remains the reviewed SHA.
  const reviewsById = new Map(reviews.map((review) => [Number(review.id), review]))
  const codexRootReviewComments = reviewComments.filter(
    (comment) =>
      isCodexBot(comment.user?.login, botLogins) &&
      comment.in_reply_to_id == null,
  )
  const unmatchedCodexReviewComments = codexRootReviewComments.filter((comment) => {
    const parentReview = reviewsById.get(Number(comment.pull_request_review_id))
    return !parentReview || !isCodexBot(parentReview.user?.login, botLogins)
  })
  const codexReviewIdsForHead = new Set(
    codexReviewsForHead.map((review) => Number(review.id)),
  )
  const codexReviewCommentsForHead = codexRootReviewComments.filter((comment) =>
    codexReviewIdsForHead.has(Number(comment.pull_request_review_id)),
  )

  const codexReviewSummaries = codexReviewsForHead.filter(
    (review) =>
      String(review.body || '').trim() &&
      !NO_FINDINGS_PATTERN.test(String(review.body || '')) &&
      !codexReviewCommentsForHead.some(
        (comment) => Number(comment.pull_request_review_id) === Number(review.id),
      ),
  )

  if (codexReviewCommentsForHead.length > 0 || codexReviewSummaries.length > 0) {
    return {
      state: 'findings',
      acceptedSignal: null,
      findings: [
        ...codexReviewCommentsForHead.map(serializeFinding),
        ...codexReviewSummaries.map(serializeReviewFinding),
      ],
      codexReviewIds: codexReviewsForHead.map((review) => review.id),
    }
  }

  if (unmatchedCodexReviewComments.length > 0) {
    return {
      state: 'pending',
      reason: 'incomplete_parent_review_evidence',
      acceptedSignal: null,
      findings: [],
      unmatchedReviewCommentIds: unmatchedCodexReviewComments.map((comment) => comment.id),
      codexReviewIds: codexReviewsForHead.map((review) => review.id),
    }
  }

  const unavailableComment = codexIssueComments.find((comment) =>
    UNAVAILABLE_PATTERN.test(String(comment.body || '')),
  )
  if (unavailableComment) {
    return {
      state: 'unavailable',
      reason: 'codex_usage_limit',
      acceptedSignal: null,
      signalUrl: unavailableComment.html_url,
      findings: [],
      codexReviewIds: codexReviewsForHead.map((review) => review.id),
    }
  }

  const noFindingsComment = codexIssueComments.find(
    (comment) =>
      NO_FINDINGS_PATTERN.test(String(comment.body || '')) &&
      matchesReviewedHead(comment.body, head),
  )
  const noFindingsReview = codexReviewsAfterRequest.find((review) =>
    NO_FINDINGS_PATTERN.test(String(review.body || '')),
  )
  const thumbsUp = codexReactions.find((reaction) => reaction.content === '+1')
  const noFindingsArtifact = noFindingsComment || noFindingsReview

  if (thumbsUp || noFindingsArtifact) {
    let acceptedSignal = 'post_request_thumbs_up'
    if (thumbsUp && noFindingsArtifact) {
      acceptedSignal = 'post_request_thumbs_up_and_exact_head_no_findings'
    } else if (noFindingsArtifact) {
      acceptedSignal = 'exact_head_no_findings'
    }

    return {
      state: 'clean',
      acceptedSignal,
      signalUrl: noFindingsArtifact?.html_url ?? null,
      signalReactionId: thumbsUp?.id ?? null,
      findings: [],
      codexReviewIds: codexReviewsForHead.map((review) => review.id),
    }
  }

  return {
    state: 'pending',
    acceptedSignal: null,
    observedSignals: {
      thumbsUp: Boolean(thumbsUp),
      explicitNoFindings: Boolean(noFindingsArtifact),
    },
    findings: [],
    codexReviewIds: codexReviewsForHead.map((review) => review.id),
  }
}

function printJson(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`)
}

function requestReview(options) {
  const repo = normalizeRepo(options.repo)
  const pr = normalizePr(options.pr)
  const before = getPr(repo, pr)

  if (before.state !== 'OPEN') fail(`PR #${pr} is not open`)
  if (before.isDraft) fail(`PR #${pr} is draft; mark it ready before requesting Codex review`)

  const comment = runGhJson([
    'api',
    '--method',
    'POST',
    '-H',
    'Accept: application/vnd.github+json',
    `repos/${repo}/issues/${pr}/comments`,
    '-f',
    'body=@codex review',
  ])
  const after = getPr(repo, pr)

  if (before.headRefOid !== after.headRefOid) {
    printJson({
      state: 'stale',
      reason: 'head_changed_while_requesting_review',
      repo,
      pr,
      requestCommentId: comment.id,
      requestedAt: comment.created_at,
      requestedHeadRefOid: before.headRefOid,
      currentHeadRefOid: after.headRefOid,
      requestUrl: comment.html_url,
    })
    process.exitCode = 4
    return
  }

  printJson({
    state: 'requested',
    repo,
    pr,
    requestCommentId: comment.id,
    requestedAt: comment.created_at,
    headRefOid: after.headRefOid,
    requestUrl: comment.html_url,
    prUrl: after.url,
  })
}

function reviewStatus(options) {
  const repo = normalizeRepo(options.repo)
  const pr = normalizePr(options.pr)
  const head = normalizeHead(options.head)
  const requestCommentId = options['request-comment-id']
  if (!/^\d+$/.test(requestCommentId || '')) {
    fail('--request-comment-id must be a positive integer')
  }

  const prState = getPr(repo, pr)
  if (String(prState.headRefOid).toLowerCase() !== head) {
    printJson({
      state: 'stale',
      reason: 'pr_head_changed',
      repo,
      pr,
      requestedHeadRefOid: head,
      currentHeadRefOid: prState.headRefOid,
    })
    process.exitCode = 4
    return
  }

  const requestComment = runGhJson([
    'api',
    '-H',
    'Accept: application/vnd.github+json',
    `repos/${repo}/issues/comments/${requestCommentId}`,
  ])
  if (String(requestComment.body || '').trim() !== '@codex review') {
    fail(`Comment ${requestCommentId} is not an @codex review request`)
  }
  if (!String(requestComment.issue_url || '').endsWith(`/issues/${pr}`)) {
    fail(`Comment ${requestCommentId} does not belong to PR #${pr}`)
  }

  const botLogins = new Set(DEFAULT_BOT_LOGINS)

  const requestReactions = getPaged(
    `repos/${repo}/issues/comments/${requestCommentId}/reactions?per_page=100`,
  )
  const prReactions = getPaged(`repos/${repo}/issues/${pr}/reactions?per_page=100`)
  const issueComments = getPaged(`repos/${repo}/issues/${pr}/comments?per_page=100`)
  const reviews = getPaged(`repos/${repo}/pulls/${pr}/reviews?per_page=100`)
  const reviewComments = getPaged(`repos/${repo}/pulls/${pr}/comments?per_page=100`)

  const result = classifyEvidence({
    prReactions,
    requestReactions,
    issueComments,
    reviews,
    reviewComments,
    requestedAt: requestComment.created_at,
    head,
    botLogins,
  })

  const afterEvidence = getPr(repo, pr)
  if (String(afterEvidence.headRefOid).toLowerCase() !== head) {
    printJson({
      state: 'stale',
      reason: 'pr_head_changed_while_collecting_evidence',
      repo,
      pr,
      requestedHeadRefOid: head,
      currentHeadRefOid: afterEvidence.headRefOid,
    })
    process.exitCode = 4
    return
  }

  printJson({
    ...result,
    repo,
    pr,
    requestCommentId: Number(requestCommentId),
    requestedAt: requestComment.created_at,
    headRefOid: head,
    botLogins: [...botLogins],
  })

  if (result.state === 'findings') process.exitCode = 2
  if (result.state === 'pending') process.exitCode = 3
  if (result.state === 'unavailable') process.exitCode = 5
}

function selfTest() {
  const botLogins = new Set(DEFAULT_BOT_LOGINS)
  const head = '0123456789abcdef0123456789abcdef01234567'
  const requestedAt = '2026-07-13T00:00:00Z'
  const base = {
    prReactions: [],
    requestReactions: [],
    issueComments: [],
    reviews: [],
    reviewComments: [],
    requestedAt,
    head,
    botLogins,
  }

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: '+1',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      issueComments: [
        {
          body: `Codex Review: Didn't find any major issues.\n\n**Reviewed commit:** \`0123456789\``,
          created_at: '2026-07-13T00:01:00Z',
          html_url: 'https://example.test/comment',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).acceptedSignal,
    'post_request_thumbs_up_and_exact_head_no_findings',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: '+1',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      reviews: [
        {
          id: 10,
          body: 'Codex Review: automated suggestions follow',
          submitted_at: '2026-07-13T00:01:00Z',
          commit_id: head,
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      reviewComments: [
        {
          id: 1,
          body: 'Fix this',
          created_at: '2026-07-13T00:01:00Z',
          commit_id: head,
          pull_request_review_id: 10,
          in_reply_to_id: null,
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).state,
    'findings',
  )

  const preRequestFindingResult = classifyEvidence({
    ...base,
    prReactions: [
      {
        content: '+1',
        created_at: '2026-07-13T00:01:00Z',
        user: { login: DEFAULT_BOT_LOGINS[0] },
      },
    ],
    reviews: [
      {
        id: 5,
        body: 'Codex Review: automated suggestions follow',
        submitted_at: '2026-07-12T23:59:00Z',
        commit_id: head,
        user: { login: DEFAULT_BOT_LOGINS[0] },
      },
    ],
    reviewComments: [
      {
        id: 6,
        body: 'Existing current-head finding',
        created_at: '2026-07-12T23:59:00Z',
        commit_id: head,
        pull_request_review_id: 5,
        in_reply_to_id: null,
        user: { login: DEFAULT_BOT_LOGINS[0] },
      },
    ],
  })
  assert.equal(preRequestFindingResult.state, 'findings')
  assert.equal(preRequestFindingResult.findings.length, 1)

  assert.equal(
    classifyEvidence({
      ...base,
      issueComments: [
        {
          body: `Codex Review: Didn't find any major issues.\n\n**Reviewed commit:** \`0123456789\``,
          created_at: '2026-07-13T00:01:00Z',
          html_url: 'https://example.test/comment',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).acceptedSignal,
    'exact_head_no_findings',
  )

  const matchingNoFindingsComment = {
    body: `Codex Review: Didn't find any major issues.\n\n**Reviewed commit:** \`0123456789\``,
    created_at: '2026-07-13T00:01:00Z',
    html_url: 'https://example.test/comment',
    user: { login: DEFAULT_BOT_LOGINS[0] },
  }

  const previousHead = 'fedcba9876543210fedcba9876543210fedcba98'
  const historicalReview = {
    id: 20,
    body: 'Codex Review: automated suggestions follow',
    submitted_at: '2026-07-12T23:59:00Z',
    commit_id: previousHead,
    user: { login: DEFAULT_BOT_LOGINS[0] },
  }
  const reboundHistoricalComment = {
    id: 21,
    body: 'Historical finding rebound by GitHub',
    created_at: '2026-07-12T23:59:00Z',
    commit_id: head,
    original_commit_id: previousHead,
    pull_request_review_id: historicalReview.id,
    in_reply_to_id: null,
    user: { login: DEFAULT_BOT_LOGINS[0] },
  }

  assert.equal(
    classifyEvidence({
      ...base,
      issueComments: [matchingNoFindingsComment],
      reviews: [historicalReview],
      reviewComments: [reboundHistoricalComment],
    }).state,
    'clean',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      reviews: [historicalReview],
      reviewComments: [reboundHistoricalComment],
    }).state,
    'pending',
  )

  const incompleteParentEvidence = classifyEvidence({
    ...base,
    issueComments: [matchingNoFindingsComment],
    reviewComments: [
      {
        ...reboundHistoricalComment,
        id: 22,
        pull_request_review_id: 999,
      },
    ],
  })
  assert.equal(incompleteParentEvidence.state, 'pending')
  assert.equal(incompleteParentEvidence.reason, 'incomplete_parent_review_evidence')

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: '+1',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      reviews: [
        {
          id: 30,
          body: 'Codex Review: automated suggestions follow',
          submitted_at: '2026-07-13T00:01:00Z',
          commit_id: head,
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      reviewComments: [
        {
          id: 31,
          body: 'Current review finding',
          created_at: '2026-07-13T00:01:00Z',
          commit_id: previousHead,
          pull_request_review_id: 30,
          in_reply_to_id: null,
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).state,
    'findings',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: '+1',
          created_at: '2026-07-12T23:59:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      issueComments: [matchingNoFindingsComment],
    }).acceptedSignal,
    'exact_head_no_findings',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: '+1',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: 'human-reviewer' },
        },
      ],
      issueComments: [matchingNoFindingsComment],
    }).acceptedSignal,
    'exact_head_no_findings',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: 'eyes',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
      issueComments: [matchingNoFindingsComment],
    }).acceptedSignal,
    'exact_head_no_findings',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          id: 4,
          content: '+1',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).acceptedSignal,
    'post_request_thumbs_up',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      prReactions: [
        {
          content: '+1',
          created_at: '2026-07-12T23:59:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).state,
    'pending',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      issueComments: [
        {
          body: `Codex Review: Didn't find any major issues.\n\n**Reviewed commit:** \`fedcba9876\``,
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).state,
    'pending',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      reviews: [
        {
          id: 2,
          body: 'Codex Review: automated suggestions follow',
          submitted_at: '2026-07-13T00:01:00Z',
          commit_id: head,
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).state,
    'findings',
  )

  assert.equal(
    classifyEvidence({
      ...base,
      issueComments: [
        {
          id: 3,
          body: 'You have reached your Codex usage limits for code reviews.',
          created_at: '2026-07-13T00:01:00Z',
          user: { login: DEFAULT_BOT_LOGINS[0] },
        },
      ],
    }).state,
    'unavailable',
  )

  printJson({ ok: true, tests: 18 })
}

function printHelp() {
  process.stdout.write(`Usage:\n  codex-review-gate.mjs request --pr <number> [--repo owner/name]\n  codex-review-gate.mjs status --pr <number> --request-comment-id <id> --head <full-sha> [--repo owner/name]\n  codex-review-gate.mjs self-test\n`)
}

const { command, options } = parseArgs(process.argv.slice(2))

switch (command) {
  case 'request':
    requestReview(options)
    break
  case 'status':
    reviewStatus(options)
    break
  case 'self-test':
    selfTest()
    break
  case 'help':
  case '--help':
  case undefined:
    printHelp()
    break
  default:
    fail(`Unknown command: ${command}`)
}
