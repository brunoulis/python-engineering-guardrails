"""Portable Agent Skills packaging invariants (no third-party YAML parser)."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_required_frontmatter_and_name(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("\n---\n", 1)[0]
        self.assertIn("name: python-engineering-guardrails", frontmatter)
        self.assertIn("license: MIT", frontmatter)
        self.assertIn("version: \"0.1.0\"", frontmatter)
        self.assertLess(len(re.search(r"(?ms)^description: >-\n(.*?)(?=^[^ \n])", frontmatter).group(1)), 1024)

    def test_all_documented_skill_reference_paths_exist(self):
        entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("](engineering-guide.md)", entry)
        text = entry + "\n" + (ROOT / "engineering-guide.md").read_text(encoding="utf-8")
        referenced = set(re.findall(
            r"`((?:references|modes|profiles|policies|tools)/[^`]+\.(?:md|py))`", text
        ))
        referenced.update(re.findall(
            r"\]\(((?:references|modes|profiles|policies|tools)/[^)#]+\.(?:md|py))(?:#[^)]*)?\)",
            text,
        ))
        self.assertGreaterEqual(len(referenced), 10)
        for reference in referenced:
            with self.subTest(reference=reference):
                self.assertTrue((ROOT / reference).is_file(), reference)

    def test_upstream_dependency_is_external(self):
        self.assertFalse((ROOT / "databricks-core").exists())
        self.assertFalse((ROOT / "skills" / "databricks-core").exists())
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Mandatory Databricks upstream integration", text)
        self.assertIn("stop the\n   Databricks-specific portion", text)

    def test_current_serverless_cache_caveat(self):
        text = (ROOT / "references" / "databricks-runtime-and-compute.md").read_text(encoding="utf-8")
        self.assertIn("2026-10-23", text)
        self.assertIn("public preview", text.lower())
        self.assertIn("dataframe-cache", text)


if __name__ == "__main__":
    unittest.main()
