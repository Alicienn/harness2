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

"""A misconfiguration is one remediation line, not a traceback (issue #38)."""

import contextlib
import io
import unittest

from harness2.cli import judge as judge_cli
from harness2.cli import report as report_cli


def run(main, argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        status = main(argv)
    return status, err.getvalue()


class CliErrorTests(unittest.TestCase):
    def test_report_reports_a_bad_mode_without_a_traceback(self):
        status, err = run(report_cli.main, ["--bench", "lab", "--mode", "bogus"])
        self.assertEqual(status, 1)
        self.assertIn("error: --modes: unknown mode 'bogus'", err)
        self.assertNotIn("Traceback", err)

    def test_judge_reports_a_bad_mode_without_a_traceback(self):
        status, err = run(judge_cli.main, ["--bench", "lab", "--mode", "bogus"])
        self.assertEqual(status, 1)
        self.assertIn("error: --modes: unknown mode 'bogus'", err)
        self.assertNotIn("Traceback", err)

    def test_both_commands_refuse_wb_without_a_subset(self):
        for main in (report_cli.main, judge_cli.main):
            status, err = run(main, ["--bench", "wb"])
            self.assertEqual(status, 1)
            self.assertTrue(err.startswith("error: "), err)
            self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
