#!/usr/bin/env python3
"""Build a deterministic review bundle for a GitHub pull request."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PR_FIELDS = [
    "number",
    "title",
    "url",
    "baseRefName",
    "headRefName",
    "body",
    "changedFiles",
    "files",
]

SOURCE_PREFIXES = ("app/", "components/", "lib/", "supabase/")
TEST_PREFIX = "tests/"
DOC_PREFIX = "docs/"
AVAILABLE_LENSES = [
    "access-control",
    "security",
    "data-integrity",
    "correctness",
    "failure-modes",
    "api-contract",
    "performance",
    "observability-ops",
    "frontend-ux",
    "tests",
    "maintainability",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize a GitHub PR into a local review bundle."
    )
    parser.add_argument("--repo", default=".", help="Repository path. Default: current directory.")
    parser.add_argument("--pr", help="PR number or URL. Default: current branch PR.")
    parser.add_argument(
        "--out-dir",
        help="Directory to write the bundle into. Default: a fresh temporary directory.",
    )
    return parser.parse_args()


def run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{message}")
    return result.stdout


def gh_pr_view(repo: Path, pr: str | None) -> dict[str, Any]:
    cmd = ["gh", "pr", "view"]
    if pr:
        cmd.append(pr)
    cmd.extend(["--json", ",".join(PR_FIELDS)])
    return json.loads(run(cmd, repo))


def gh_pr_diff(repo: Path, pr: str | None) -> str:
    cmd = ["gh", "pr", "diff"]
    if pr:
        cmd.append(pr)
    cmd.append("--patch")
    return run(cmd, repo)


def sanitize_patch_path(path: str) -> Path:
    parts = [segment for segment in Path(path).parts if segment not in ("", ".", "..")]
    return Path(*parts).with_suffix(Path(path).suffix + ".patch")


def split_patch_sections(diff_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = defaultdict(list)
    current_path: str | None = None
    current_lines: list[str] = []

    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            flush_patch_section(sections, current_path, current_lines)
            current_path = extract_patch_path(line)
            current_lines = [line]
            continue
        if current_path is not None:
            current_lines.append(line)

    flush_patch_section(sections, current_path, current_lines)
    return {path: "".join(chunks) for path, chunks in sections.items()}


def flush_patch_section(
    sections: dict[str, list[str]], current_path: str | None, current_lines: list[str]
) -> None:
    if current_path and current_lines:
        sections[current_path].append("".join(current_lines).rstrip() + "\n")


def extract_patch_path(header: str) -> str | None:
    match = re.match(r"^diff --git a/(.+) b/(.+)$", header.rstrip())
    if not match:
        return None
    return match.group(2)


def compute_totals(files: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "files": len(files),
        "additions": sum(int(file.get("additions", 0) or 0) for file in files),
        "deletions": sum(int(file.get("deletions", 0) or 0) for file in files),
    }


def area_for_path(path: str) -> str:
    parts = Path(path).parts
    if len(parts) >= 2 and parts[0] in {"app", "lib", "tests", "docs"}:
        return "/".join(parts[:2])
    return parts[0] if parts else path


def is_ui_path(path: str) -> bool:
    return (
        path.startswith("components/")
        or path.startswith("styles/")
        or (path.startswith("app/") and not path.startswith("app/api/"))
    )


def is_api_contract_path(path: str) -> bool:
    lowered = path.lower()
    return (
        path.startswith("app/api/")
        or path.startswith("types/")
        or path == "docs/architecture/api-tree.md"
        or (
            path.startswith("lib/")
            and any(
                token in lowered
                for token in ("schema", "contract", "validation", "validator", "client", "api")
            )
        )
        or (
            path.startswith(TEST_PREFIX)
            and any(token in lowered for token in ("integration", "route.test", "api/"))
        )
    )


def is_access_control_path(path: str) -> bool:
    lowered = path.lower()
    return (
        path.startswith("app/api/")
        or path.startswith("supabase/")
        or path.endswith(("middleware.ts", "middleware.tsx"))
        or any(
            token in lowered
            for token in (
                "auth",
                "authorize",
                "permission",
                "policy",
                "policies",
                "role",
                "roles",
                "scope",
                "tenant",
                "facility",
                "organization",
                "session",
                "cookie",
                "csrf",
                "origin",
                "redirect",
                "login",
            )
        )
    )


def is_security_path(path: str) -> bool:
    lowered = path.lower()
    return (
        path.endswith(("next.config.mjs", "next.config.js"))
        or any(
            token in lowered
            for token in (
                "secret",
                "token",
                "credential",
                "crypto",
                "password",
                "webhook",
                "upload",
                "file",
                "cors",
                "ssrf",
                "sanitize",
                "redact",
                "prompt",
                "injection",
            )
        )
    )


def is_data_integrity_path(path: str) -> bool:
    lowered = path.lower()
    return (
        path.startswith("supabase/migrations/")
        or path.startswith("supabase/seed")
        or any(
            token in lowered
            for token in (
                "migration",
                "schema",
                "backfill",
                "archive",
                "canonical",
                "repository",
                "transaction",
                "rollback",
                "upsert",
                "dedupe",
                "integrity",
            )
        )
    )


def is_failure_modes_path(path: str) -> bool:
    lowered = path.lower()
    return (
        path.startswith(("app/", "components/", "lib/"))
        and not path.startswith((TEST_PREFIX, DOC_PREFIX))
        and (
            path.startswith("app/api/")
            or path.endswith("route.ts")
            or any(
                token in lowered
                for token in (
                    "error",
                    "fallback",
                    "recovery",
                    "retry",
                    "timeout",
                    "degraded",
                    "partial",
                    "audit",
                    "lockout",
                    "login",
                    "fetch",
                    "client",
                    "server",
                )
            )
        )
    )


def is_performance_path(path: str) -> bool:
    lowered = path.lower()
    return (
        (
            path.startswith(("app/", "components/", "lib/"))
            and not path.startswith(TEST_PREFIX)
        )
        or path.endswith("next.config.mjs")
        or any(token in lowered for token in ("cache", "stream", "poll", "batch"))
    )


def is_observability_ops_path(path: str) -> bool:
    lowered = path.lower()
    return (
        any(
            token in lowered
            for token in (
                "sentry",
                "logger",
                "logging",
                "log",
                "audit",
                "telemetry",
                "trace",
                "monitor",
                "metrics",
                "alert",
            )
        )
        or path.startswith("app/api/")
        or path.endswith("route.ts")
    )


def build_lens_hints(files: list[dict[str, Any]]) -> dict[str, Any]:
    changed_paths = [file["path"] for file in files]
    root_level_paths = [
        path for path in changed_paths if len(Path(path).parts) == 1
    ]
    test_paths = [
        path
        for path in changed_paths
        if path.startswith(TEST_PREFIX) and (".test." in path or ".spec." in path)
    ]
    source_paths = [
        path
        for path in changed_paths
        if path.startswith(SOURCE_PREFIXES)
        and not path.startswith(TEST_PREFIX)
        and not path.startswith(DOC_PREFIX)
    ]

    def select(predicate: Any) -> list[str]:
        return [path for path in changed_paths if predicate(path)]

    def matching_test_changed(path: str) -> bool:
        stem = Path(path).stem
        base = Path(path).name.split(".")[0]
        tokens = {token for token in re.split(r"[-_.]", stem) if len(token) >= 4}
        tokens.add(base)
        return any(any(token in test_path for token in tokens) for test_path in test_paths)

    large_source_paths = [
        file["path"]
        for file in files
        if file["path"].startswith(SOURCE_PREFIXES)
        and int(file.get("additions", 0) or 0) + int(file.get("deletions", 0) or 0) >= 120
    ]
    ui_paths = [
        path
        for path in changed_paths
        if is_ui_path(path) and not path.startswith((TEST_PREFIX, DOC_PREFIX))
    ]
    api_contract_paths = select(is_api_contract_path)

    access_control_focus = select(is_access_control_path)
    security_focus = select(is_security_path)
    data_integrity_focus = select(is_data_integrity_path)
    correctness_focus = select(
        lambda path: path.startswith(SOURCE_PREFIXES) and not path.startswith(DOC_PREFIX)
    )
    failure_modes_focus = select(is_failure_modes_path)
    maintainability_focus = sorted(
        set(
            large_source_paths
            + root_level_paths
            + select(lambda path: path.startswith(("components/", "lib/", "docs/")))
        )
    )
    performance_focus = select(is_performance_path)
    observability_ops_focus = select(is_observability_ops_path)
    tests_without_matches = [path for path in source_paths if not matching_test_changed(path)]

    access_control_recommended = bool(access_control_focus)
    security_recommended = bool(security_focus)
    data_integrity_recommended = bool(data_integrity_focus)
    failure_modes_recommended = bool(failure_modes_focus)
    maintainability_recommended = (
        len(source_paths) >= 6
        or len(large_source_paths) >= 1
        or bool(select(lambda path: path.startswith(DOC_PREFIX)))
    )
    performance_recommended = bool(performance_focus)
    observability_ops_recommended = bool(observability_ops_focus)

    lenses = {
        "access-control": {
            "recommended": access_control_recommended,
            "reason": "Auth, authorization, session, route, policy, tenant, or object-scope boundaries changed.",
            "focus_files": access_control_focus,
        },
        "security": {
            "recommended": security_recommended,
            "reason": "Secret, injection, unsafe file/network, upload, webhook, or redaction-sensitive paths changed.",
            "focus_files": security_focus,
        },
        "data-integrity": {
            "recommended": data_integrity_recommended,
            "reason": "Migration, backfill, schema, repository, transaction, or canonical data paths changed.",
            "focus_files": data_integrity_focus,
        },
        "correctness": {
            "recommended": bool(source_paths),
            "reason": "Production source files changed and core behavior may regress.",
            "focus_files": correctness_focus,
        },
        "failure-modes": {
            "recommended": failure_modes_recommended,
            "reason": "Error handling, fallback, retry, partial failure, or dependency-failure behavior may change.",
            "focus_files": failure_modes_focus,
        },
        "api-contract": {
            "recommended": bool(api_contract_paths),
            "reason": "API routes, schemas, clients, or API docs/tests changed.",
            "focus_files": api_contract_paths,
        },
        "performance": {
            "recommended": performance_recommended,
            "reason": "Runtime paths changed and request/render cost, caching, or repeated work may regress.",
            "focus_files": performance_focus,
        },
        "observability-ops": {
            "recommended": observability_ops_recommended,
            "reason": "Logging, Sentry, audit, telemetry, route, or production investigation paths changed.",
            "focus_files": observability_ops_focus,
        },
        "frontend-ux": {
            "recommended": bool(ui_paths),
            "reason": "User-facing pages, components, or styles changed.",
            "focus_files": ui_paths,
        },
        "tests": {
            "recommended": bool(source_paths or test_paths),
            "reason": "Changed production code or tests should be checked for coverage and assertion quality.",
            "focus_files": test_paths,
            "source_files_without_matching_changed_tests": tests_without_matches,
        },
        "maintainability": {
            "recommended": maintainability_recommended,
            "reason": "The diff is large or cross-cutting enough to justify a maintainability pass.",
            "focus_files": maintainability_focus,
        },
    }

    recommended_lenses = [
        lens
        for lens in AVAILABLE_LENSES
        if lenses.get(lens, {}).get("recommended")
    ]

    if not recommended_lenses and changed_paths:
        recommended_lenses = ["maintainability"]
        lenses["maintainability"]["recommended"] = True
        lenses["maintainability"]["reason"] = (
            "No code-heavy lens matched strongly, so run a lightweight maintainability pass."
        )
        lenses["maintainability"]["focus_files"] = list(changed_paths)

    recommended_focus_files = {
        path
        for lens in recommended_lenses
        for path in lenses.get(lens, {}).get("focus_files", [])
    }
    coverage_gaps = [
        path for path in changed_paths if path not in recommended_focus_files
    ]

    return {
        "recommended_lenses": recommended_lenses,
        "available_lenses": AVAILABLE_LENSES,
        "selection_notes": [
            "Launch only recommended_lenses by default.",
            "Add other lenses only when the diff is unusually cross-cutting or the user asks for exhaustive review.",
            "Before finalizing the review, make sure every changed file is covered by at least one lens or by direct coordinator review.",
            "For UI-heavy diffs, pair frontend-ux with correctness and failure-modes.",
            "For API-heavy diffs, pair api-contract with access-control, failure-modes, and tests.",
            "For destructive data changes, pair data-integrity with tests and observability-ops.",
        ],
        "coverage_gaps": coverage_gaps,
        "lenses": lenses,
    }


def build_summary(
    metadata: dict[str, Any],
    files: list[dict[str, Any]],
    totals: dict[str, int],
    lens_hints: dict[str, Any],
    bundle_dir: Path,
    generated_at: str,
) -> str:
    largest = sorted(
        files,
        key=lambda item: int(item.get("additions", 0) or 0)
        + int(item.get("deletions", 0) or 0),
        reverse=True,
    )[:10]

    directory_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "additions": 0, "deletions": 0}
    )
    for file in files:
        area = area_for_path(file["path"])
        directory_totals[area]["files"] += 1
        directory_totals[area]["additions"] += int(file.get("additions", 0) or 0)
        directory_totals[area]["deletions"] += int(file.get("deletions", 0) or 0)

    lines = [
        f"# PR #{metadata['number']}: {metadata['title']}",
        "",
        f"- URL: {metadata['url']}",
        f"- Base: `{metadata['baseRefName']}`",
        f"- Head: `{metadata['headRefName']}`",
        f"- Changed files: {totals['files']}",
        f"- Line delta: `+{totals['additions']} -{totals['deletions']}`",
        f"- Generated at: {generated_at}",
        f"- Bundle dir: `{bundle_dir}`",
        "",
        "## Largest file deltas",
        "",
    ]

    for file in largest:
        lines.append(
            f"- `{file['path']}` `+{int(file.get('additions', 0) or 0)} -{int(file.get('deletions', 0) or 0)}`"
        )

    lines.extend(["", "## Directory summary", ""])
    for area, stats in sorted(
        directory_totals.items(),
        key=lambda item: (item[1]["files"], item[1]["additions"] + item[1]["deletions"]),
        reverse=True,
    ):
        lines.append(
            f"- `{area}` {stats['files']} files `+{stats['additions']} -{stats['deletions']}`"
        )

    lines.extend(["", "## Recommended lenses", ""])
    for lens in lens_hints.get("recommended_lenses", []):
        lens_info = lens_hints.get("lenses", {}).get(lens, {})
        lines.append(f"- `{lens}`: {lens_info.get('reason', '')}")

    lines.extend(["", "## Coverage gaps after recommended lens selection", ""])
    coverage_gaps = lens_hints.get("coverage_gaps", [])
    if coverage_gaps:
        for path in coverage_gaps:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Lens hints", ""])
    for lens in lens_hints.get("available_lenses", []):
        hint = lens_hints.get("lenses", {}).get(lens, {})
        focus_files = hint.get("focus_files", [])
        recommendation = "recommended" if hint.get("recommended") else "optional"
        lines.append(f"- `{lens}`: {recommendation}, {len(focus_files)} focus files")
        reason = hint.get("reason")
        if reason:
            lines.append(f"  - reason: {reason}")
        missing_tests = hint.get("source_files_without_matching_changed_tests")
        if missing_tests is not None:
            lines.append(
                f"  - source files without matching changed tests: {len(missing_tests)}"
            )

    lines.extend(["", "## Changed files", ""])
    for file in files:
        lines.append(
            f"- `{file['path']}` `+{int(file.get('additions', 0) or 0)} -{int(file.get('deletions', 0) or 0)}`"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()

    try:
        metadata = gh_pr_view(repo, args.pr)
        diff_text = gh_pr_diff(repo, args.pr)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    generated_at = datetime.now(timezone.utc).isoformat()
    bundle_dir = (
        Path(args.out_dir).resolve()
        if args.out_dir
        else Path(tempfile.mkdtemp(prefix=f"gh-pr-review-{metadata['number']}-"))
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)
    patches_dir = bundle_dir / "patches"
    patches_dir.mkdir(parents=True, exist_ok=True)

    patch_sections = split_patch_sections(diff_text)
    files = metadata.get("files", [])
    files_json: list[dict[str, Any]] = []
    for file in files:
        path = file["path"]
        patch_path = None
        patch_text = patch_sections.get(path)
        if patch_text:
            relative_patch_path = sanitize_patch_path(path)
            absolute_patch_path = patches_dir / relative_patch_path
            absolute_patch_path.parent.mkdir(parents=True, exist_ok=True)
            absolute_patch_path.write_text(patch_text, encoding="utf-8")
            patch_path = str(Path("patches") / relative_patch_path)

        files_json.append(
            {
                "path": path,
                "additions": int(file.get("additions", 0) or 0),
                "deletions": int(file.get("deletions", 0) or 0),
                "patchPath": patch_path,
            }
        )

    totals = compute_totals(files_json)
    lens_hints = build_lens_hints(files_json)

    metadata_output = {
        **metadata,
        "generatedAt": generated_at,
        "bundleDir": str(bundle_dir),
        "totals": totals,
    }

    summary = build_summary(metadata_output, files_json, totals, lens_hints, bundle_dir, generated_at)

    (bundle_dir / "metadata.json").write_text(
        json.dumps(metadata_output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "files.json").write_text(
        json.dumps(files_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "lens-hints.json").write_text(
        json.dumps(lens_hints, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "summary.md").write_text(summary, encoding="utf-8")
    (bundle_dir / "diff.patch").write_text(diff_text, encoding="utf-8")

    print(f"bundle_dir={bundle_dir}")
    print(f"summary_file={bundle_dir / 'summary.md'}")
    print(f"diff_file={bundle_dir / 'diff.patch'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
