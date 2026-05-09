#!/usr/bin/env python3
"""Extract likely local seed login credentials from repository seed/fixture files."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".next",
    ".turbo",
    "coverage",
    "dist",
    "node_modules",
    "playwright-report",
    "test-results",
}
ALLOWED_SUFFIXES = {
    ".cjs",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".sql",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
SEED_NAME_RE = re.compile(
    r"(seed|fixture|factory|sample|demo|test-data|testdata|e2e|mock)",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+")
USERNAME_RE = re.compile(
    r"\b(?:username|user_name|login|email)\b\s*[:=]\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
PASSWORD_RE = re.compile(
    r"\b(?:password|pass|plain_password|raw_password|initial_password)\b\s*[:=]\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
HASH_RE = re.compile(r"(password_hash|encrypted_password|hashed_password)", re.IGNORECASE)
ROLE_RE = re.compile(r"\b(?:role|user_role|account_role)\b\s*[:=]\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
TENANT_RE = re.compile(r"\b(?:tenant|tenant_id|organization|organization_id|org_id)\b\s*[:=]\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
FACILITY_RE = re.compile(r"\b(?:facility|facility_id|office|office_id)\b\s*[:=]\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
SQL_INSERT_RE = re.compile(r"\((?P<fields>[^)]+)\)\s*values\s*\((?P<values>[^;]+)\)", re.IGNORECASE)
SQL_VALUE_RE = re.compile(r"'([^']*)'|\"([^\"]*)\"|([^,\s)]+)")


@dataclass(frozen=True)
class Credential:
    source: str
    line: int
    login: str
    password: str | None
    role: str | None
    tenant: str | None
    facility: str | None
    confidence: str


def iter_candidate_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if SEED_NAME_RE.search(str(relative)):
            yield path


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def nearest(pattern: re.Pattern[str], chunk: str) -> str | None:
    match = pattern.search(chunk)
    return match.group(1) if match else None


def clean_login(value: str) -> str:
    return value.strip().strip("'\"`")


def line_at(text: str, index: int) -> str:
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    if end == -1:
        end = len(text)
    return text[start:end]


def split_sql_values(value_text: str) -> list[str]:
    values: list[str] = []
    for match in SQL_VALUE_RE.finditer(value_text):
        values.append(next(group for group in match.groups() if group is not None).strip())
    return values


def sql_context(line: str, login: str) -> dict[str, str]:
    match = SQL_INSERT_RE.search(line)
    if not match:
        return {}
    fields = [field.strip().strip("\"`'").lower() for field in match.group("fields").split(",")]
    values = split_sql_values(match.group("values"))
    if len(fields) != len(values):
        return {}
    mapping = dict(zip(fields, values))
    if login not in {mapping.get("email"), mapping.get("username"), mapping.get("login")}:
        return {}
    return mapping


def extract_from_file(root: Path, path: Path, context_chars: int) -> list[Credential]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")

    credentials: list[Credential] = []
    seen: set[tuple[str, int]] = set()
    relative = str(path.relative_to(root))

    matches = list(EMAIL_RE.finditer(text)) + list(USERNAME_RE.finditer(text))
    matches.sort(key=lambda match: match.start())

    for match in matches:
        login = clean_login(match.group(1) if match.lastindex else match.group(0))
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)
        chunk = text[start:end]
        sql = sql_context(line_at(text, match.start()), login)
        chunk_before_login = text[max(0, match.start() - 80) : match.start()]
        password = None if HASH_RE.search(chunk_before_login) else sql.get("password") or nearest(PASSWORD_RE, chunk)
        role = sql.get("role") or sql.get("user_role") or nearest(ROLE_RE, chunk)
        tenant = sql.get("tenant") or sql.get("tenant_id") or sql.get("organization_id") or nearest(TENANT_RE, chunk)
        facility = sql.get("facility") or sql.get("facility_id") or nearest(FACILITY_RE, chunk)
        line = line_number(text, match.start())
        key = (login, line)
        if key in seen:
            continue
        seen.add(key)
        confidence = "high" if password else "login-only"
        credentials.append(
            Credential(
                source=relative,
                line=line,
                login=login,
                password=password,
                role=role,
                tenant=tenant,
                facility=facility,
                confidence=confidence,
            )
        )

    return credentials


def render_markdown(credentials: list[Credential]) -> str:
    lines = [
        "# Local Seed Credentials",
        "",
        "Sensitive local assessment artifact. Do not commit. Pass only the required account to each subagent, and instruct subagents not to echo passwords or tokens.",
        "",
        "| Login | Password | Role | Tenant | Facility | Source | Confidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in credentials:
        password = item.password if item.password is not None else ""
        lines.append(
            f"| `{item.login}` | `{password}` | {item.role or ''} | {item.tenant or ''} | {item.facility or ''} | `{item.source}:{item.line}` | {item.confidence} |"
        )
    if not credentials:
        lines.extend(["|  |  |  |  |  |  | no candidates found |"])
    lines.extend(
        [
            "",
            "## Handling Rules",
            "",
            "- Use these credentials only against the approved local disposable target.",
            "- Do not include raw passwords, cookies, tokens, or session identifiers in final reports.",
            "- If a credential is login-only, verify the local seed/reset docs before assigning it to a subagent.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract likely local seed login credentials from seed/fixture files."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--out", help="Write markdown output to this path")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--context-chars", type=int, default=500)
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    credentials: list[Credential] = []
    for path in iter_candidate_files(root):
        credentials.extend(extract_from_file(root, path, args.context_chars))

    credentials.sort(key=lambda item: (item.source, item.line, item.login))
    if args.format == "json":
        output = json.dumps([asdict(item) for item in credentials], ensure_ascii=False, indent=2) + "\n"
    else:
        output = render_markdown(credentials)

    if args.out:
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
