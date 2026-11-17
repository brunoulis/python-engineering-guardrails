"""Offline, reproducible stdlib tests for the optional auditor."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "py_rails.py"


class AuditorCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "project"
        self.src.mkdir()
        self.upstream = self.root / "upstream"
        (self.upstream / "skills" / "databricks-core").mkdir(parents=True)
        (self.upstream / "skills" / "databricks-core" / "SKILL.md").write_text(
            "---\nname: databricks-core\ndescription: Official parent\n---\n",
            encoding="utf-8",
        )

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *arguments],
            text=True, capture_output=True, check=False,
        )

    def write(self, name: str, text: str) -> None:
        destination = self.src / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    def audit(self, profile: str = "databricks-classic", *flags: str) -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            "audit", str(self.src), "--profile", profile,
            "--upstream-root", str(self.upstream), "--format", "json", *flags,
        )

    def test_doctor_found_and_no_network(self) -> None:
        result = self.run_cli("doctor", "--upstream-root", str(self.upstream))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FOUND ON DISK", result.stdout)

    def test_missing_upstream_fail_closed(self) -> None:
        self.write("job.py", "df.collect()\n")
        result = self.run_cli(
            "audit", str(self.src), "--profile", "databricks-classic",
            "--upstream-root", str(self.root / "uninstalled"),
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("blocked", result.stderr)

    def test_python_profile_independent(self) -> None:
        self.write("api.py", "def query(cursor):\n    return cursor.fetchall()\n")
        result = self.run_cli("audit", str(self.src), "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["rule_id"], "PYR001")

    def test_driver_risks_and_low_confidence(self) -> None:
        self.write("job.py", """\
def transform(df):
    rows = df.collect()
    local = df.toPandas()
    single = df.coalesce(1)
    groups = df.groupBy('id').applyInPandas(lambda pdf: pdf, schema='id long')
    snapshot = df.cache()
    values = list(df.toLocalIterator())
    return rows, local, single, groups, snapshot, values
""")
        result = self.audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        ids = {issue["rule_id"] for issue in data["findings"]}
        self.assertEqual(ids, {"DBR001", "DBR002", "DBR003", "DBR004", "DBR005", "DBR006"})
        self.assertTrue(all(issue["confidence"] == "HEURISTIC" for issue in data["findings"]))
        self.assertEqual(data["measurements"], "NOT_MEASURED")

    def test_bounded_collect_downgrade_not_certified_safe(self) -> None:
        self.write("job.py", "rows = df.limit(50).collect()\n")
        result = self.audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        finding = json.loads(result.stdout)["findings"][0]
        self.assertEqual(finding["rule_id"], "DBR001")
        self.assertEqual(finding["severity"], "P3")

    def test_serverless_cache_is_review_not_automatic_error(self) -> None:
        self.write("job.py", """\
x = df.cache()
checkpoint = df.checkpoint()
raw = df.rdd
cache = spark.catalog.cacheTable('x')
sql = spark.sql('CACHE TABLE foo')
""")
        result = self.audit("databricks-serverless")
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual({item["rule_id"] for item in findings},
                         {"DBR004", "DBR008", "DBR009", "DBR010"})
        cache = next(item for item in findings if item["rule_id"] == "DBR004")
        self.assertEqual(cache["severity"], "P3")

    def test_ignore_venv_and_optional_tests(self) -> None:
        self.write(".venv/lib.py", "df.collect()\n")
        self.write("tests/test_job.py", "df.collect()\n")
        self.write("src/worker.py", "df.collect()\n")
        result = self.audit("databricks-classic", "--exclude-tests")
        self.assertEqual(result.returncode, 0, result.stderr)
        paths = {item["file"] for item in json.loads(result.stdout)["findings"]}
        self.assertEqual(paths, {"src/worker.py"})

    def test_baseline_gate_and_no_implicit_overwrite(self) -> None:
        self.write("job.py", "df.collect()\n")
        initial = self.audit("databricks-classic", "--fail-on", "P2")
        self.assertEqual(initial.returncode, 1)
        baseline = self.root / "baseline.json"
        result = self.audit("databricks-classic", "--write-baseline", str(baseline))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(baseline.exists())
        passed = self.audit("databricks-classic", "--baseline", str(baseline), "--fail-on", "P2")
        self.assertEqual(passed.returncode, 0, passed.stderr)
        overwrite = self.audit("databricks-classic", "--write-baseline", str(baseline))
        self.assertEqual(overwrite.returncode, 2)

    def test_syntax_error_is_incomplete_not_clean(self) -> None:
        self.write("invalid.py", "def bad(:\n  pass\n")
        result = self.audit()
        self.assertEqual(result.returncode, 2)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "INCOMPLETE")
        self.assertTrue(data["errors"])

    def test_report_sarif_and_output_path(self) -> None:
        self.write("job.py", "df.collect()\n")
        report = self.root / "report.sarif"
        result = self.run_cli(
            "audit", str(self.src), "--profile", "databricks-classic",
            "--upstream-root", str(self.upstream), "--format", "sarif", "--output", str(report),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        content = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(content["version"], "2.1.0")
        self.assertEqual(content["runs"][0]["results"][0]["ruleId"], "DBR001")
        self.assertEqual(self.run_cli(
            "audit", str(self.src), "--profile", "databricks-classic",
            "--upstream-root", str(self.upstream), "--format", "sarif", "--output", str(report),
        ).returncode, 2)


if __name__ == "__main__":
    unittest.main()
