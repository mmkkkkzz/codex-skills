#!/usr/bin/env python3
"""Create a lightweight web security assessment workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "web-target"


def unique_dir(base: Path) -> Path:
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = Path(f"{base}-{index}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Could not find an unused directory near {base}")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an assessment ledger for an authorized local web security review."
    )
    parser.add_argument("--root", default=".", help="Repository or workspace root")
    parser.add_argument("--target", required=True, help="Short target name or slug")
    parser.add_argument(
        "--base-url",
        action="append",
        default=[],
        help="In-scope base URL. Repeat for multiple URLs.",
    )
    parser.add_argument("--source-repo", help="Primary repository path")
    parser.add_argument("--worktree", help="Dedicated assessment worktree path")
    parser.add_argument("--base-ref", help="Git ref used to create the assessment worktree")
    parser.add_argument("--install-command", default="pnpm install", help="Dependency install command")
    parser.add_argument("--dev-command", default="PORT=<free-local-port> pnpm run dev", help="Local dev server command")
    parser.add_argument("--dev-session", default="TBD", help="Dev server process or session identifier")
    parser.add_argument(
        "--out-dir",
        default="security-assessments",
        help="Directory under root where assessment artifacts are created",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    date = dt.date.today().strftime("%Y%m%d")
    target_slug = slugify(args.target)
    assessment_dir = unique_dir(root / args.out_dir / f"{date}_{target_slug}")
    evidence_dir = assessment_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    base_urls = "\n".join(f"- {url}" for url in args.base_url) or "- TBD"
    source_repo = args.source_repo or "TBD"
    worktree = args.worktree or str(root)
    base_ref = args.base_ref or "TBD"
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")

    write_file(
        assessment_dir / "scope.md",
        f"""# Scope

- Created at: {now}
- Target: {args.target}
- Base URLs:
{base_urls}
- Source repo: {source_repo}
- Assessment worktree: {worktree}
- Base ref: {base_ref}
- Local URL/port:
- Env files copied:
- Install command: {args.install_command}
- Dev server command: {args.dev_command}
- Dev server process/session: {args.dev_session}
- Authorization owner:
- Environment: local only
- Test accounts and roles, redacted:
- Credential inventory path: credentials.md
- In-scope data boundaries:
- Disposable local data/services:
- Stubbed email/SMS/payment/webhook sinks:
- Out-of-scope systems: staging, preview, production, public internet, third parties
- Request/resource budgets:
- Reset/cleanup commands:
- Assessment mode: local black-box destructive assessment
- Remediation requested now: no, defer until confirmed findings are reported
- Destructive app-level actions allowed: yes, local disposable scope only
- Explicitly allowed destructive actions:
- Explicitly prohibited non-local actions:

## Rules of Engagement

- Run setup, local server, probing, scanner/fuzzer commands, and artifact writes from the assessment worktree.
- Use only local approved targets, accounts, and disposable test data.
- Use seed-derived credentials only for local authentication and pass them only to subagents that need them.
- Use externally observable behavior only unless the user explicitly changes scope.
- Do not modify source code, configuration files, infrastructure, branches, commits, PRs, or deployments during assessment work.
- Destructive app-level actions are allowed only inside the local disposable target and must be followed by cleanup/reset notes.
- Redact secrets, tokens, cookies, and personal data from artifacts.
- Stop before any staging, preview, production, public internet, third-party, host-damaging, real-secret, phishing, malware, or persistence test.
""",
    )

    write_file(
        assessment_dir / "worktree.md",
        f"""# Worktree Isolation

- Source repo: {source_repo}
- Assessment worktree: {worktree}
- Base ref: {base_ref}
- Created at: {now}
- Local URL/port:
- Env files copied:
- Install command: {args.install_command}
- Dev server command: {args.dev_command}
- Dev server process/session: {args.dev_session}
- Reset/cleanup command:
- Remove worktree after assessment: yes / no / ask

## Setup Checklist

```bash
git status --short
git worktree list
git worktree add --detach ../<repo>-redteam-<date> HEAD
pnpm install
PORT=<free-local-port> pnpm run dev
```

## Notes

