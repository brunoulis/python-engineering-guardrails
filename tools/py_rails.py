#!/usr/bin/env python3
"""Read-only Python AST triage for Python Engineering Guardrails v0.1.0.

Python stdlib only. No import of target files, network, Azure calls or rewriting.
This scanner finds *possible* patterns; it cannot measure peak memory or infer
Spark DataFrame types. Databricks profiles require an installed official skill.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import tokenize
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

VERSION = "0.1.0"
DATABRICKS_PROFILES = {"databricks-classic", "databricks-serverless", "databricks-streaming"}
PROFILES = (
    "python-general", "api-service", "async-io", "batch-etl",
    "data-science", "library-sdk", *sorted(DATABRICKS_PROFILES),
)
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".ruff_cache",
    ".pytest_cache", ".tox", ".nox", "node_modules", "dist", "build", ".next",
    ".ipynb_checkpoints", "site-packages", ".databricks",
}
LEVELS = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
BASELINE_SCHEMA = 1


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    memory_domain: str
    message: str
    recommendation: str


RULES: dict[str, Rule] = {
    "PYR001": Rule("PYR001", "P3", "Python process", "fetchall() materializes an entire result set", "Check result size; use bounded fetchmany()/pagination/streaming when appropriate."),
    "PYR002": Rule("PYR002", "P3", "Python process", "Whole-file read may allocate a large buffer", "Check file sizes; consider chunked/streamed processing without buffering the entire output."),
    "PYR003": Rule("PYR003", "P3", "Python process", "create_task() inside a loop may create unbounded in-flight work", "Bound both submitted tasks and active work; confirm loop is already bounded before changing."),
    "PYR004": Rule("PYR004", "P3", "Audit coverage", "PySpark code scanned with a non-Databricks profile; Spark rules did not run", "Rerun with --profile databricks-classic (or serverless/streaming)."),
    "PYR005": Rule("PYR005", "P2", "Side effects", "Outbound write or explicit production target", "Confirm idempotency, authorization and a dry-run/non-prod path; keep side effects out of transformation functions."),
    "PYR006": Rule("PYR006", "P3", "Maintainability", "Function body is only 'pass'", "Remove the dead stub or implement it; callers may silently do nothing."),
    "PYR007": Rule("PYR007", "P3", "Maintainability", "Identical zero-argument call repeated in the same block", "Confirm the repeat is intended; repeated pipeline steps redo work or write twice."),
    "PYR008": Rule("PYR008", "P3", "Python process", "Growing a list inside a while loop may accumulate without a bound", "Bound the loop and the accumulated size, or process/write per chunk."),
    "DBR001": Rule("DBR001", "P2", "Spark driver", "collect() may materialize a distributed result on the driver", "Prove row/byte budget; favor distributed transforms and writes over unbounded collection."),
    "DBR002": Rule("DBR002", "P2", "Spark driver / Python process", "DataFrame-to-pandas conversion may create a large local dataset", "Prove result size; prefer distributed transformations or bounded data when needed."),
    "DBR003": Rule("DBR003", "P2", "Spark executor / shuffle", "Single output partition can create an oversized task", "Avoid forcing one partition unless workload and correctness requirements justify it."),
    "DBR004": Rule("DBR004", "P3", "Spark cache / storage", "cache()/persist() adds reuse and lifecycle trade-offs", "Verify repeated reuse, data freshness, storage costs and versioned cache semantics; plan release/cleanup."),
    "DBR005": Rule("DBR005", "P2", "Python worker / shuffle", "Grouped Pandas/Arrow code may materialize very large groups", "Inspect maximum group size and skew; compare native Spark expressions and supported iterator APIs."),
    "DBR006": Rule("DBR006", "P2", "Spark driver", "list(toLocalIterator()) defeats incremental iteration", "Consume incrementally with bounded partitions or keep computation distributed."),
    "DBR007": Rule("DBR007", "P3", "Spark driver", "toLocalIterator() still requires the largest partition to fit in memory", "Inspect partition-size distribution and consume rows incrementally; avoid eager wrapping."),
    "DBR008": Rule("DBR008", "P2", "Databricks serverless compatibility", "RDD or SparkContext access may be unsupported on serverless", "Consult the official installed Databricks skills and versioned serverless API support."),
    "DBR009": Rule("DBR009", "P2", "Databricks serverless compatibility", "checkpoint() may be unsupported on serverless compute", "Verify current serverless feature support; avoid applying classic compute advice unchanged."),
    "DBR010": Rule("DBR010", "P2", "Databricks serverless compatibility", "SQL/catalog cache operation may be unsupported on serverless", "Check current official support; DataFrame caching preview is a distinct feature."),
    "DBR011": Rule("DBR011", "P3", "Spark execution", "Repeated Spark actions inside a loop may trigger extra distributed jobs", "Check iteration bounds and query plan; prefer one appropriate action when semantics allow."),
    "DBR012": Rule("DBR012", "P2", "Spark driver", "createDataFrame() from driver-side Python data", "Prove the row budget; read from storage or build the frame with Spark expressions instead of a Python list."),
}
PROD_VALUES = {"prod", "production", "prd"}


@dataclass
class Finding:
    rule_id: str
    severity: str
    confidence: str
    memory_domain: str
    file: str
    line: int
    column: int
    message: str
    recommendation: str
    snippet: str
    fingerprint: str
    baseline: bool = False


def _fingerprint(path: str, rule_id: str, snippet: str) -> str:
    normalized = " ".join(snippet.strip().split())
    return hashlib.sha256(f"{path}\n{rule_id}\n{normalized}".encode("utf-8")).hexdigest()[:24]


def _method_name(node: ast.AST) -> str | None:
    return node.func.attr if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) else None


def _integer_constant(node: ast.AST) -> int | None:
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    return None


def _inside_loop(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    current = parents.get(id(node))
    while current is not None:
        if isinstance(current, (ast.For, ast.AsyncFor, ast.While)):
            return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return False
        current = parents.get(id(current))
    return False


def _inside_while(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    current = parents.get(id(node))
    while current is not None:
        if isinstance(current, ast.While):
            return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return False
        current = parents.get(id(current))
    return False


class RiskVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str, source: str, profile: str, tree: ast.AST):
        self.path = relative_path
        self.lines = source.splitlines()
        self.profile = profile
        self.is_databricks = profile in DATABRICKS_PROFILES
        self.findings: list[Finding] = []
        self.spark_noted = False
        self.parents = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }

    def add(self, rule_id: str, node: ast.AST, severity: str | None = None) -> None:
        rule = RULES[rule_id]
        lineno = getattr(node, "lineno", 1)
        col = getattr(node, "col_offset", 0)
        snippet = self.lines[lineno - 1].strip() if 0 < lineno <= len(self.lines) else ""
        self.findings.append(Finding(
            rule_id=rule_id,
            severity=severity or rule.severity,
            confidence="HEURISTIC",
            memory_domain=rule.memory_domain,
            file=self.path,
            line=lineno,
            column=col + 1,
            message=rule.message,
            recommendation=rule.recommendation,
            snippet=snippet[:250],
            fingerprint=_fingerprint(self.path, rule_id, snippet),
        ))

    def _note_spark(self, node: ast.AST, module: str | None) -> None:
        if not self.is_databricks and not self.spark_noted and (module or "").split(".")[0] == "pyspark":
            self.spark_noted = True
            self.add("PYR004", node)

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self._note_spark(node, alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        self._note_spark(node, node.module)

    def _repeated_calls(self, body: list[ast.stmt]) -> None:
        seen: set[str] = set()
        for stmt in body:
            if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                    and not stmt.value.args and not stmt.value.keywords):
                key = ast.dump(stmt.value)
                if key in seen:
                    self.add("PYR007", stmt)
                seen.add(key)

    def visit_Module(self, node: ast.Module) -> Any:
        self._repeated_calls(node.body)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        if len(body) == 1 and isinstance(body[0], ast.Pass) and not node.decorator_list:
            self.add("PYR006", node)
        self._repeated_calls(node.body)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if self.profile == "databricks-serverless":
            if node.attr == "rdd":
                self.add("DBR008", node)
            elif node.attr == "sparkContext" and isinstance(node.value, ast.Name) and node.value.id == "spark":
                self.add("DBR008", node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        name = _method_name(node)
        if name == "fetchall" and not node.args and not node.keywords:
            self.add("PYR001", node)
        if name in {"read_bytes", "read_text"} and not node.args:
            self.add("PYR002", node)
        if (name == "create_task" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "asyncio" and _inside_loop(node, self.parents)):
            self.add("PYR003", node)
        if name in {"append", "extend"} and isinstance(node.func.value, ast.Name) and _inside_while(node, self.parents):
            self.add("PYR008", node)
        if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "requests" and name in {"post", "put", "patch", "delete"}):
            self.add("PYR005", node, "P3")
        elif any(isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)
                 and k.value.value.lower() in PROD_VALUES for k in node.keywords):
            self.add("PYR005", node)

        if self.is_databricks:
            if name == "createDataFrame" and node.args and not isinstance(node.args[0], (ast.List, ast.Tuple, ast.Dict)):
                self.add("DBR012", node)
            if name == "collect":
                receiver = node.func.value
                bounded = isinstance(receiver, ast.Call) and _method_name(receiver) == "limit"
                self.add("DBR001", node, "P3" if bounded else None)
            elif name in {"toPandas", "to_pandas"}:
                self.add("DBR002", node)
            elif name in {"repartition", "coalesce"} and node.args and _integer_constant(node.args[0]) == 1:
                self.add("DBR003", node)
            elif name in {"cache", "persist"}:
                self.add("DBR004", node)
            elif name in {"applyInPandas", "applyInArrow", "applyInPandasWithState"}:
                self.add("DBR005", node)
            elif name == "toLocalIterator":
                parent = self.parents.get(id(node))
                if not (isinstance(parent, ast.Call) and parent.args and parent.args[0] is node
                        and isinstance(parent.func, ast.Name) and parent.func.id in {"list", "tuple", "set"}):
                    self.add("DBR007", node)
            elif (isinstance(node.func, ast.Name) and node.func.id in {"list", "tuple", "set"}
                  and node.args and isinstance(node.args[0], ast.Call)
                  and _method_name(node.args[0]) == "toLocalIterator"):
                self.add("DBR006", node)
            elif name in {"count", "show", "display"} and _inside_loop(node, self.parents):
                self.add("DBR011", node)

            if self.profile == "databricks-serverless":
                if name == "checkpoint":
                    self.add("DBR009", node)
                elif name in {"cacheTable", "uncacheTable", "clearCache"}:
                    self.add("DBR010", node)
                elif name == "sql" and node.args and isinstance(node.args[0], ast.Constant):
                    sql = node.args[0].value
                    if isinstance(sql, str) and re.match(r"\s*(?:CACHE|UNCACHE|CLEAR)\s+(?:LAZY\s+)?(?:TABLE|CACHE)\b", sql, re.I):
                        self.add("DBR010", node)
        self.generic_visit(node)


def _discover_roots(explicit_root: str | None) -> list[Path]:
    if explicit_root:
        return [Path(explicit_root).expanduser()]
    roots: list[Path] = []
    env = os.environ.get("DATABRICKS_AGENT_SKILLS_DIR")
    if env:
        roots.append(Path(env).expanduser())
    home = Path.home()
    roots += [
        Path.cwd() / ".agents" / "skills", Path.cwd() / ".claude" / "skills",
        home / ".agents" / "skills", home / ".claude" / "skills",
        home / ".codex" / "skills", home / ".cursor" / "skills",
    ]
    return roots


def find_databricks_core(explicit_root: str | None = None) -> Path | None:
    """Find locally installed skill. Does not validate publisher/manifest integrity."""
    for root in _discover_roots(explicit_root):
        candidates = [
            root / "databricks-core" / "SKILL.md",
            root / "skills" / "databricks-core" / "SKILL.md",
        ]
        if root.name == "databricks-core":
            candidates.append(root / "SKILL.md")
        for file in candidates:
            if file.is_file():
                try:
                    header = file.read_text(encoding="utf-8")[:4000]
                    if re.search(r"(?m)^name:\s*['\"]?databricks-core['\"]?\s*$", header):
                        return file.resolve()
                except (OSError, UnicodeError):
                    continue
    return None


def _walk_python_files(root: Path, exclude_tests: bool) -> list[Path]:
    if root.is_symlink():
        raise ValueError("Symlink root is not accepted for a source-only audit")
    if root.is_file():
        if root.suffix != ".py":
            raise ValueError("Target file must have .py extension")
        return [root]
    if not root.is_dir():
        raise ValueError("Target does not exist or is not a Python file/directory")
    result: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in EXCLUDED_DIRS and not (exclude_tests and d in {"tests", "test"})
                             and not (Path(dirpath) / d).is_symlink())
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            if exclude_tests and (name.startswith("test_") or name.endswith("_test.py")):
                continue
            target = Path(dirpath) / name
            if not target.is_symlink():
                result.append(target)
    return result


def scan(root: Path, profile: str, exclude_tests: bool = False) -> tuple[list[Finding], list[str], int]:
    root = root.expanduser()
    if root.is_symlink():
        raise ValueError("Symlink root is not accepted for a source-only audit")
    root = root.resolve()
    files = _walk_python_files(root, exclude_tests)
    base = root.parent if root.is_file() else root
    findings: list[Finding] = []
    errors: list[str] = []
    for path in files:
        relative = path.relative_to(base).as_posix()
        try:
            with tokenize.open(path) as source_file:
                source = source_file.read()
            tree = ast.parse(source, filename=relative)
        except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
            errors.append(f"{relative}: {type(exc).__name__}: {exc}")
            continue
        visitor = RiskVisitor(relative, source, profile, tree)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    findings.sort(key=lambda item: (LEVELS[item.severity], item.file, item.line, item.rule_id))
    return findings, errors, len(files)


def _load_baseline(path: str | None) -> set[str]:
    if not path:
        return set()
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    if (not isinstance(content, dict) or content.get("schema") != BASELINE_SCHEMA
            or not isinstance(content.get("fingerprints"), list)
            or not all(isinstance(x, str) for x in content["fingerprints"])):
        raise ValueError("Incompatible baseline. Expected {schema: 1, fingerprints: [...]}.")
    return set(content["fingerprints"])


def _write_json(path: str, value: dict[str, Any]) -> None:
    """Write *only* at the explicitly requested path."""
    destination = Path(path).expanduser()
    if destination.exists():
        raise ValueError(f"Refusing to overwrite existing output: {destination}")
    if not destination.parent.is_dir():
        raise ValueError(f"Output directory does not exist: {destination.parent}")
    with destination.open("x", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")


def _sarif_payload(findings: list[Finding], errors: list[str]) -> dict[str, Any]:
    used = sorted({item.rule_id for item in findings})
    results = []
    for item in findings:
        results.append({
            "ruleId": item.rule_id,
            "level": "warning" if item.severity in {"P1", "P2"} else "note",
            "message": {"text": f"{item.severity} HEURISTIC: {item.message} {item.recommendation}"},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": item.file},
                "region": {"startLine": item.line, "startColumn": item.column},
            }}],
            "partialFingerprints": {"primaryLocationLineHash": item.fingerprint},
            "properties": {"severity": item.severity, "memory_domain": item.memory_domain,
                           "baseline": item.baseline, "confidence": item.confidence},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "py-rails", "version": VERSION,
                                "informationUri": "https://agentskills.io/specification",
                                "rules": [{"id": rid, "name": rid,
                                           "shortDescription": {"text": RULES[rid].message}}
                                          for rid in used]}},
            "results": results,
            "invocations": [{"executionSuccessful": not errors,
                             "toolExecutionNotifications": [
                                 {"level": "error", "message": {"text": e}} for e in errors]}],
        }],
    }


def _format_text(findings: list[Finding], errors: list[str], total_files: int, profile: str) -> str:
    lines = [f"py-rails {VERSION} | {profile} | {total_files} Python file(s) | {len(findings)} heuristic finding(s)"]
    for item in findings:
        baseline = " [BASELINE]" if item.baseline else ""
        lines.append(f"{item.severity} {item.rule_id} {item.file}:{item.line}:{item.column}{baseline}")
        lines.append(f"  {item.message} [HEURISTIC; {item.memory_domain}]")
        lines.append(f"  Review: {item.recommendation}")
    for error in errors:
        lines.append(f"INCOMPLETE: {error}")
    if not findings and not errors:
        lines.append("No patterns matched. This does NOT certify memory efficiency.")
    lines.append("AST patterns only; no execution, Azure connection or RAM measurement performed.")
    return "\n".join(lines) + "\n"


def _add_upstream_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--upstream-root", help="Path to installed databricks-core, skills/ directory, or official repo root")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="py-rails", description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Check official skill availability, no network")
    doctor.add_argument("--profile", choices=PROFILES, default="databricks-classic")
    _add_upstream_option(doctor)
    audit = commands.add_parser("audit", help="Read-only Python AST scan")
    audit.add_argument("path", help="Python .py file or source directory")
    audit.add_argument("--profile", choices=PROFILES, default="python-general")
    audit.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    audit.add_argument("--output", help="Write report to NEW explicit path (never overwrite)")
    audit.add_argument("--baseline", help="Previously accepted fingerprint baseline JSON")
    audit.add_argument("--write-baseline", help="Write NEW JSON baseline to explicit path")
    audit.add_argument("--fail-on", choices=("P1", "P2", "P3"), help="Exit 1 for new findings at/above severity")
    audit.add_argument("--exclude-tests", action="store_true")
    _add_upstream_option(audit)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        if args.profile not in DATABRICKS_PROFILES:
            print("Python-only profile: official Databricks skills not required.")
            return 0
        found = find_databricks_core(args.upstream_root)
        if found is None:
            print("MISSING/UNVERIFIED: official databricks-core SKILL.md was not found locally.", file=sys.stderr)
            print("Install official databricks-agent-skills (databricks aitools install), then retry.", file=sys.stderr)
            print("Plugin caches may be undiscoverable: pass --upstream-root to the installed skills directory.", file=sys.stderr)
            return 3
        print(f"FOUND ON DISK: {found}")
        print("This does not prove the coding agent has activated the official skill.")
        return 0
    if args.profile in DATABRICKS_PROFILES:
        found = find_databricks_core(args.upstream_root)
        if not found:
            print("Databricks audit blocked: official databricks-core is missing/unverified.", file=sys.stderr)
            print("Use 'databricks aitools install', then --upstream-root if needed.", file=sys.stderr)
            return 3
    try:
        findings, errors, count = scan(Path(args.path), args.profile, args.exclude_tests)
        if count == 0:
            errors.append("No Python files found; audit coverage is empty.")
        baselined = _load_baseline(args.baseline)
        for finding in findings:
            finding.baseline = finding.fingerprint in baselined
        if args.write_baseline and errors:
            raise ValueError("Cannot create a baseline from an incomplete scan")
        if args.write_baseline:
            _write_json(args.write_baseline, {
                "schema": BASELINE_SCHEMA,
                "tool": f"py-rails {VERSION}",
                "fingerprints": sorted({f.fingerprint for f in findings}),
            })
        if args.format == "text":
            rendered = _format_text(findings, errors, count, args.profile)
        elif args.format == "sarif":
            rendered = json.dumps(_sarif_payload(findings, errors), ensure_ascii=False, indent=2) + "\n"
        else:
            rendered = json.dumps({
                "tool": "py-rails", "version": VERSION, "profile": args.profile,
                "files_scanned": count, "status": "INCOMPLETE" if errors else "COMPLETE",
                "measurements": "NOT_MEASURED", "errors": errors,
                "findings": [asdict(item) for item in findings],
            }, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            destination = Path(args.output).expanduser()
            if destination.exists():
                raise ValueError(f"Refusing to overwrite existing output: {destination}")
            if not destination.parent.is_dir():
                raise ValueError(f"Output directory does not exist: {destination.parent}")
            with destination.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
            print(f"Report saved: {destination}", file=sys.stderr)
        else:
            print(rendered, end="")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        return 2
    if args.fail_on and any(not item.baseline and LEVELS[item.severity] <= LEVELS[args.fail_on]
                            for item in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
