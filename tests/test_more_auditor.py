from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "tools" / "py_rails.py"


class AdditionalRiskTests(unittest.TestCase):
    def run_scan(self, source: str, *options: str):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "job.py").write_text(source, encoding="utf-8")
            cmd = [sys.executable, str(CLI), "audit", str(root), "--format", "json", *options]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result, root

    def test_control_flow_leaving_finally(self):
        source = """def run(items):
    for item in items:
        try:
            work(item)
        finally:
            if item == 1:
                return item
            if item == 2:
                continue
            break
"""
        result, _ = self.run_scan(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual([f["line"] for f in findings if f["rule_id"] == "PYR009"], [7, 9, 10])

    def test_control_flow_local_to_cleanup(self):
        source = """def run(items):
    try:
        return work()
    finally:
        def cleanup():
            return 1
        for item in items:
            if item:
                break
            continue
        cleanup()
"""
        result, _ = self.run_scan(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(f["rule_id"] == "PYR009" for f in json.loads(result.stdout)["findings"]))

    def test_bounded_input_does_not_escape_as_runtime_measurement(self):
        result, _ = self.run_scan("with open('data') as f:\n    text = f.read()\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["measurements"], "NOT_MEASURED")

    def test_generic_whole_file_read(self):
        result, _ = self.run_scan("content = pathlib.Path('input').read_bytes()\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["rule_id"], "PYR002")

    def test_unbounded_async_tasks_are_heuristic(self):
        result, _ = self.run_scan("""\
import asyncio
async def run_all(items):
    for item in items:
        asyncio.create_task(handle(item))
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["rule_id"], "PYR003")

    def test_incomplete_scan_cannot_write_clean_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "bad.py").write_text("def broken(:\n", encoding="utf-8")
            baseline = root / "baseline.json"
            result = subprocess.run(
                [sys.executable, str(CLI), "audit", str(root),
                 "--write-baseline", str(baseline)], capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(baseline.exists())


if __name__ == "__main__":
    unittest.main()
