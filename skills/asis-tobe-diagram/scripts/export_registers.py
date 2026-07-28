#!/usr/bin/env python3
"""Export review registers from a process model as Excel-friendly CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from validate import as_list, load_json


def joined(value: Any) -> str:
    return "; ".join(str(x) for x in as_list(value))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def node_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for state in as_list(model.get("states")):
        if not isinstance(state, dict):
            continue
        lanes = {x.get("id"): x.get("label") for x in as_list(state.get("lanes")) if isinstance(x, dict)}
        stages = {x.get("id"): x.get("label") for x in as_list(state.get("stages")) if isinstance(x, dict)}
        for node in as_list(state.get("nodes")):
            if not isinstance(node, dict):
                continue
            output.append({
                "state": state.get("label", state.get("id", "")),
                "node_id": node.get("id", ""),
                "label": node.get("label", ""),
                "type": node.get("type", ""),
                "mode": node.get("mode", ""),
                "lane": lanes.get(node.get("lane"), node.get("lane", "")),
                "stage": stages.get(node.get("stage"), node.get("stage", "")),
                "owner": node.get("owner", ""),
                "system": node.get("system", ""),
                "status": node.get("status", ""),
                "pain_point_ids": joined(node.get("painPointIds")),
                "change_ids": joined(node.get("changeIds")),
                "risk_ids": joined(node.get("riskIds")),
                "source_ids": joined(node.get("sourceIds")),
                "detail": node.get("detail", ""),
            })
    return output


def traceability_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    pain = {x.get("id"): x for x in as_list(model.get("painPoints")) if isinstance(x, dict)}
    kpis = {x.get("id"): x for x in as_list(model.get("kpis")) if isinstance(x, dict)}
    objectives = {x.get("id"): x for x in as_list(model.get("objectives")) if isinstance(x, dict)}
    output = []
    for change in as_list(model.get("changes")):
        if not isinstance(change, dict):
            continue
        pids = as_list(change.get("painPointIds"))
        oids = as_list(change.get("objectiveIds"))
        kids = as_list(change.get("kpiIds"))
        output.append({
            "change_id": change.get("id", ""),
            "change": change.get("title", ""),
            "type": change.get("type", ""),
            "priority": change.get("priority", ""),
            "phase": change.get("phase", ""),
            "owner": change.get("owner", ""),
            "status": change.get("status", ""),
            "from_node_ids": joined(change.get("fromNodeIds")),
            "to_node_ids": joined(change.get("toNodeIds")),
            "pain_point_ids": joined(pids),
            "pain_points": "; ".join(str(pain.get(pid, {}).get("title", pid)) for pid in pids),
            "objective_ids": joined(oids),
            "objectives": "; ".join(str(objectives.get(oid, {}).get("title", oid)) for oid in oids),
            "kpi_ids": joined(kids),
            "kpis": "; ".join(str(kpis.get(kid, {}).get("name", kid)) for kid in kids),
            "risk_ids": joined(change.get("riskIds")),
            "rationale": change.get("rationale", ""),
        })
    return output


def question_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for q in as_list(model.get("openQuestions")):
        if not isinstance(q, dict):
            continue
        output.append({
            "id": q.get("id", ""),
            "question": q.get("question", ""),
            "why": q.get("why", ""),
            "blocking": q.get("blocking", False),
            "owner": q.get("owner", ""),
            "due": q.get("due", ""),
            "related_ids": joined(q.get("relatedIds")),
            "status": q.get("status", "open"),
        })
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path)
    parser.add_argument("--output-dir", "-o", required=True, type=Path)
    args = parser.parse_args(argv)
    model = load_json(args.input)

    files = {
        "node-register.csv": (
            ["state", "node_id", "label", "type", "mode", "lane", "stage", "owner", "system", "status", "pain_point_ids", "change_ids", "risk_ids", "source_ids", "detail"],
            node_rows(model),
        ),
        "traceability-register.csv": (
            ["change_id", "change", "type", "priority", "phase", "owner", "status", "from_node_ids", "to_node_ids", "pain_point_ids", "pain_points", "objective_ids", "objectives", "kpi_ids", "kpis", "risk_ids", "rationale"],
            traceability_rows(model),
        ),
        "open-questions.csv": (
            ["id", "question", "why", "blocking", "owner", "due", "related_ids", "status"],
            question_rows(model),
        ),
    }
    for filename, (fields, rows) in files.items():
        path = args.output_dir / filename
        write_csv(path, fields, rows)
        print(f"Wrote {path.resolve()} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
