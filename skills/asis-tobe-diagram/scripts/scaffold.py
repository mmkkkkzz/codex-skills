#!/usr/bin/env python3
"""Create a maintainable As-is / To-be work package.

The output contains a semantic JSON model, the bundled schema, a decision log,
an open-question register, and a source inventory. Rendering remains a separate
step so reviewers can validate the model before producing HTML.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path

from init_model import blank_model


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def decision_log(title: str, version: str, today: str) -> str:
    return f"""# Decision Log — {title}

## Document control

| Field | Value |
|---|---|
| Model version | {version} |
| Created | {today} |
| Status | Draft |
| Owner | TBD |
| Approver | TBD |

## Scope decisions

| ID | Date | Decision | Rationale / evidence | Alternatives considered | Owner | Status |
|---|---|---|---|---|---|---|
| D-001 | {today} | Define the start and end conditions | TBD | TBD | TBD | Open |

## Modeling decisions

Record choices that materially affect interpretation, such as diagram level,
state decomposition, lane ownership, system boundaries, automation mode, and
whether a detail is represented as a sub-process rather than expanded inline.

| ID | Date | Decision | Rationale / evidence | Impacted IDs | Owner | Status |
|---|---|---|---|---|---|---|
| D-101 | {today} | Use JSON as the source of truth and regenerate HTML | Enables deterministic maintenance and review | All | Model owner | Accepted |

## Assumptions adopted for the draft

Do not duplicate assumptions without linking them to `meta.assumptions` in the
model. Note here only assumptions that changed a design decision.

| Assumption ID | Consequence if false | Validation owner | Due | Status |
|---|---|---|---|---|
| — | — | — | — | — |

## Rejected options

| ID | Option | Why rejected | Reconsider when |
|---|---|---|---|
| R-001 | TBD | TBD | TBD |
"""


def open_questions(title: str) -> str:
    return f"""# Open Questions — {title}

Keep this file synchronized with `openQuestions` in `process-model.json`.
Questions should be consolidated, assigned, and ordered by decision impact.

## 1. Blocking — prevents business or design agreement

| ID | Question | Why it matters | Owner | Due | Related IDs | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## 2. Required before requirements sign-off

| ID | Question | Why it matters | Owner | Due | Related IDs | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## 3. Required before implementation / operations

| ID | Question | Why it matters | Owner | Due | Related IDs | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## 4. Non-blocking precision improvements

| ID | Question | Why it matters | Owner | Due | Related IDs | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
"""


def source_inventory(title: str) -> str:
    return f"""# Source Inventory — {title}

Register every source before extracting facts. Do not treat an unverified
hypothesis as an observed fact.

| Source ID | Type | Title / person | Date | Location | Confidence | Extracted facts | Restrictions |
|---|---|---|---|---|---|---|---|
| S-001 | document / interview / image / system / observation / assumption | TBD | TBD | TBD | high / medium / low | TBD | Internal |

## Conflict log

| Conflict ID | Sources | Conflicting statements | Working interpretation | Resolution owner | Status |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", "-o", required=True, type=Path)
    parser.add_argument("--title", default="業務改善 As-is / To-be")
    parser.add_argument("--sample", action="store_true", help="Use the bundled sample model")
    parser.add_argument("--force", action="store_true", help="Overwrite files created by this script")
    args = parser.parse_args(argv)

    out = args.output_dir.resolve()
    skill_dir = Path(__file__).resolve().parents[1]
    managed = [
        out / "process-model.json",
        out / "model.schema.json",
        out / "decision-log.md",
        out / "open-questions.md",
        out / "source-inventory.md",
    ]
    existing = [p for p in managed if p.exists()]
    if existing and not args.force:
        paths = "\n  - ".join(str(p) for p in existing)
        raise SystemExit(f"Refusing to overwrite existing files:\n  - {paths}\nUse --force to replace them.")

    out.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    if args.sample:
        model = json.loads((skill_dir / "assets" / "sample-model.json").read_text(encoding="utf-8"))
        model["meta"]["title"] = args.title
        model["meta"]["updatedAt"] = today
    else:
        model = blank_model(args.title)

    write_text(out / "process-model.json", json.dumps(model, ensure_ascii=False, indent=2))
    shutil.copy2(skill_dir / "assets" / "model.schema.json", out / "model.schema.json")
    write_text(out / "decision-log.md", decision_log(args.title, str(model["meta"].get("version", "0.1.0")), today))
    write_text(out / "open-questions.md", open_questions(args.title))
    write_text(out / "source-inventory.md", source_inventory(args.title))

    print(f"Created work package: {out}")
    for path in managed:
        print(f"  - {path.name}")
    print("Next: populate process-model.json, run validate.py --strict, then render.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
