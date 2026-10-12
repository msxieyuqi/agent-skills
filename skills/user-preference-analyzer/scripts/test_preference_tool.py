"""Behavior tests; all ledgers and decisions are synthetic temporary data."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import preference_tool as tool


def record(record_id, confidence=0.96, status="proposed", value="yes", key=None):
    return {
        "id": record_id, "category": "communication", "preference_key": key or record_id,
        "value": value, "description": "示例偏好", "confidence": confidence,
        "scope": "示例范围", "last_validated": "2020-01-01", "confirmation_status": status,
        "conflicts_with": [], "linked_skill": None,
        "evidence": [{"source_type": "synthetic", "source": "test-only",
                      "detail": "示例证据", "observed_at": "2020-01-01", "source_project": "fictional-project"}],
    }


def registry(*records):
    return {"preferences": list(records), "history": [], "source_inventory": [], "authorized_sources": []}


class ReviewTests(unittest.TestCase):
    def test_strict_threshold_status_sort_and_compact_evidence(self):
        long = record("A", 0.99)
        long["evidence"][0]["detail"] = "字" * 150
        data = registry(record("B", 0.99), long, record("C", 0.9001), record("D", 0.9),
                        record("E", 1.0, "confirmed"), record("F", 1.0, "rejected"),
                        record("G", 1.0, "superseded"))
        before = copy.deepcopy(data)
        result = tool.review_registry(data)
        self.assertEqual([x["id"] for x in result["candidates"]], ["A", "B", "C"])
        self.assertEqual(len(result["candidates"][0]["evidence_summary"]), 100)
        self.assertNotIn("fictional-project", json.dumps(result))
        self.assertEqual(data, before)

    def test_empty_review_and_stale_boundary(self):
        self.assertEqual(tool.review_text(tool.review_registry(registry())), "暂无置信度超过 0.9 的待确认偏好。")
        a, b = record("A"), record("B")
        a["last_validated"] = (date.today() - timedelta(days=180)).isoformat()
        b["last_validated"] = (date.today() - timedelta(days=181)).isoformat()
        candidates = tool.review_registry(registry(a, b))["candidates"]
        self.assertFalse(candidates[0]["stale"])
        self.assertTrue(candidates[1]["stale"])

    def test_batch_decisions_preserve_evidence_and_validation_dates(self):
        data = registry(*(record(x) for x in "ABCDE"))
        decisions = [{"id": "A", "action": "confirm", "scope": "新的明确范围"},
                     {"id": "B", "action": "reject"}, {"id": "C", "scope": "仅示例项目"},
                     {"id": "D", "action": "defer"}]
        updated, changed = tool.review_decisions(data, decisions, tool.registry_version(data))
        self.assertEqual(changed, ["A", "B", "C"])
        self.assertEqual([x["confirmation_status"] for x in updated["preferences"]],
                         ["confirmed", "rejected", "proposed", "proposed", "proposed"])
        self.assertEqual(updated["preferences"][0]["confirmation_method"], "user")
        self.assertIn("confirmed_at", updated["preferences"][0])
        self.assertEqual(updated["preferences"][2]["scope"], "仅示例项目")
        for old, new in zip(data["preferences"], updated["preferences"]):
            for field in ("confidence", "evidence", "last_validated"):
                self.assertEqual(old[field], new[field])
        self.assertEqual(data["preferences"][0]["confirmation_status"], "proposed")
        self.assertEqual(len(updated["history"]), 3)
        self.assertEqual(updated["history"][0]["before"]["confirmation_status"], "proposed")
        self.assertEqual(updated["history"][0]["after"]["confirmation_status"], "confirmed")
        self.assertEqual(tool.validate_registry(updated), [])

    def test_invalid_batches_never_partially_mutate(self):
        data = registry(record("A"), record("LOW", 0.9))
        cases = [
            [{"id": "A", "action": "confirm"}, {"id": "missing", "action": "confirm"}],
            [{"id": "A", "action": "confirm"}, {"id": "A", "action": "reject"}],
            [{"id": "LOW", "action": "confirm"}],
            [{"id": "A", "action": "invalid"}], [{"id": "A", "action": {}}],
            [{"id": "A", "scope": ""}], [{"id": "A", "action": "defer", "scope": "new"}],
            [{"id": "A", "action": "confirm", "extra": True}], [], {},
        ]
        for decisions in cases:
            with self.subTest(decisions=decisions):
                before = copy.deepcopy(data)
                with self.assertRaises(ValueError):
                    tool.review_decisions(data, decisions, tool.registry_version(data))
                self.assertEqual(data, before)

    def test_changed_version_rejected(self):
        data = registry(record("A"))
        version = tool.registry_version(data)
        data["preferences"][0]["description"] = "另一个 Agent 改过的内容"
        with self.assertRaisesRegex(ValueError, "刷新清单"):
            tool.review_decisions(data, [{"id": "A", "action": "confirm"}], version)

    def test_conflicts_require_resolution_then_new_review(self):
        a, b = record("A", key="shared"), record("B", key="shared", value="no")
        a["conflicts_with"] = ["B"]
        data = registry(a, b)
        with self.assertRaisesRegex(ValueError, "unresolved conflicts"):
            tool.review_decisions(data, [{"id": "A", "action": "confirm"},
                                         {"id": "B", "action": "reject"}], tool.registry_version(data))
        updated, _ = tool.review_decisions(data, [{"id": "B", "action": "reject"}], tool.registry_version(data))
        self.assertEqual(tool.review_registry(updated)["candidates"][0]["conflicts_with"], [])
        final, _ = tool.review_decisions(updated, [{"id": "A", "action": "confirm"}], tool.registry_version(updated))
        self.assertEqual(final["preferences"][0]["confirmation_status"], "confirmed")

    def test_defer_is_noop_and_old_records_are_valid(self):
        data = registry(record("A"))
        self.assertEqual(tool.validate_registry(data), [])
        updated, changed = tool.review_decisions(data, [{"id": "A", "action": "defer"}], tool.registry_version(data))
        self.assertEqual(updated, data)
        self.assertEqual(changed, [])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="preference-tool-test-")
        self.root = Path(self.temp.name)
        self.registry = self.root / "docs/preferences/preferences.json"
        self.registry.parent.mkdir(parents=True)
        self.registry.write_text(json.dumps(registry(record("A")), ensure_ascii=False), encoding="utf-8")
        self.command = [sys.executable, str(Path(tool.__file__)), "--root", str(self.root)]

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, command=None, env=None):
        return subprocess.run((command or self.command) + list(args), capture_output=True, text=True, env=env)

    def decisions(self, choices):
        path = self.root / "choices.json"
        path.write_text(json.dumps(choices, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def test_read_only_review_and_failed_batch_bytes_unchanged(self):
        before = self.registry.read_bytes()
        result = self.run_cli("review", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.registry.read_bytes(), before)
        text = self.run_cli("review")
        self.assertEqual(text.returncode, 0)
        self.assertNotIn("fictional-project", text.stdout)
        choices = self.decisions([{"id": "A", "action": "confirm"}, {"id": "wrong", "action": "reject"}])
        failed = self.run_cli("review-decide", "--decisions", choices,
                              "--expected-version", json.loads(result.stdout)["version"])
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertFalse(self.registry.with_name(".preferences.json.lock").exists())

    def test_defer_does_not_write_file(self):
        before = self.registry.stat().st_mtime_ns
        review = json.loads(self.run_cli("review", "--format", "json").stdout)
        result = self.run_cli("review-decide", "--decisions", self.decisions([{"id": "A", "action": "defer"}]),
                              "--expected-version", review["version"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.registry.stat().st_mtime_ns, before)

    def test_shared_global_override_and_confirmation(self):
        shared = self.root / "shared"
        shared.mkdir()
        ledger = shared / "preferences.json"
        ledger.write_bytes(self.registry.read_bytes())
        env = dict(os.environ, USER_PREFERENCE_HOME=str(shared))
        cmd = [sys.executable, str(Path(tool.__file__)), "--global-store"]
        result = self.run_cli("review", "--format", "json", command=cmd, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        confirmed = self.run_cli("review-decide", "--decisions", self.decisions([{"id": "A", "action": "confirm"}]),
                                 "--expected-version", json.loads(result.stdout)["version"], command=cmd, env=env)
        self.assertEqual(confirmed.returncode, 0, confirmed.stderr)
        self.assertEqual(json.loads(ledger.read_text())["preferences"][0]["confirmation_status"], "confirmed")
        self.assertEqual(json.loads(self.registry.read_text())["preferences"][0]["confirmation_status"], "proposed")

    def test_status_update_does_not_refresh_validation_date(self):
        result = self.run_cli("update", "--id", "A", "--status", "confirmed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.registry.read_text())["preferences"][0]["last_validated"], "2020-01-01")

    def test_all_writes_wait_for_shared_lock_and_timeout(self):
        with tool.registry_lock(self.registry):
            result = self.run_cli("update", "--id", "A", "--status", "confirmed")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("稍后重试", result.stderr)
        self.assertEqual(json.loads(self.registry.read_text())["preferences"][0]["confirmation_status"], "proposed")

    def test_concurrent_adds_preserve_both_records(self):
        processes = []
        for record_id in ("B", "C"):
            args = ["add", "--id", record_id, "--category", "communication", "--key", record_id,
                    "--value", "yes", "--description", "synthetic record", "--confidence", "0.96",
                    "--scope", "synthetic", "--evidence-type", "synthetic", "--evidence-source", "test-only",
                    "--evidence-detail", "synthetic evidence"]
            processes.append(subprocess.Popen(self.command + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual({x["id"] for x in json.loads(self.registry.read_text())["preferences"]}, {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
