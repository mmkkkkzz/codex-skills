#!/usr/bin/env python3
"""Extract the embedded process model from a generated HTML artifact."""

from __future__ import annotations

import argparse
import html
import json
from html.parser import HTMLParser
from pathlib import Path


class ModelScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.capture = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attr_map = dict(attrs)
        if attr_map.get("id") == "process-model":
            self.capture = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.capture:
            self.capture = False

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.parts.append(data)


def extract(html_text: str) -> dict:
    parser = ModelScriptParser()
    parser.feed(html_text)
    raw = html.unescape("".join(parser.parts)).strip()
    if not raw:
        raise ValueError("No <script id=\"process-model\"> block was found")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Embedded process model is not a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path)
    parser.add_argument("--output", "-o", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.output.exists() and not args.force:
        raise SystemExit(f"Output exists: {args.output}. Use --force to overwrite.")
    model = extract(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
