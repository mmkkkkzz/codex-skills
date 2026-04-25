#!/usr/bin/env node
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { resolve } from "node:path";

const usage = `Usage:
  run_claude_pr_review.mjs --repo <repo> --bundle-dir <dir> [options]

Options:
  --repo <dir>              Repository path for Claude Code. Required.
  --bundle-dir <dir>        Review bundle directory. Required.
  --review-aspects <args>   Arguments for /pr-review-toolkit:review-pr.
                            Default: "all parallel".
  --instruction <text>      Extra instruction for Claude. Repeatable.
  --timeout-ms <ms>         Timeout for the Claude process. Default: 1800000.
  --max-budget-usd <value>  Optional Claude Code budget limit.
  --claude-wrapper <path>   Override claude-code-task.mjs path.
  --permission-mode <mode>  Claude Code permission mode. Default: auto.
  --allowed-tools <tools>   Claude Code allowed tools for the review.
  --dry-run                 Print the command without running it.
  --help                    Show this help.

Output:
  Writes raw Claude stdout to <bundle-dir>/claude-pr-review.md.
  Writes stderr to <bundle-dir>/claude-pr-review.stderr.txt when present.
`;

const args = process.argv.slice(2);
const opts = {
  instructions: [],
  reviewAspects: "all parallel",
  timeoutMs: 30 * 60 * 1000,
  permissionMode: "auto",
  allowedTools: "Bash(git *) Bash(gh *) Glob Grep Read Task",
};

function fail(message) {
  console.error(`[run_claude_pr_review] ${message}`);
  console.error(usage);
  process.exit(2);
}

function takeValue(index, flag) {
  const value = args[index + 1];
  if (index + 1 >= args.length || value.startsWith("--")) {
    fail(`${flag} requires a value`);
  }
  return value;
}

for (let i = 0; i < args.length; i += 1) {
  const arg = args[i];
  switch (arg) {
    case "--help":
    case "-h":
      console.log(usage);
      process.exit(0);
      break;
    case "--repo":
      opts.repo = takeValue(i, arg);
      i += 1;
      break;
    case "--bundle-dir":
      opts.bundleDir = takeValue(i, arg);
      i += 1;
      break;
    case "--review-aspects":
      opts.reviewAspects = takeValue(i, arg);
      i += 1;
      break;
    case "--instruction":
      opts.instructions.push(takeValue(i, arg));
      i += 1;
      break;
    case "--timeout-ms":
      opts.timeoutMs = Number(takeValue(i, arg));
      i += 1;
      break;
    case "--max-budget-usd":
      opts.maxBudgetUsd = takeValue(i, arg);
      i += 1;
      break;
    case "--claude-wrapper":
      opts.claudeWrapper = takeValue(i, arg);
      i += 1;
      break;
    case "--permission-mode":
      opts.permissionMode = takeValue(i, arg);
      i += 1;
      break;
    case "--allowed-tools":
    case "--allowedTools":
      opts.allowedTools = takeValue(i, arg);
      i += 1;
      break;
    case "--dry-run":
      opts.dryRun = true;
      break;
    default:
      fail(`unknown option: ${arg}`);
  }
}

if (!opts.repo) fail("--repo is required");
if (!opts.bundleDir) fail("--bundle-dir is required");
if (!Number.isFinite(opts.timeoutMs) || opts.timeoutMs <= 0) {
  fail("--timeout-ms must be a positive number");
}

const repo = resolve(opts.repo);
const bundleDir = resolve(opts.bundleDir);
const codexHome = process.env.CODEX_HOME || `${homedir()}/.codex`;
const wrapper =
  opts.claudeWrapper ||
  `${codexHome}/skills/claude-code/scripts/claude-code-task.mjs`;

if (!existsSync(wrapper)) {
  fail(`claude-code wrapper not found: ${wrapper}`);
}

const baseInstruction = [
  "Run Claude Code's pr-review-toolkit review for this PR.",
  "Return the review result only. Do not edit files.",
  "Lead with concrete findings ordered by severity. Use file:line anchors when available.",
  "If there are no findings, say so explicitly and include residual risk.",
  "Codex will merge this raw output with other lens review outputs and quote this full raw report verbatim in the final review.",
].join(" ");

const prompt = [baseInstruction, ...opts.instructions].join("\n\n");
const command = [
  wrapper,
  "--cwd",
  repo,
  "--review-pr",
  "--review-aspects",
  opts.reviewAspects,
  "--timeout-ms",
  String(opts.timeoutMs),
  "--permission-mode",
  opts.permissionMode,
];
if (opts.allowedTools) {
  command.push("--allowed-tools", opts.allowedTools);
}
if (opts.maxBudgetUsd) {
  command.push("--max-budget-usd", opts.maxBudgetUsd);
}
command.push("--", prompt);

if (opts.dryRun) {
  console.log(
    JSON.stringify(
      {
        cwd: repo,
        command: ["node", ...command.slice(0, -1), "<prompt>"],
        output: `${bundleDir}/claude-pr-review.md`,
      },
      null,
      2
    )
  );
  process.exit(0);
}

await mkdir(bundleDir, { recursive: true });

const child = spawn("node", command, {
  cwd: repo,
  env: process.env,
  stdio: ["ignore", "pipe", "pipe"],
});

let stdout = "";
let stderr = "";

child.stdout.setEncoding("utf8");
child.stderr.setEncoding("utf8");
child.stdout.on("data", (chunk) => {
  stdout += chunk;
  process.stdout.write(chunk);
});
child.stderr.on("data", (chunk) => {
  stderr += chunk;
  process.stderr.write(chunk);
});

const exitCode = await new Promise((resolveExit) => {
  child.on("error", (error) => {
    stderr += `[run_claude_pr_review] failed to start: ${error.message}\n`;
    resolveExit(127);
  });
  child.on("close", (code, signal) => {
    if (signal) {
      stderr += `[run_claude_pr_review] terminated by ${signal}\n`;
      resolveExit(128);
      return;
    }
    resolveExit(code ?? 1);
  });
});

const stdoutPath = `${bundleDir}/claude-pr-review.md`;
const stderrPath = `${bundleDir}/claude-pr-review.stderr.txt`;
await writeFile(stdoutPath, stdout || "", "utf8");
if (stderr) {
  await writeFile(stderrPath, stderr, "utf8");
}

if (exitCode !== 0) {
  console.error(`[run_claude_pr_review] Claude review failed with exit code ${exitCode}`);
}
process.exit(exitCode);
