#!/usr/bin/env python3
"""Create a starter process-model.json from the bundled sample or a blank skeleton."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path


def blank_model(title: str) -> dict:
    today = date.today().isoformat()
    lanes = [
        {"id": "requester", "label": "依頼者", "kind": "external"},
        {"id": "operator", "label": "業務担当", "kind": "role"},
        {"id": "system", "label": "システム / 自動化", "kind": "system"},
    ]
    stages = [
        {"id": "start", "label": "開始"},
        {"id": "process", "label": "処理"},
        {"id": "complete", "label": "完了"},
    ]
    return {
        "$schema": "./model.schema.json",
        "schemaVersion": "1.0.0",
        "meta": {
            "title": title,
            "subtitle": "",
            "version": "0.1.0",
            "status": "draft",
            "language": "ja",
            "purpose": "要記入",
            "audience": [],
            "owner": "",
            "approver": "",
            "scope": {"start": "要記入", "end": "要記入", "inScope": [], "outOfScope": []},
            "sources": [],
            "assumptions": [],
            "conflicts": [],
            "confidentiality": "internal",
            "createdAt": today,
            "updatedAt": today,
            "generatedBy": "fde-asis-tobe init_model.py",
            "changeLog": [{"version": "0.1.0", "date": today, "summary": "Initial skeleton"}],
        },
        "objectives": [],
        "states": [
            {
                "id": "asis",
                "label": "As-is",
                "summary": "要記入",
                "theme": "asis",
                "lanes": lanes,
                "stages": stages,
                "groups": [],
                "nodes": [
                    {"id": "A-START", "label": "開始", "type": "start", "lane": "requester", "stage": "start", "order": 1, "mode": "manual"},
                    {"id": "A-01", "label": "現行処理を記入する", "type": "activity", "lane": "operator", "stage": "process", "order": 1, "mode": "manual"},
                    {"id": "A-END", "label": "完了", "type": "end", "lane": "requester", "stage": "complete", "order": 1, "mode": "manual"},
                ],
                "edges": [
                    {"id": "AE-01", "from": "A-START", "to": "A-01", "type": "sequence"},
                    {"id": "AE-02", "from": "A-01", "to": "A-END", "type": "sequence"},
                ],
            },
            {
                "id": "tobe",
                "label": "To-be",
                "summary": "要記入",
                "theme": "tobe",
                "lanes": lanes,
                "stages": stages,
                "groups": [],
                "nodes": [
                    {"id": "T-START", "label": "開始", "type": "start", "lane": "requester", "stage": "start", "order": 1, "mode": "manual"},
                    {"id": "T-01", "label": "将来処理を記入する", "type": "activity", "lane": "system", "stage": "process", "order": 1, "mode": "automated"},
                    {"id": "T-END", "label": "完了", "type": "end", "lane": "requester", "stage": "complete", "order": 1, "mode": "automated"},
                ],
                "edges": [
                    {"id": "TE-01", "from": "T-START", "to": "T-01", "type": "sequence"},
                    {"id": "TE-02", "from": "T-01", "to": "T-END", "type": "sequence"},
                ],
            },
        ],
        "painPoints": [],
        "changes": [],
        "kpis": [],
        "risks": [],
        "openQuestions": [],
        "implementation": [],
        "view": {
            "layout": "stacked",
            "orientation": "left-to-right",
            "showLegend": True,
            "showDiff": True,
            "showEvidence": True,
            "page": {"size": "A3", "orientation": "landscape"},
            "theme": {
                "brandColor": "#315f86",
                "accentColor": "#d97706",
                "asisColor": "#315f86",
                "tobeColor": "#a16207",
                "logoText": "FDE Enablement",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", required=True, type=Path)
    parser.add_argument("--title", default="業務改善 As-is / To-be")
    parser.add_argument("--sample", action="store_true", help="Copy the bundled full sample instead of a blank skeleton")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"Output exists: {args.output}. Use --force to overwrite.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    skill_dir = Path(__file__).resolve().parents[1]
    if args.sample:
        shutil.copy2(skill_dir / "assets" / "sample-model.json", args.output)
    else:
        args.output.write_text(json.dumps(blank_model(args.title), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
