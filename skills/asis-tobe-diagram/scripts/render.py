#!/usr/bin/env python3
"""Render a self-contained As-is / To-be HTML report from process-model JSON."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from validate import load_json, validate_model

APP_VERSION = "1.0.0"


def merge_theme(model: dict, theme_path: Path | None) -> dict:
    if theme_path is None:
        return model
    theme = load_json(theme_path)
    if not isinstance(theme, dict):
        raise SystemExit(f"Theme file must contain a JSON object: {theme_path}")
    result = json.loads(json.dumps(model))
    result.setdefault("view", {}).setdefault("theme", {}).update(theme)
    return result


def render(model: dict, template_path: Path) -> str:
    try:
        template = template_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"Template not found: {template_path}") from exc

    # Avoid ending the JSON script tag if user-provided text contains </script>.
    model_json = json.dumps(model, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    if "__MODEL_JSON__" not in template:
        raise SystemExit(f"Template placeholder __MODEL_JSON__ not found in {template_path}")
    return template.replace("__MODEL_JSON__", model_json).replace("__APP_VERSION__", APP_VERSION)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path, help="Path to process-model.json")
    parser.add_argument("--output", "-o", required=True, type=Path, help="Output HTML path")
    parser.add_argument("--theme", type=Path, help="Optional JSON theme override")
    parser.add_argument("--template", type=Path, help="Optional custom template.html")
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open output in the default browser")
    parser.add_argument("--allow-errors", action="store_true", help="Render even when semantic validation has errors")
    args = parser.parse_args(argv)

    skill_dir = Path(__file__).resolve().parents[1]
    template_path = args.template or (skill_dir / "assets" / "template.html")
    model = merge_theme(load_json(args.input), args.theme)
    validation = validate_model(model, strict=False)

    if validation.errors and not args.allow_errors:
        print("Refusing to render because validation errors were found:", file=sys.stderr)
        for item in validation.errors:
            print(f"  - {item}", file=sys.stderr)
        print("Run validate.py for the full report, or pass --allow-errors for diagnostic rendering.", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(model, template_path), encoding="utf-8")
    print(f"Rendered: {args.output.resolve()}")
    if validation.warnings:
        print(f"Warnings: {len(validation.warnings)} (run validate.py for details)")
    if args.open_browser:
        webbrowser.open(args.output.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
