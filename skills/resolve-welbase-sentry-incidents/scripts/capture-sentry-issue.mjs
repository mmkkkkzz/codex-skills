#!/usr/bin/env node

import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import process from 'node:process'

const SAFE_TAGS = new Set(['environment', 'level', 'release', 'transaction'])
const ISSUE_PATTERN = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+#[A-Za-z0-9_-]+$/

function fail(message, exitCode = 1) {
  process.stderr.write(`${message}\n`)
  process.exit(exitCode)
}

function parseArgs(argv) {
  const [commandOrFlag, ...rest] = argv
  if (commandOrFlag === 'self-test' || commandOrFlag === 'help' || commandOrFlag === '--help') {
    return { command: commandOrFlag, options: {} }
  }

  const tokens = commandOrFlag ? [commandOrFlag, ...rest] : []
  const options = {}
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index]
    if (!token.startsWith('--')) fail(`Unexpected argument: ${token}`)
    const value = tokens[index + 1]
    if (!value || value.startsWith('--')) fail(`Missing value for ${token}`)
    options[token.slice(2)] = value
    index += 1
  }
  return { command: 'capture', options }
}

function normalizeIssue(value) {
  if (!ISSUE_PATTERN.test(value || '')) fail('--issue must use org/project#ISSUE-ID')
  return value
}

function normalizeOutputDirectory(value) {
  if (!value) fail('--out-dir is required')
  return path.resolve(value)
}

function normalizeTags(tags) {
  if (!Array.isArray(tags)) return {}

  return Object.fromEntries(
    tags
      .map((tag) => {
        if (Array.isArray(tag)) return [tag[0], tag[1]]
        return [tag?.key, tag?.value]
      })
      .filter(([key, value]) => SAFE_TAGS.has(key) && typeof value === 'string'),
  )
}

function sanitizeIssue(raw) {
  const issue = raw?.data && !Array.isArray(raw.data) ? raw.data : raw
  const event = issue?.event && typeof issue.event === 'object' ? issue.event : {}

  return {
    id: issue?.id ?? null,
    shortId: issue?.shortId ?? null,
    culprit: issue?.culprit ?? null,
    count: issue?.count ?? null,
    userCount: issue?.userCount ?? null,
    firstSeen: issue?.firstSeen ?? null,
    lastSeen: issue?.lastSeen ?? null,
    level: issue?.level ?? null,
    status: issue?.status ?? null,
    priority: issue?.priority ?? null,
    substatus: issue?.substatus ?? null,
    isUnhandled: issue?.isUnhandled ?? null,
    permalink: issue?.permalink ?? null,
    event: {
      eventId: event.eventID ?? event.id ?? null,
      dateCreated: event.dateCreated ?? null,
      platform: event.platform ?? null,
      type: event.type ?? null,
      tags: normalizeTags(event.tags),
    },
  }
}

function writeProtectedEvidence(outputDirectory, shortId, rawJson) {
  mkdirSync(outputDirectory, { recursive: true, mode: 0o700 })
  chmodSync(outputDirectory, 0o700)
  const fileName = `${String(shortId || 'issue').replaceAll(/[^A-Za-z0-9_-]/g, '_')}.json`
  const rawPath = path.join(outputDirectory, fileName)
  writeFileSync(rawPath, `${JSON.stringify(rawJson, null, 2)}\n`, { mode: 0o600 })
  chmodSync(rawPath, 0o600)
  return rawPath
}

function capture(options) {
  const issue = normalizeIssue(options.issue)
  const outputDirectory = normalizeOutputDirectory(options['out-dir'])
  const result = spawnSync(
    'sentry',
    [
      'issue',
      'view',
      issue,
      '--fresh',
      '--spans',
      'all',
      '--json',
      '--fields',
      'id,shortId,title,culprit,count,userCount,firstSeen,lastSeen,level,status,priority,substatus,isUnhandled,permalink,event,replayIds,trace',
    ],
    { encoding: 'utf8', maxBuffer: 100 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] },
  )

  if (result.error) fail(`Unable to run sentry: ${result.error.message}`)
  if (result.status !== 0) fail(result.stderr.trim() || 'sentry issue view failed')

  let raw
  try {
    raw = JSON.parse(result.stdout)
  } catch (error) {
    fail(`sentry returned invalid JSON: ${error.message}`)
  }

  const sanitized = sanitizeIssue(raw)
  const rawPath = writeProtectedEvidence(outputDirectory, sanitized.shortId, raw)
  process.stdout.write(`${JSON.stringify({ rawPath, mode: '0600', sanitized }, null, 2)}\n`)
}

function selfTest() {
  const root = mkdtempSync(path.join(tmpdir(), 'capture-sentry-issue-'))
  try {
    const raw = {
      id: '1',
      shortId: 'WELBASE-X',
      title: 'secret title',
      culprit: '/api/test',
      event: {
        eventID: 'event-1',
        message: 'must not escape',
        tags: [
          { key: 'environment', value: 'production' },
          { key: 'secret', value: 'must not escape' },
        ],
      },
      replayIds: ['secret-replay'],
    }
    const sanitized = sanitizeIssue(raw)
    assert.equal(sanitized.event.tags.environment, 'production')
    assert.equal('secret' in sanitized.event.tags, false)
    assert.equal('title' in sanitized, false)
    assert.equal('message' in sanitized.event, false)

    const rawPath = writeProtectedEvidence(root, raw.shortId, raw)
    assert.equal(statSync(root).mode & 0o777, 0o700)
    assert.equal(statSync(rawPath).mode & 0o777, 0o600)
    assert.equal(JSON.parse(readFileSync(rawPath, 'utf8')).replayIds[0], 'secret-replay')
    process.stdout.write(`${JSON.stringify({ ok: true, tests: 7 })}\n`)
  } finally {
    rmSync(root, { recursive: true, force: true })
  }
}

function printHelp() {
  process.stdout.write(`Usage:\n  capture-sentry-issue.mjs --issue org/project#ISSUE-ID --out-dir <directory>\n  capture-sentry-issue.mjs self-test\n`)
}

const { command, options } = parseArgs(process.argv.slice(2))

switch (command) {
  case 'capture':
    capture(options)
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
