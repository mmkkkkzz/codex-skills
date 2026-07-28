#!/usr/bin/env python3
"""Validate an As-is / To-be process-model JSON file.

The validator intentionally uses only the Python standard library so the skill
works in locked-down environments. The bundled JSON Schema is suitable for IDEs
or full jsonschema validation when that package is available, while this script
performs the semantic checks that matter most to the renderer and workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_duplicates(values: Iterable[tuple[str, str]], result: ValidationResult, scope: str) -> None:
    seen: dict[str, str] = {}
    for value, path in values:
        if not value:
            result.errors.append(f"{path}: id is missing")
            continue
        if value in seen:
            result.errors.append(f"{scope}: duplicate id '{value}' ({seen[value]} and {path})")
        else:
            seen[value] = path


def validate_model(model: Any, *, strict: bool = False) -> ValidationResult:
    r = ValidationResult()
    if not isinstance(model, dict):
        r.errors.append("Top-level JSON value must be an object")
        return r

    meta = model.get("meta")
    states = model.get("states")
    if not isinstance(meta, dict):
        r.errors.append("meta must be an object")
        meta = {}
    if not isinstance(states, list) or len(states) < 2:
        r.errors.append("states must be an array with at least two states")
        states = as_list(states)

    for key in ("title", "version", "status", "purpose", "confidentiality"):
        if not is_nonempty_string(meta.get(key)):
            r.errors.append(f"meta.{key} is required")

    scope = meta.get("scope")
    if not isinstance(scope, dict):
        r.errors.append("meta.scope must be an object")
        scope = {}
    if not is_nonempty_string(scope.get("start")):
        (r.errors if strict else r.warnings).append("meta.scope.start is missing")
    if not is_nonempty_string(scope.get("end")):
        (r.errors if strict else r.warnings).append("meta.scope.end is missing")
    if not as_list(meta.get("audience")):
        r.warnings.append("meta.audience is empty")

    # Top-level IDs are global.
    global_items: list[tuple[str, str]] = []
    for key in (
        "objectives",
        "painPoints",
        "changes",
        "kpis",
        "risks",
        "openQuestions",
        "implementation",
    ):
        for i, item in enumerate(as_list(model.get(key))):
            if isinstance(item, dict):
                global_items.append((str(item.get("id") or ""), f"{key}[{i}]"))
            else:
                r.errors.append(f"{key}[{i}] must be an object")
    for key in ("sources", "assumptions", "conflicts"):
        for i, item in enumerate(as_list(meta.get(key))):
            if isinstance(item, dict):
                global_items.append((str(item.get("id") or ""), f"meta.{key}[{i}]"))
            else:
                r.errors.append(f"meta.{key}[{i}] must be an object")
    add_duplicates(global_items, r, "top-level")

    all_node_ids: set[str] = set()
    all_edge_ids: set[str] = set()
    state_ids: list[tuple[str, str]] = []
    node_id_sources: dict[str, str] = {}
    edge_id_sources: dict[str, str] = {}
    node_records: list[tuple[dict[str, Any], str]] = []

    for si, state in enumerate(states):
        path = f"states[{si}]"
        if not isinstance(state, dict):
            r.errors.append(f"{path} must be an object")
            continue
        state_id = str(state.get("id") or "")
        state_ids.append((state_id, path))
        if not is_nonempty_string(state.get("label")):
            r.errors.append(f"{path}.label is required")

        lanes = as_list(state.get("lanes"))
        stages = as_list(state.get("stages"))
        nodes = as_list(state.get("nodes"))
        edges = as_list(state.get("edges"))
        groups = as_list(state.get("groups"))

        if not lanes:
            r.errors.append(f"{path}.lanes must not be empty")
        if not stages:
            r.errors.append(f"{path}.stages must not be empty")
        if not nodes:
            r.errors.append(f"{path}.nodes must not be empty")

        add_duplicates(
            ((str(x.get("id") or ""), f"{path}.lanes[{i}]") for i, x in enumerate(lanes) if isinstance(x, dict)),
            r,
            f"{state_id or path} lanes",
        )
        add_duplicates(
            ((str(x.get("id") or ""), f"{path}.stages[{i}]") for i, x in enumerate(stages) if isinstance(x, dict)),
            r,
            f"{state_id or path} stages",
        )
        add_duplicates(
            ((str(x.get("id") or ""), f"{path}.nodes[{i}]") for i, x in enumerate(nodes) if isinstance(x, dict)),
            r,
            f"{state_id or path} nodes",
        )
        add_duplicates(
            ((str(x.get("id") or ""), f"{path}.edges[{i}]") for i, x in enumerate(edges) if isinstance(x, dict)),
            r,
            f"{state_id or path} edges",
        )
        add_duplicates(
            ((str(x.get("id") or ""), f"{path}.groups[{i}]") for i, x in enumerate(groups) if isinstance(x, dict)),
            r,
            f"{state_id or path} groups",
        )

        lane_ids = {str(x.get("id")) for x in lanes if isinstance(x, dict) and x.get("id")}
        stage_ids = {str(x.get("id")) for x in stages if isinstance(x, dict) and x.get("id")}
        node_ids = {str(x.get("id")) for x in nodes if isinstance(x, dict) and x.get("id")}

        for ni, node in enumerate(nodes):
            npath = f"{path}.nodes[{ni}]"
            if not isinstance(node, dict):
                r.errors.append(f"{npath} must be an object")
                continue
            nid = str(node.get("id") or "")
            if nid:
                if nid in node_id_sources:
                    r.errors.append(
                        f"Node id '{nid}' must be globally unique across states "
                        f"({node_id_sources[nid]} and {npath})"
                    )
                else:
                    node_id_sources[nid] = npath
                all_node_ids.add(nid)
            node_records.append((node, npath))
            if not is_nonempty_string(node.get("label")):
                r.errors.append(f"{npath}.label is required")
            if node.get("lane") not in lane_ids:
                r.errors.append(f"{nid or npath}: unknown lane '{node.get('lane')}'")
            if node.get("stage") not in stage_ids:
                r.errors.append(f"{nid or npath}: unknown stage '{node.get('stage')}'")
            if not is_nonempty_string(node.get("type")):
                r.warnings.append(f"{nid or npath}: type is missing")
            if not is_nonempty_string(node.get("mode")):
                r.warnings.append(f"{nid or npath}: mode is missing")
            if len(str(node.get("label") or "")) > 42:
                r.warnings.append(f"{nid or npath}: label is long; move explanation to detail")

        for ei, edge in enumerate(edges):
            epath = f"{path}.edges[{ei}]"
            if not isinstance(edge, dict):
                r.errors.append(f"{epath} must be an object")
                continue
            eid = str(edge.get("id") or "")
            if eid:
                if eid in edge_id_sources:
                    r.errors.append(
                        f"Edge id '{eid}' must be globally unique across states "
                        f"({edge_id_sources[eid]} and {epath})"
                    )
                else:
                    edge_id_sources[eid] = epath
                all_edge_ids.add(eid)
            if edge.get("from") not in node_ids:
                r.errors.append(f"{eid or epath}: unknown from node '{edge.get('from')}'")
            if edge.get("to") not in node_ids:
                r.errors.append(f"{eid or epath}: unknown to node '{edge.get('to')}'")
            if not is_nonempty_string(edge.get("type")):
                r.warnings.append(f"{eid or epath}: type is missing")

        incoming = {nid: 0 for nid in node_ids}
        outgoing = {nid: 0 for nid in node_ids}
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            if edge.get("from") in outgoing:
                outgoing[str(edge.get("from"))] += 1
            if edge.get("to") in incoming:
                incoming[str(edge.get("to"))] += 1
        for node in nodes:
            if not isinstance(node, dict) or not node.get("id"):
                continue
            nid = str(node["id"])
            ntype = node.get("type")
            if ntype == "start" and incoming.get(nid, 0):
                r.warnings.append(f"{nid}: start node has incoming edge(s)")
            elif ntype != "start" and incoming.get(nid, 0) == 0:
                r.warnings.append(f"{nid}: node has no incoming edge")
            if ntype == "end" and outgoing.get(nid, 0):
                r.warnings.append(f"{nid}: end node has outgoing edge(s)")
            elif ntype != "end" and outgoing.get(nid, 0) == 0:
                r.warnings.append(f"{nid}: node has no outgoing edge")
            if ntype == "decision" and outgoing.get(nid, 0) < 2:
                r.warnings.append(f"{nid}: decision node has fewer than two outgoing paths")

        for gi, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            gid = str(group.get("id") or f"group[{gi}]")
            for lid in as_list(group.get("laneIds")):
                if lid not in lane_ids:
                    r.errors.append(f"{gid}: unknown laneId '{lid}'")
            for sid in as_list(group.get("stageIds")):
                if sid not in stage_ids:
                    r.errors.append(f"{gid}: unknown stageId '{sid}'")

        start_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("type") == "start")
        end_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("type") == "end")
        if start_count == 0:
            (r.errors if strict else r.warnings).append(f"{state_id or path}: no start node")
        if end_count == 0:
            (r.errors if strict else r.warnings).append(f"{state_id or path}: no end node")
        if len(lanes) > 6:
            r.warnings.append(f"{state_id or path}: {len(lanes)} lanes; consider overview/detail split")
        if len(stages) > 8:
            r.warnings.append(f"{state_id or path}: {len(stages)} stages; consider splitting")
        if len(nodes) > 35:
            r.warnings.append(f"{state_id or path}: {len(nodes)} nodes; consider splitting")
        if len(edges) > 45:
            r.warnings.append(f"{state_id or path}: {len(edges)} edges; consider splitting")

    add_duplicates(state_ids, r, "states")

    source_ids = {str(x.get("id")) for x in as_list(meta.get("sources")) if isinstance(x, dict) and x.get("id")}
    pain_ids = {str(x.get("id")) for x in as_list(model.get("painPoints")) if isinstance(x, dict) and x.get("id")}
    objective_ids = {str(x.get("id")) for x in as_list(model.get("objectives")) if isinstance(x, dict) and x.get("id")}
    change_ids = {str(x.get("id")) for x in as_list(model.get("changes")) if isinstance(x, dict) and x.get("id")}
    kpi_ids = {str(x.get("id")) for x in as_list(model.get("kpis")) if isinstance(x, dict) and x.get("id")}
    risk_ids = {str(x.get("id")) for x in as_list(model.get("risks")) if isinstance(x, dict) and x.get("id")}
    phase_ids = {str(x.get("id")) for x in as_list(model.get("implementation")) if isinstance(x, dict) and x.get("id")}
    state_id_set = {value for value, _ in state_ids if value}
    known_ids = source_ids | pain_ids | objective_ids | change_ids | kpi_ids | risk_ids | phase_ids | all_node_ids | all_edge_ids | state_id_set

    for node, npath in node_records:
        nid = str(node.get("id") or npath)
        for sid in as_list(node.get("sourceIds")):
            if sid not in source_ids:
                r.warnings.append(f"{nid}: unknown sourceId '{sid}'")
        for pid in as_list(node.get("painPointIds")):
            if pid not in pain_ids:
                r.errors.append(f"{nid}: unknown painPointId '{pid}'")
        for cid in as_list(node.get("changeIds")):
            if cid not in change_ids:
                r.errors.append(f"{nid}: unknown changeId '{cid}'")
        for rid in as_list(node.get("riskIds")):
            if rid not in risk_ids:
                r.errors.append(f"{nid}: unknown riskId '{rid}'")

    for key, collection in (
        ("objectives", as_list(model.get("objectives"))),
        ("changes", as_list(model.get("changes"))),
        ("kpis", as_list(model.get("kpis"))),
        ("risks", as_list(model.get("risks"))),
        ("openQuestions", as_list(model.get("openQuestions"))),
    ):
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or f"{key}[{index}]")
            for sid in as_list(item.get("sourceIds")):
                if sid not in source_ids:
                    r.warnings.append(f"{item_id}: unknown sourceId '{sid}'")

    for key in ("assumptions", "conflicts"):
        for index, item in enumerate(as_list(meta.get(key))):
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or f"meta.{key}[{index}]")
            for sid in as_list(item.get("sourceIds")):
                if sid not in source_ids:
                    r.warnings.append(f"{item_id}: unknown sourceId '{sid}'")

    pain_points = as_list(model.get("painPoints"))
    for p in pain_points:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or "painPoint")
        links = as_list(p.get("nodeIds")) + as_list(p.get("edgeIds"))
        if not links:
            r.warnings.append(f"{pid}: not linked to a node or edge")
        for nid in as_list(p.get("nodeIds")):
            if nid not in all_node_ids:
                r.errors.append(f"{pid}: unknown nodeId '{nid}'")
        for eid in as_list(p.get("edgeIds")):
            if eid not in all_edge_ids:
                r.errors.append(f"{pid}: unknown edgeId '{eid}'")
        for sid in as_list(p.get("sourceIds")):
            if sid not in source_ids:
                r.warnings.append(f"{pid}: unknown sourceId '{sid}'")

    changes = as_list(model.get("changes"))
    for c in changes:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id") or "change")
        for nid in as_list(c.get("fromNodeIds")) + as_list(c.get("toNodeIds")):
            if nid not in all_node_ids:
                r.errors.append(f"{cid}: unknown nodeId '{nid}'")
        for pid in as_list(c.get("painPointIds")):
            if pid not in pain_ids:
                r.errors.append(f"{cid}: unknown painPointId '{pid}'")
        for oid in as_list(c.get("objectiveIds")):
            if oid not in objective_ids:
                r.errors.append(f"{cid}: unknown objectiveId '{oid}'")
        for kid in as_list(c.get("kpiIds")):
            if kid not in kpi_ids:
                r.errors.append(f"{cid}: unknown kpiId '{kid}'")
        for rid in as_list(c.get("riskIds")):
            if rid not in risk_ids:
                r.errors.append(f"{cid}: unknown riskId '{rid}'")
        if not as_list(c.get("toNodeIds")):
            r.warnings.append(f"{cid}: no To-be node is linked")
        if not as_list(c.get("painPointIds")) and not as_list(c.get("objectiveIds")):
            r.warnings.append(f"{cid}: not linked to a pain point or objective")

    for kpi in as_list(model.get("kpis")):
        if not isinstance(kpi, dict):
            continue
        kid = str(kpi.get("id") or "kpi")
        for cid in as_list(kpi.get("linkedChangeIds")):
            if cid not in change_ids:
                r.errors.append(f"{kid}: unknown linkedChangeId '{cid}'")
        for field_name in ("baseline", "target", "unit", "measurement", "owner"):
            if not is_nonempty_string(kpi.get(field_name)):
                r.warnings.append(f"{kid}: {field_name} is missing")

    for risk in as_list(model.get("risks")):
        if not isinstance(risk, dict):
            continue
        rid = str(risk.get("id") or "risk")
        for related_id in as_list(risk.get("relatedIds")):
            if related_id not in known_ids:
                r.warnings.append(f"{rid}: unknown relatedId '{related_id}'")
        if not is_nonempty_string(risk.get("mitigation")):
            r.warnings.append(f"{rid}: mitigation is missing")
        if not is_nonempty_string(risk.get("owner")):
            r.warnings.append(f"{rid}: owner is missing")

    for question in as_list(model.get("openQuestions")):
        if not isinstance(question, dict):
            continue
        qid = str(question.get("id") or "question")
        for related_id in as_list(question.get("relatedIds")):
            if related_id not in known_ids:
                r.warnings.append(f"{qid}: unknown relatedId '{related_id}'")
        if question.get("status", "open") == "open" and not is_nonempty_string(question.get("owner")):
            r.warnings.append(f"{qid}: open question has no owner")

    for phase in as_list(model.get("implementation")):
        if not isinstance(phase, dict):
            continue
        phid = str(phase.get("id") or "phase")
        for cid in as_list(phase.get("changeIds")):
            if cid not in change_ids:
                r.errors.append(f"{phid}: unknown changeId '{cid}'")
        for dependency in as_list(phase.get("dependencies")):
            if dependency not in phase_ids:
                r.errors.append(f"{phid}: unknown phase dependency '{dependency}'")
        if not as_list(phase.get("exitCriteria")):
            r.warnings.append(f"{phid}: exitCriteria is empty")

    # Reciprocity checks make traceability useful in both directions.
    pain_by_id = {str(p.get("id")): p for p in pain_points if isinstance(p, dict) and p.get("id")}
    change_by_id = {str(c.get("id")): c for c in changes if isinstance(c, dict) and c.get("id")}
    for node, npath in node_records:
        nid = str(node.get("id") or npath)
        for pid in as_list(node.get("painPointIds")):
            pain = pain_by_id.get(pid)
            if pain and nid not in as_list(pain.get("nodeIds")):
                r.warnings.append(f"{nid} ↔ {pid}: pain-point link is not reciprocal")
        for cid in as_list(node.get("changeIds")):
            change = change_by_id.get(cid)
            if change and nid not in (as_list(change.get("fromNodeIds")) + as_list(change.get("toNodeIds"))):
                r.warnings.append(f"{nid} ↔ {cid}: change link is not reciprocal")

    # Source/evidence coverage and traceability metrics.
    nodes = [
        n
        for state in states
        if isinstance(state, dict)
        for n in as_list(state.get("nodes"))
        if isinstance(n, dict)
    ]
    source_coverage = (
        sum(1 for n in nodes if as_list(n.get("sourceIds"))) / len(nodes)
        if nodes
        else 0.0
    )
    pain_traceability = (
        sum(1 for p in pain_points if isinstance(p, dict) and (as_list(p.get("nodeIds")) or as_list(p.get("edgeIds"))))
        / len(pain_points)
        if pain_points
        else 0.0
    )
    change_traceability = (
        sum(1 for c in changes if isinstance(c, dict) and (as_list(c.get("painPointIds")) or as_list(c.get("objectiveIds"))))
        / len(changes)
        if changes
        else 0.0
    )
    kpi_traceability = (
        sum(1 for c in changes if isinstance(c, dict) and as_list(c.get("kpiIds"))) / len(changes)
        if changes
        else 0.0
    )
    blocking_open = sum(
        1
        for q in as_list(model.get("openQuestions"))
        if isinstance(q, dict) and q.get("blocking") is True and q.get("status", "open") == "open"
    )
    r.metrics = {
        "states": len(states),
        "nodes": len(nodes),
        "edges": sum(len(as_list(s.get("edges"))) for s in states if isinstance(s, dict)),
        "source_coverage": round(source_coverage, 4),
        "pain_traceability": round(pain_traceability, 4),
        "change_traceability": round(change_traceability, 4),
        "kpi_traceability": round(kpi_traceability, 4),
        "blocking_open_questions": blocking_open,
    }

    if source_coverage < 0.70:
        r.warnings.append(f"Source coverage is {source_coverage:.0%}; stakeholder-ready target is >= 70%")
    if pain_points and pain_traceability < 1.0:
        r.warnings.append(f"Pain-point traceability is {pain_traceability:.0%}; target is 100%")
    if changes and change_traceability < 1.0:
        r.warnings.append(f"Change traceability is {change_traceability:.0%}; target is 100%")
    if changes and kpi_traceability < 0.80:
        r.warnings.append(f"Change-to-KPI traceability is {kpi_traceability:.0%}; target is >= 80%")
    if meta.get("status") == "approved" and blocking_open:
        r.errors.append(f"Approved model has {blocking_open} open blocking question(s)")
    elif blocking_open:
        r.warnings.append(f"There are {blocking_open} open blocking question(s)")

    # Ensure as-is / to-be identities are present. Labels alone are accepted as fallback.
    state_tokens = {
        str(s.get("id", "")).lower()
        for s in states
        if isinstance(s, dict)
    } | {
        str(s.get("label", "")).lower().replace("-", "").replace(" ", "")
        for s in states
        if isinstance(s, dict)
    }
    has_asis = any(token in {"asis", "as-is", "現行", "before"} or "asis" in token for token in state_tokens)
    has_tobe = any(token in {"tobe", "to-be", "将来", "after"} or "tobe" in token for token in state_tokens)
    if not has_asis:
        r.warnings.append("No explicit As-is state detected")
    if not has_tobe:
        r.warnings.append("No explicit To-be state detected")

    return r


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def format_text(result: ValidationResult) -> str:
    lines = ["As-is / To-be model validation"]
    lines.append(f"Result: {'PASS' if result.ok else 'FAIL'}")
    if result.errors:
        lines.append(f"\nErrors ({len(result.errors)}):")
        lines.extend(f"  - {item}" for item in result.errors)
    if result.warnings:
        lines.append(f"\nWarnings ({len(result.warnings)}):")
        lines.extend(f"  - {item}" for item in result.warnings)
    lines.append("\nMetrics:")
    for key, value in result.metrics.items():
        if key.endswith("coverage") or key.endswith("traceability"):
            lines.append(f"  - {key}: {float(value):.0%}")
        else:
            lines.append(f"  - {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path, help="Path to process-model.json")
    parser.add_argument("--strict", action="store_true", help="Apply stricter semantic requirements")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return exit code 1 when warnings exist")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print machine-readable JSON")
    args = parser.parse_args(argv)

    result = validate_model(load_json(args.input), strict=args.strict)
    if args.json_output:
        print(json.dumps({"ok": result.ok, "errors": result.errors, "warnings": result.warnings, "metrics": result.metrics}, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))

    if result.errors:
        return 2
    if args.fail_on_warning and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
