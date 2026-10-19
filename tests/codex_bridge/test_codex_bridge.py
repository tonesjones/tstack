"""Tests for skills/codex-delegate/scripts/codex_bridge.py against a fake Codex CLI. Stdlib only.

Run: python3 -m unittest discover -s tests/codex_bridge
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "skills" / "codex-delegate" / "scripts" / "codex_bridge.py"
FAKE = Path(__file__).resolve().parent / "fake_codex.py"


def write_launcher(path: Path, use_exec: bool) -> Path:
    """A `codex` on PATH. Without exec it stays the parent of the fake, like npm's node launcher."""
    if os.name == "nt":
        path = path.with_suffix(".cmd")
        path.write_text(f'@"{sys.executable}" "{FAKE}" %*\n')
    else:
        path.write_text(f'#!/bin/sh\n{"exec " if use_exec else ""}"{sys.executable}" "{FAKE}" "$@"\n')
        path.chmod(0o755)
    return path


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        launcher = write_launcher(self.tmp / "codex", use_exec=True)
        self.calls = self.tmp / "calls.jsonl"
        # Tier overrides or a GIT_DIR from the caller's shell would change what the bridge does.
        clean = {k: v for k, v in os.environ.items() if not k.startswith(("CODEX_MODEL_", "GIT_"))}
        self.env = dict(clean, CODEX_BIN=str(launcher), CODEX_HOME=str(self.tmp / "codex-home"),
                        CODEX_BRIDGE_HOME=str(self.tmp / "bridge-home"), FAKE_CODEX_CALLS=str(self.calls))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def worktree(self, name):
        wt = self.tmp / name
        self.git("worktree", "add", "-q", str(wt), "-b", f"codex/{name}")
        return wt

    def bridge(self, *args, cwd=None, **env):
        r = subprocess.run([sys.executable, str(BRIDGE), *args], capture_output=True, text=True,
                           env=dict(self.env, **env), cwd=cwd or self.tmp)
        receipt = None
        if "--- codex receipt: " in r.stdout:
            receipt = json.loads(r.stdout.split("--- codex receipt: ", 1)[1].strip())
        return r, receipt

    def call_count(self):
        return len(self.calls.read_text(encoding="utf-8").splitlines()) if self.calls.exists() else 0

    def last_call(self):
        return json.loads(self.calls.read_text(encoding="utf-8").splitlines()[-1])

    def assertRefused(self, result, message):
        r, receipt = result
        self.assertNotEqual(r.returncode, 0)
        self.assertIsNone(receipt)
        self.assertIn(message, r.stderr)

    # receipt

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
        self.assertIn("finding 49:", Path(receipt["final"]).read_text(encoding="utf-8"))

    def test_short_final_message_is_printed_whole(self):
        r, _ = self.bridge("run", "--cd", str(self.repo), "--prompt", "x")
        self.assertIn("finding 2:", r.stdout)
        self.assertNotIn("not printed", r.stdout)

    def test_missing_directory_is_reported_as_missing(self):
        self.assertRefused(self.bridge("run", "--write", "--cd", str(self.tmp / "wt-typo"), "--prompt", "x"),
                           "directory not found")

    # write guard

    def test_write_refused_in_main_working_tree(self):
        self.assertRefused(self.bridge("run", "--write", "--cd", str(self.repo), "--prompt", "edit"),
                           "main working tree")
        self.assertEqual(self.call_count(), 0)

    def test_workspace_write_sandbox_flag_is_guarded_too(self):
        self.assertRefused(self.bridge("run", "--sandbox", "workspace-write", "--cd", str(self.repo),
                                       "--prompt", "edit"), "main working tree")

    def test_add_dir_is_guarded_too(self):
        wt = self.worktree("wt-add")
        self.assertRefused(self.bridge("run", "--write", "--cd", str(wt), "--add-dir", str(self.repo),
                                       "--prompt", "edit"), "main working tree")

    def test_write_refused_in_the_worktree_the_bridge_runs_from(self):
        wt = self.worktree("wt-session")
        self.assertRefused(self.bridge("run", "--write", "--cd", ".", "--prompt", "edit", cwd=wt),
                           "checkout the bridge was run from")

    def test_no_worktree_check_never_allows_a_main_tree(self):
        self.assertRefused(self.bridge("run", "--write", "--no-worktree-check", "--cd", str(self.repo),
                                       "--prompt", "edit"), "main working tree")
        scratch = self.tmp / "scratch"
        scratch.mkdir()
        self.assertRefused(self.bridge("run", "--write", "--no-worktree-check", "--cd", str(scratch),
                                       "--add-dir", str(self.repo), "--prompt", "edit"), "main working tree")

    def test_no_worktree_check_never_allows_repo_internals(self):
        self.assertRefused(self.bridge("run", "--write", "--no-worktree-check", "--cd", str(self.repo / ".git"),
                                       "--prompt", "edit"), "inside a git directory")
        broken = self.tmp / "broken"
        broken.mkdir()
        (broken / ".git").write_text("gitdir: /nonexistent\n")
        self.assertRefused(self.bridge("run", "--write", "--no-worktree-check", "--cd", str(broken),
                                       "--prompt", "edit"), "git refuses to read")

    def test_write_refused_outside_git_unless_overridden(self):
        scratch = self.tmp / "scratch"
        scratch.mkdir()
        self.assertRefused(self.bridge("run", "--write", "--cd", str(scratch), "--prompt", "edit"),
                           "not inside a git repository")
        r, _ = self.bridge("run", "--write", "--no-worktree-check", "--cd", str(scratch), "--prompt", "edit")
        self.assertEqual(r.returncode, 0, r.stderr)

    # resume

    def test_resume_returns_to_the_worktree_with_its_sandbox_and_model(self):
        wt = self.worktree("wt-task")
        r, receipt = self.bridge("run", "--tier", "luna", "--write", "--cd", str(wt), "--prompt", "edit")
        self.assertEqual(r.returncode, 0, r.stderr)

        r, resumed = self.bridge("resume", receipt["thread"], "--prompt", "add tests")
        self.assertEqual(r.returncode, 0, r.stderr)
        call = self.last_call()
        self.assertEqual(Path(call["cwd"]), wt.resolve())
        self.assertIn('sandbox_mode="workspace-write"', call["argv"])
        self.assertEqual(call["stdin"], "add tests")
        self.assertEqual(resumed["requested_model"], "gpt-6-luna")

    def test_resume_reports_the_latest_turns_model(self):
        _, receipt = self.bridge("run", "--tier", "luna", "--cd", str(self.repo), "--prompt", "x")
        _, resumed = self.bridge("resume", receipt["thread"], "--tier", "sol", "--prompt", "deeper")
        self.assertEqual(resumed["requested_model"], "gpt-6.1-sol")
        self.assertEqual(resumed["model"], "gpt-6.1-sol")

    def test_resume_cd_cannot_move_a_write_thread_into_the_main_tree(self):
        wt = self.worktree("wt-move")
        _, receipt = self.bridge("run", "--write", "--cd", str(wt), "--prompt", "edit")
        calls = self.call_count()
        self.assertRefused(self.bridge("resume", receipt["thread"], "--cd", str(self.repo), "--prompt", "more"),
                           "main working tree")
        self.assertEqual(self.call_count(), calls)

    def test_resume_refuses_a_removed_worktree(self):
        wt = self.worktree("wt-gone")
        _, receipt = self.bridge("run", "--write", "--cd", str(wt), "--prompt", "edit")
        self.git("worktree", "remove", "--force", str(wt))
        calls = self.call_count()
        self.assertRefused(self.bridge("resume", receipt["thread"], "--prompt", "more"), "directory not found")
        self.assertEqual(self.call_count(), calls)

    def test_resume_keeps_a_recorded_worktree_check_skip_for_the_same_directory(self):
        scratch = self.tmp / "scratch"
        scratch.mkdir()
        _, receipt = self.bridge("run", "--write", "--no-worktree-check", "--cd", str(scratch), "--prompt", "x")
        r, _ = self.bridge("resume", receipt["thread"], "--prompt", "more")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('sandbox_mode="workspace-write"', self.last_call()["argv"])

    def test_read_only_waiver_does_not_carry_into_resume_write(self):
        scratch = self.tmp / "scratch"
        scratch.mkdir()
        _, receipt = self.bridge("run", "--no-worktree-check", "--cd", str(scratch), "--prompt", "look")
        calls = self.call_count()
        self.assertRefused(self.bridge("resume", receipt["thread"], "--write", "--prompt", "edit"),
                           "not inside a git repository")
        self.assertEqual(self.call_count(), calls)

    def test_read_only_add_dirs_do_not_become_writable_on_resume(self):
        wt, docs = self.worktree("wt-ro"), self.worktree("wt-ro-docs")
        _, receipt = self.bridge("run", "--cd", str(wt), "--add-dir", str(docs), "--prompt", "look")
        self.bridge("resume", receipt["thread"], "--write", "--prompt", "edit")
        self.assertFalse(any("writable_roots" in a for a in self.last_call()["argv"]))

    def test_resume_restores_extra_writable_dirs(self):
        wt, docs = self.worktree("wt-code"), self.worktree("wt-docs")
        _, receipt = self.bridge("run", "--write", "--cd", str(wt), "--add-dir", str(docs), "--prompt", "edit")
        self.bridge("resume", receipt["thread"], "--prompt", "also docs")
        argv = self.last_call()["argv"]
        self.assertIn("sandbox_workspace_write.writable_roots=" + json.dumps([str(docs.resolve())]), argv)

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib")
    def test_restored_dirs_keep_the_configured_writable_roots(self):
        home = Path(self.env["CODEX_HOME"])
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.toml").write_text('[sandbox_workspace_write]\nwritable_roots = ["/cache/x"]\n')
        wt, docs = self.worktree("wt-cfg"), self.worktree("wt-cfg-docs")
        _, receipt = self.bridge("run", "--write", "--cd", str(wt), "--add-dir", str(docs), "--prompt", "edit")
        self.bridge("resume", receipt["thread"], "--prompt", "more")
        roots = json.dumps(["/cache/x", str(docs.resolve())])
        self.assertIn("sandbox_workspace_write.writable_roots=" + roots, self.last_call()["argv"])

    def test_resume_without_a_new_turn_reports_no_model(self):
        _, receipt = self.bridge("run", "--tier", "luna", "--cd", str(self.repo), "--prompt", "x")
        _, resumed = self.bridge("resume", receipt["thread"], "--tier", "sol", "--ephemeral", "--prompt", "y")
        self.assertIsNone(resumed["model"])
        self.assertEqual(resumed["requested_model"], "gpt-6.1-sol")

    def test_resume_of_unknown_thread_is_read_only_unless_write(self):
        wt = self.worktree("wt-old")
        r, _ = self.bridge("resume", "old-thread", "--cd", str(wt), "--prompt", "hi")
        self.assertIn("pass --write", r.stderr)
        self.assertIn('sandbox_mode="read-only"', self.last_call()["argv"])
        r, _ = self.bridge("resume", "old-thread", "--cd", str(wt), "--write", "--prompt", "hi")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('sandbox_mode="workspace-write"', self.last_call()["argv"])
        self.assertRefused(self.bridge("resume", "old-thread", "--cd", str(self.repo), "--write", "--prompt", "hi"),
                           "main working tree")

    # review

    def test_review_is_read_only_and_targets_base(self):
        r, receipt = self.bridge("review", "--tier", "sol", "--cd", str(self.repo), "--base", "main")
        self.assertEqual(r.returncode, 0, r.stderr)
        call = self.last_call()
        self.assertEqual(call["argv"][:2], ["exec", "review"])
        self.assertIn('sandbox_mode="read-only"', call["argv"])
        self.assertEqual(call["argv"][-2:], ["--base", "main"])
        self.assertEqual(Path(call["cwd"]), self.repo.resolve())
        self.assertEqual(receipt["requested_model"], "gpt-6.1-sol")

    def test_review_with_custom_instructions_sends_them_alone(self):
        r, _ = self.bridge("review", "--cd", str(self.repo), "--prompt", "Review the diff against main.")
        self.assertEqual(r.returncode, 0, r.stderr)
        call = self.last_call()
        self.assertEqual(call["argv"][-1], "-")
        self.assertFalse({"--base", "--commit", "--uncommitted"} & set(call["argv"]))
        self.assertEqual(call["stdin"], "Review the diff against main.")

    def test_review_rejects_instructions_with_a_target_and_an_empty_request(self):
        self.assertRefused(self.bridge("review", "--cd", str(self.repo), "--base", "main", "--prompt", "auth"),
                           "exactly one of")
        self.assertRefused(self.bridge("review", "--cd", str(self.repo)), "exactly one of")
        self.assertRefused(self.bridge("review", "--cd", str(self.repo), "--base", "main", "--commit", "HEAD"),
                           "not allowed with argument")
        self.assertEqual(self.call_count(), 0)

    # timeout

    def test_timeout_kills_codex_behind_its_launcher_and_keeps_the_thread(self):
        launcher = write_launcher(self.tmp / "codex-wrapped", use_exec=False)
        done = self.tmp / "done"
        r, receipt = self.bridge("run", "--cd", str(self.repo), "--prompt", "x", "--timeout", "1",
                                 CODEX_BIN=str(launcher), FAKE_CODEX_SLEEP="3", FAKE_CODEX_DONE=str(done))
        self.assertEqual(r.returncode, 124)
        self.assertIn("timed out", r.stderr)
        self.assertEqual(receipt["exit"], 124)
        self.assertTrue(receipt["thread"])
        time.sleep(3.5)
        self.assertFalse(done.exists(), "the Codex process outlived the timeout")


    @unittest.skipIf(sys.version_info < (3, 11), "tomllib")
    def test_a_malformed_writable_roots_value_is_ignored(self):
        home = Path(self.env["CODEX_HOME"])
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.toml").write_text('[sandbox_workspace_write]\nwritable_roots = "/cache"\n')
        wt, docs = self.worktree("wt-bad"), self.worktree("wt-bad-docs")
        _, receipt = self.bridge("run", "--write", "--cd", str(wt), "--add-dir", str(docs), "--prompt", "edit")
        self.bridge("resume", receipt["thread"], "--prompt", "more")
        roots = json.dumps([str(docs.resolve())])
        self.assertIn("sandbox_workspace_write.writable_roots=" + roots, self.last_call()["argv"])

    @unittest.skipIf(os.name == "nt", "POSIX signals")
    def test_nohup_keeps_the_bridge_and_codex_running(self):
        launcher = write_launcher(self.tmp / "codex-wrapped", use_exec=False)
        done = self.tmp / "done-nohup"
        proc = subprocess.Popen([sys.executable, str(BRIDGE), "run", "--cd", str(self.repo), "--prompt", "x"],
                                env=dict(self.env, CODEX_BIN=str(launcher), FAKE_CODEX_SLEEP="2",
                                         FAKE_CODEX_DONE=str(done)),
                                cwd=self.tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                preexec_fn=lambda: signal.signal(signal.SIGHUP, signal.SIG_IGN))
        deadline = time.time() + 10
        while self.call_count() == 0 and time.time() < deadline:
            time.sleep(0.1)
        proc.send_signal(signal.SIGHUP)
        self.assertEqual(proc.wait(timeout=15), 0)
        self.assertTrue(done.exists())

    @unittest.skipIf(os.name == "nt", "POSIX sessions")
    def test_a_daemon_holding_the_pipes_does_not_hang_the_bridge(self):
        started = time.time()
        r, receipt = self.bridge("run", "--cd", str(self.repo), "--prompt", "x", FAKE_CODEX_DAEMON="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(receipt["thread"])
        self.assertLess(time.time() - started, 12)

    @unittest.skipIf(os.name == "nt", "POSIX signals")
    def test_stopping_the_bridge_stops_codex(self):
        launcher = write_launcher(self.tmp / "codex-wrapped", use_exec=False)
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            done = self.tmp / f"done-{int(sig)}"
            calls = self.call_count()
            proc = subprocess.Popen([sys.executable, str(BRIDGE), "run", "--cd", str(self.repo), "--prompt", "x"],
                                    env=dict(self.env, CODEX_BIN=str(launcher), FAKE_CODEX_SLEEP="3",
                                             FAKE_CODEX_DONE=str(done)),
                                    cwd=self.tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.time() + 10
            while self.call_count() == calls and time.time() < deadline:
                time.sleep(0.1)
            proc.send_signal(sig)
            proc.wait(timeout=10)
            time.sleep(3.5)
            self.assertFalse(done.exists(), f"Codex outlived the bridge after signal {sig.name}")


if __name__ == "__main__":
    unittest.main()
