"""Tests for skills/codex-delegate/scripts/codex_bridge.py against a fake Codex CLI. Stdlib only.

Run: python3 -m unittest discover -s tests/codex_bridge
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "skills" / "codex-delegate" / "scripts" / "codex_bridge.py"
FAKE = Path(__file__).resolve().parent / "fake_codex.py"


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        launcher = self.tmp / ("codex.cmd" if os.name == "nt" else "codex")
        if os.name == "nt":
            launcher.write_text(f'@"{sys.executable}" "{FAKE}" %*\n')
        else:
            launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
            launcher.chmod(0o755)
        self.calls = self.tmp / "calls.jsonl"
        self.env = dict(os.environ, CODEX_BIN=str(launcher), CODEX_HOME=str(self.tmp / "codex-home"),
                        CODEX_BRIDGE_HOME=str(self.tmp / "bridge-home"), FAKE_CODEX_CALLS=str(self.calls))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")

    def git(self, *args, cwd=None):
        subprocess.run(["git", *args], cwd=cwd or self.repo, check=True, capture_output=True)

    def bridge(self, *args, **env):
        r = subprocess.run([sys.executable, str(BRIDGE), *args], capture_output=True, text=True,
                           env=dict(self.env, **env), cwd=self.tmp)
        receipt = None
        if "--- codex receipt: " in r.stdout:
            receipt = json.loads(r.stdout.split("--- codex receipt: ", 1)[1].strip())
        return r, receipt

    def last_call(self):
        return json.loads(self.calls.read_text(encoding="utf-8").splitlines()[-1])

    def test_receipt_reports_requested_and_actual_model(self):
        r, receipt = self.bridge("run", "--tier", "luna", "--cd", str(self.repo), "--prompt", "list files")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(receipt["requested_model"], "gpt-6-luna")
        self.assertEqual(receipt["model"], "gpt-6-luna")
        self.assertEqual(Path(receipt["cwd"]), self.repo.resolve())

    def test_ephemeral_keeps_requested_model(self):
        _, receipt = self.bridge("run", "--tier", "sol", "--ephemeral", "--cd", str(self.repo), "--prompt", "x")
        self.assertIsNone(receipt["model"])
        self.assertEqual(receipt["requested_model"], "gpt-6.1-sol")

    def test_long_final_message_is_clipped_and_saved(self):
        r, receipt = self.bridge("run", "--cd", str(self.repo), "--prompt", "x", "--max-output", "200",
                                 FAKE_CODEX_LINES="50")
        printed = r.stdout.split("\n--- codex receipt: ", 1)[0]
        self.assertLess(len(printed), 400)
        self.assertIn("not printed. Full message:", printed)
        full = Path(receipt["final"]).read_text(encoding="utf-8")
        self.assertIn("finding 49:", full)

    def test_short_final_message_is_printed_whole(self):
        r, _ = self.bridge("run", "--cd", str(self.repo), "--prompt", "x")
        self.assertIn("finding 2:", r.stdout)
        self.assertNotIn("not printed", r.stdout)

    def test_write_refused_in_main_working_tree(self):
        r, receipt = self.bridge("run", "--write", "--cd", str(self.repo), "--prompt", "edit")
        self.assertNotEqual(r.returncode, 0)
        self.assertIsNone(receipt)
        self.assertIn("main working tree", r.stderr)
        self.assertFalse(self.calls.exists())

    def test_workspace_write_sandbox_flag_is_guarded_too(self):
        r, _ = self.bridge("run", "--sandbox", "workspace-write", "--cd", str(self.repo), "--prompt", "edit")
        self.assertIn("main working tree", r.stderr)

    def test_write_refused_outside_git_unless_overridden(self):
        scratch = self.tmp / "scratch"
        scratch.mkdir()
        r, _ = self.bridge("run", "--write", "--cd", str(scratch), "--prompt", "edit")
        self.assertIn("not inside a git repository", r.stderr)
        r, _ = self.bridge("run", "--write", "--no-worktree-check", "--cd", str(scratch), "--prompt", "edit")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_write_allowed_in_linked_worktree_and_resume_returns_there(self):
        wt = self.tmp / "wt-codex-task"
        self.git("worktree", "add", "-q", str(wt), "-b", "codex/task")
        r, receipt = self.bridge("run", "--write", "--cd", str(wt), "--prompt", "edit")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("workspace-write", self.last_call()["argv"])

        r, _ = self.bridge("resume", receipt["thread"], "--prompt", "add tests")
        self.assertEqual(r.returncode, 0, r.stderr)
        call = self.last_call()
        self.assertEqual(Path(call["cwd"]), wt.resolve())
        self.assertIn('sandbox_mode="workspace-write"', call["argv"])
        self.assertEqual(call["stdin"], "add tests")

    def test_resume_refuses_a_removed_worktree(self):
        wt = self.tmp / "wt-gone"
        self.git("worktree", "add", "-q", str(wt), "-b", "codex/gone")
        _, receipt = self.bridge("run", "--write", "--cd", str(wt), "--prompt", "edit")
        self.git("worktree", "remove", "--force", str(wt))
        calls = len(self.calls.read_text(encoding="utf-8").splitlines())
        r, _ = self.bridge("resume", receipt["thread"], "--prompt", "more")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("directory not found", r.stderr)
        self.assertEqual(len(self.calls.read_text(encoding="utf-8").splitlines()), calls)

    def test_resume_of_unknown_thread_warns(self):
        r, _ = self.bridge("resume", "no-such-thread", "--prompt", "hi")
        self.assertIn("no directory recorded", r.stderr)
        self.assertIn('sandbox_mode="read-only"', self.last_call()["argv"])

    def test_review_is_read_only_and_targets_base(self):
        r, receipt = self.bridge("review", "--tier", "sol", "--cd", str(self.repo), "--base", "main")
        self.assertEqual(r.returncode, 0, r.stderr)
        call = self.last_call()
        self.assertEqual(call["argv"][:2], ["exec", "review"])
        self.assertIn('sandbox_mode="read-only"', call["argv"])
        self.assertEqual(call["argv"][call["argv"].index("--base") + 1], "main")
        self.assertNotIn("-", call["argv"])
        self.assertEqual(Path(call["cwd"]), self.repo.resolve())
        self.assertEqual(receipt["requested_model"], "gpt-6.1-sol")

    def test_review_passes_custom_instructions_on_stdin(self):
        self.bridge("review", "--cd", str(self.repo), "--uncommitted", "--prompt", "focus on auth")
        call = self.last_call()
        self.assertIn("--uncommitted", call["argv"])
        self.assertEqual(call["argv"][-1], "-")
        self.assertEqual(call["stdin"], "focus on auth")

    def test_timeout_still_prints_receipt_with_thread(self):
        r, receipt = self.bridge("run", "--cd", str(self.repo), "--prompt", "x", "--timeout", "1",
                                 FAKE_CODEX_SLEEP="5")
        self.assertEqual(r.returncode, 124)
        self.assertIn("timed out", r.stderr)
        self.assertEqual(receipt["exit"], 124)
        self.assertTrue(receipt["thread"])


if __name__ == "__main__":
    unittest.main()
