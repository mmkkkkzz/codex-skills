#!/usr/bin/env python3
"""Compare two process models by stable ID and write a reviewable change report."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from validate import as_list, load_json


@dataclass
class CollectionDiff:
    added: list[str]
    removed: list[str]
    modified: list[str]


def index(items: list[Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): item
        for item in items
        if isinstance(item, dict) and item.get("id")
    }


def diff_collection(old_items: list[Any], new_items: list[Any]) -> CollectionDiff:
    old = index(old_items)
    new = index(new_items)
    common = old.keys() & new.keys()
    return CollectionDiff(
        added=sorted(new.keys() - old.keys()),
        removed=sorted(old.keys() - new.keys()),
        modified=sorted(key for key in common if old[key] != new[key]),
    )


def flatten_state_items(model: dict[str, Any], key: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for state in as_list(model.get("states")):
        if not isinstance(state, dict):
            continue
        state_id = str(state.get("id") or "state")
        for item in as_list(state.get(key)):
            if not isinstance(item, dict):
                continue
            copy = json.loads(json.dumps(item))
            copy["_state"] = state_id
            # IDs are globally unique for nodes/edges; for axes use a scoped key.
            if key in {"lanes", "stages", "groups"}:
                copy["id"] = f"{state_id}/{copy.get('id', '')}"
            output.append(copy)
    return output


def field_changes(old: dict[str, Any], new: dict[str, Any], fields: list[str]) -> list[tuple[str, Any, Any]]:
    return [(field, old.get(field), new.get(field)) for field in fields if old.get(field) != new.get(field)]


def create_report(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    sections: dict[str, CollectionDiff] = {}
    for key in ("objectives", "painPoints", "changes", "kpis", "risks", "openQuestions", "implementation"):
        sections[key] = diff_collection(as_list(old.get(key)), as_list(new.get(key)))
    for key in ("lanes", "stages", "groups", "nodes", "edges"):
        sections[key] = diff_collection(flatten_state_items(old, key), flatten_state_items(new, key))

    meta_fields = ["title", "subtitle", "version", "status", "purpose", "owner", "approver", "scope", "confidentiality"]
    return {
        "old_version": old.get("meta", {}).get("version"),
        "new_version": new.get("meta", {}).get("version"),
        "meta_changes": field_changes(old.get("meta", {}), new.get("meta", {}), meta_fields),
        "collections": {key: asdict(value) for key, value in sections.items()},
    }


def md_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Process Model Change Report",
        "",
        f"**Version:** `{report.get('old_version')}` → `{report.get('new_version')}`",
        "",
        "## Summary",
        "",
        "| Collection | Added | Removed | Modified |",
        "|---|---:|---:|---:|",
    ]
    for key, value in report["collections"].items():
        lines.append(f"| {key} | {len(value['added'])} | {len(value['removed'])} | {len(value['modified'])} |")

    lines.extend(["", "## Metadata changes", ""])
    if report["meta_changes"]:
        lines.extend(["| Field | Before | After |", "|---|---|---|"])
        for field, before, after in report["meta_changes"]:
            lines.append(f"| {field} | {md_value(before)} | {md_value(after)} |")
    else:
        lines.append("No tracked metadata changes.")

    lines.extend(["", "## Element changes", ""])
    any_detail = False
    for key, value in report["collections"].items():
        if not any(value.values()):
            continue
        any_detail = True
        lines.append(f"### {key}")
        lines.append("")
        for label, field in (("Added", "added"), ("Removed", "removed"), ("Modified", "modified")):
            if value[field]:
                lines.append(f"- **{label}:** " + ", ".join(f"`{x}`" for x in value[field]))
        lines.append("")
    if not any_detail:
        lines.append("No element changes.")

    lines.extend([
        "## Review prompts",
        "",
        "- Were any stable IDs changed without a semantic reason?",
        "- Do removed As-is elements have an explicit change rationale?",
        "- Do new To-be elements link to a pain point or objective?",
        "- Were KPI, risks, assumptions, and open questions updated consistently?",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = create_report(load_json(args.old), load_json(args.new))
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.as_json else render_markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote: {args.output.resolve()}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
