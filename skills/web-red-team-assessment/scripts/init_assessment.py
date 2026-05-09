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
        description="Create an assessment ledger for an authorized web security review."
    )
    parser.add_argument("--root", default=".", help="Repository or workspace root")
    parser.add_argument("--target", required=True, help="Short target name or slug")
    parser.add_argument(
        "--base-url",
        action="append",
        default=[],
        help="In-scope base URL. Repeat for multiple URLs.",
    )
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
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")

    write_file(
        assessment_dir / "scope.md",
        f"""# Scope

- Created at: {now}
- Target: {args.target}
- Base URLs:
{base_urls}
- Authorization owner:
- Environment: local / staging / preview / production
- Test accounts and roles, redacted:
- In-scope data boundaries:
- Out-of-scope systems:
- Rate limits:
- Assessment mode: black-box report-only
- Destructive actions allowed: no, unless explicitly listed below
- Explicitly allowed destructive actions:

## Rules of Engagement

- Use only approved targets, accounts, and test data.
- Use externally observable behavior only unless the user explicitly changes scope.
- Do not modify code, configuration, data, infrastructure, branches, commits, PRs, or deployments during report-only work.
- Redact secrets, tokens, cookies, and personal data from artifacts.
- Stop before high-rate, destructive, third-party, or production-impacting tests unless explicitly approved.
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
| State-changing request protection | TBD |  | pending |  |
| Input validation and injection sinks | TBD |  | pending |  |
| XSS and client-side rendering | TBD |  | pending |  |
| SSRF, redirects, and external fetching | TBD |  | pending |  |
| File handling, reports, and storage | TBD |  | pending |  |
| Headers, CORS, CSP, and caching | TBD |  | pending |  |
| Secrets and supply chain | TBD |  | pending |  |
| Business logic and abuse resistance | TBD |  | pending |  |
| Logging, monitoring, and auditability | TBD |  | pending |  |
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
