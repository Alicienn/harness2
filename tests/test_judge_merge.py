# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A stale grade never survives a rollout it did not judge (issue #44)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from harness2.cli import judge as judge_cli
from harness2.core import judge


def row(**kw):
    base = {
        "task_id": "ledger-1",
        "mode": "agg",
        "k": 1,
        "label": "agg1",
        "run_id": "demo-oc-agg1/ledger-1/agg1",
        "chosen_is_base": False,
    }
    return judge.Scored(**base, **kw)


class MergeTests(unittest.TestCase):
    def test_same_rollout_keeps_its_grade_when_the_rejudge_fails(self):
        prev = row(n_passed=1, n_criteria=1, run_fingerprint="aaa")
        merged = judge_cli._merge([prev], [row(error="RuntimeError: down", run_fingerprint="aaa")])
        self.assertTrue(merged[0].graded)

    def test_replaced_rollout_loses_the_stale_grade_when_the_rejudge_fails(self):
        prev = row(n_passed=1, n_criteria=1, run_fingerprint="aaa")
        merged = judge_cli._merge([prev], [row(error="RuntimeError: down", run_fingerprint="bbb")])
        self.assertFalse(merged[0].graded)
        self.assertEqual(merged[0].error, "RuntimeError: down")

    def test_a_row_from_before_the_fingerprint_is_not_trusted(self):
        prev = row(n_passed=1, n_criteria=1)  # legacy row: no rollout identity recorded
        merged = judge_cli._merge([prev], [row(error="RuntimeError: down", run_fingerprint="aaa")])
        self.assertFalse(merged[0].graded)

    def test_judge_one_records_the_identity_of_the_rollout_it_graded(self):
        adapter = Mock()
        adapter.score.return_value = {"n_passed": 1, "n_criteria": 1}
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            (run_dir / "answer.txt").write_text("Total: 85.15")
            first = judge.judge_one(adapter, "ledger-1", "agg", 1, "agg1", "r1", run_dir)
            (run_dir / "answer.txt").write_text("Total: 105.25")
            second = judge.judge_one(adapter, "ledger-1", "agg", 1, "agg1", "r1", run_dir)
        self.assertTrue(first.run_fingerprint)
        self.assertNotEqual(first.run_fingerprint, second.run_fingerprint)

    def test_write_and_load_keep_the_fingerprint(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "judged.json"
            judge.write([row(n_passed=1, n_criteria=1, run_fingerprint="aaa")], path)
            self.assertEqual(judge_cli._load_rows(path)[0].run_fingerprint, "aaa")


if __name__ == "__main__":
    unittest.main()
