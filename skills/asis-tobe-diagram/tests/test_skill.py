from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from diff_models import create_report  # noqa: E402
from extract_model import extract  # noqa: E402
from render import render  # noqa: E402
from validate import validate_model  # noqa: E402


class SkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sample = json.loads((SKILL_DIR / "assets" / "sample-model.json").read_text(encoding="utf-8"))
        cls.template = SKILL_DIR / "assets" / "template.html"

    def test_sample_passes_strict_validation(self) -> None:
        result = validate_model(copy.deepcopy(self.sample), strict=True)
        self.assertEqual([], result.errors)
        self.assertGreaterEqual(result.metrics["source_coverage"], 0.70)
        self.assertEqual(1.0, result.metrics["pain_traceability"])
        self.assertEqual(1.0, result.metrics["change_traceability"])

    def test_shared_lane_and_stage_ids_are_allowed_across_states(self) -> None:
        result = validate_model(copy.deepcopy(self.sample), strict=True)
        self.assertFalse(any("lane" in error.lower() and "duplicate" in error.lower() for error in result.errors))
        self.assertFalse(any("stage" in error.lower() and "duplicate" in error.lower() for error in result.errors))

    def test_duplicate_node_id_across_states_is_rejected(self) -> None:
        model = copy.deepcopy(self.sample)
        model["states"][1]["nodes"][0]["id"] = model["states"][0]["nodes"][0]["id"]
        result = validate_model(model, strict=True)
        self.assertTrue(any("globally unique" in error for error in result.errors))

    def test_duplicate_edge_id_across_states_is_rejected(self) -> None:
        model = copy.deepcopy(self.sample)
        model["states"][1]["edges"][0]["id"] = model["states"][0]["edges"][0]["id"]
        result = validate_model(model, strict=True)
        self.assertTrue(any("Edge id" in error and "globally unique" in error for error in result.errors))

    def test_unknown_reference_is_rejected(self) -> None:
        model = copy.deepcopy(self.sample)
        model["changes"][0]["toNodeIds"].append("T-NOT-FOUND")
        result = validate_model(model, strict=True)
        self.assertTrue(any("T-NOT-FOUND" in error for error in result.errors))

    def test_render_is_self_contained_and_extractable(self) -> None:
        html_text = render(copy.deepcopy(self.sample), self.template)
        self.assertNotIn("__MODEL_JSON__", html_text)
        self.assertNotIn("__APP_VERSION__", html_text)
        external = re.findall(r"(?:src|href)=[\"']https?://", html_text, flags=re.I)
        self.assertEqual([], external)
        extracted = extract(html_text)
        self.assertEqual(self.sample["meta"]["title"], extracted["meta"]["title"])
        self.assertEqual(len(self.sample["states"]), len(extracted["states"]))

    def test_rendered_javascript_has_valid_syntax_when_node_is_available(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        html_text = render(copy.deepcopy(self.sample), self.template)
        scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html_text, flags=re.S | re.I)
        self.assertGreaterEqual(len(scripts), 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "renderer.js"
            path.write_text(scripts[-1], encoding="utf-8")
            result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_diff_reports_modified_node(self) -> None:
        old = copy.deepcopy(self.sample)
        new = copy.deepcopy(self.sample)
        new["meta"]["version"] = "0.1.1"
        new["states"][0]["nodes"][1]["label"] = "変更後ラベル"
        report = create_report(old, new)
        self.assertIn("A-01", report["collections"]["nodes"]["modified"])
        self.assertEqual("0.1.1", report["new_version"])

    def test_cli_round_trip_and_register_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            model_path = tmp_path / "model.json"
            html_path = tmp_path / "model.html"
            extracted_path = tmp_path / "extracted.json"
            register_dir = tmp_path / "registers"
            model_path.write_text(json.dumps(self.sample, ensure_ascii=False), encoding="utf-8")

            commands = [
                [sys.executable, str(SCRIPTS_DIR / "render.py"), "--input", str(model_path), "--output", str(html_path)],
                [sys.executable, str(SCRIPTS_DIR / "extract_model.py"), "--input", str(html_path), "--output", str(extracted_path)],
                [sys.executable, str(SCRIPTS_DIR / "export_registers.py"), "--input", str(model_path), "--output-dir", str(register_dir)],
            ]
            for command in commands:
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(html_path.exists())
            self.assertTrue(extracted_path.exists())
            self.assertTrue((register_dir / "node-register.csv").exists())
            self.assertTrue((register_dir / "traceability-register.csv").exists())
            self.assertTrue((register_dir / "open-questions.csv").exists())


if __name__ == "__main__":
    unittest.main()