- Keep the primary checkout untouched.
- Run assessment commands from the dedicated worktree.
- Copy only local development env files needed for the disposable target.
- Use a non-default local port if another checkout is active.
- Start the dev server yourself; do not wait for the user to run it.
- Do not commit assessment artifacts, credentials, local env files, or generated destructive-test residue.
""",
    )

    write_file(
        assessment_dir / "credentials.md",
        """# Local Seed Credentials

Sensitive local assessment artifact. Do not commit.

Populate this manually from seed/fixture/demo/test-data/setup docs, or use the helper as a first pass:

```bash
python3 /path/to/web-red-team-assessment/scripts/extract_seed_credentials.py --root . --out <assessment-dir>/credentials.md
```

| Login | Password | Role | Tenant | Facility | Source | Confidence | Assigned lenses |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Handling Rules

- Use these credentials only against the approved local disposable target.
- Verify ambiguous helper output manually before assigning it to a subagent.
- Pass only the required account to each subagent.
- Do not include raw passwords, cookies, tokens, or session identifiers in final reports.
- Redact credentials from copied subagent output before merging.
""",
    )

    write_file(
        assessment_dir / "test-plan.md",
        """# Test Plan

| Lens | In scope? | Evidence path | Status | Notes |
| --- | --- | --- | --- | --- |
| Recon and route/API map | TBD |  | pending |  |
| Authentication and session | TBD |  | pending |  |
| Authorization and multi-tenant isolation | TBD |  | pending |  |
| Destructive workflow and CSRF | TBD |  | pending |  |
| Input validation, injection, fuzz, and XSS | TBD |  | pending |  |
| XSS and client-side rendering | TBD |  | pending |  |
| SSRF, redirects, and external fetching | TBD |  | pending |  |
| File handling, reports, and storage | TBD |  | pending |  |
| Headers, CORS, CSP, and caching | TBD |  | pending |  |
| Secrets and supply chain | TBD |  | pending |  |
| Business logic and abuse resistance | TBD |  | pending |  |
| Automation, fuzz, race, and local stress | TBD |  | pending |  |
| Cleanup and reset | TBD |  | pending |  |
""",
    )

    write_file(
        assessment_dir / "subagents.md",
        """# Subagent Coordination

Use this only when delegation is available, the user explicitly asked for subagents or parallel assessment, and the local-only scope gate is satisfied.

## Assigned Lenses

| Lens | Agent | Assigned credential | Route/role/tenant/surface boundary | Request/resource budget | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Surface mapper |  | none unless needed |  |  | pending |  |
| Browser controls |  | none unless needed |  |  | pending |  |
| Auth and session |  |  |  |  | pending |  |
| Authorization and tenant isolation |  |  |  |  | pending |  |
| Destructive workflow and CSRF |  |  |  |  | pending |  |
| Input handling, injection, and XSS |  |  |  |  | pending |  |
| Files, reports, and storage |  |  |  |  | pending |  |
| Business logic |  |  |  |  | pending |  |
| Automation, fuzz, and local stress |  |  |  |  | pending |  |
| Cleanup and reset coordinator |  |  |  |  | pending |  |

## Safety Stops

| Proposed check | Risk | Budget/reset requirement | Approved/blocked | Safer alternative |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Merge Notes

- Treat subagent output as leads until the coordinator verifies externally observable behavior inside scope.
- Promote only confirmed, reproducible, in-scope issues to findings.
- Keep hypotheses, blocked checks, and clean passes separate.
- Deduplicate by affected asset, actor boundary, and root behavior.
- Record request counts, state-changing actions performed, cleanup/reset status, and residual risk.
""",
    )

    write_file(
        assessment_dir / "findings.md",
        """# Findings

## Confirmed Findings

### <Severity>: <Title>

- Status: open / fixed / accepted / blocked
- Affected asset:
- Actors tested:
- Impact:
- Evidence:
- Likely root cause from observed behavior:
- Remediation recommendation:
- Regression test recommendation:
- Validation:
- Cleanup/reset performed:
- Residual risk:

## Hypotheses

| Area | Signal | Needed evidence |
| --- | --- | --- |
|  |  |  |

## Clean Passes

| Area | Evidence | Notes |
| --- | --- | --- |
|  |  |  |
""",
    )

    write_file(
        evidence_dir / "README.md",
        """# Evidence

Store redacted screenshots, HTTP transcripts, logs, and scanner summaries here.
Do not store live secrets, raw cookies, access tokens, personal data, or production data exports.
""",
    )

    print(assessment_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
