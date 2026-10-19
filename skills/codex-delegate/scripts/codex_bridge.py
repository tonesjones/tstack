#!/usr/bin/env python3
"""Bridge between Claude (orchestrator) and the OpenAI Codex CLI (delegate) on a ChatGPT/Codex login.

Commands:
  setup    install the Codex CLI if missing and restore a login from the environment if one is provided
  login    ChatGPT device-code login (prints a URL and a one-time code for the person to approve)
  status   CLI version, login state and tier -> model mapping
  run      send one task to `codex exec`; prints Codex's final message plus a short receipt
  resume   send a follow-up to an earlier run's thread, in the directory and sandbox that run used
  review   run Codex's built-in code review on a diff (read-only)

Credentials are never printed or logged. Works on Linux, macOS and Windows (Python 3.9+, Node 18+ for install).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BRIDGE_HOME = Path(os.environ.get("CODEX_BRIDGE_HOME", str(Path.home() / ".codex-bridge")))
CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
LOCAL_PREFIX = BRIDGE_HOME / "npm"
THREADS = BRIDGE_HOME / "threads"
# About 2K tokens: the orchestrator re-reads whatever is printed on every later turn.
DEFAULT_MAX_OUTPUT = 8000

# Tier names follow the Luna/Sol policy; override the model ids per environment without editing this file.
TIERS = {
    "luna": ("CODEX_MODEL_LUNA", "gpt-6-luna"),    # junior: bounded, mechanical, bulk
    "sol": ("CODEX_MODEL_SOL", "gpt-6.1-sol"),     # senior: security-sensitive or judgment-heavy
    "astra": ("CODEX_MODEL_ASTRA", "gpt-6-astra"),  # only when explicitly requested
}

PREAMBLE = (
    "You are working as a delegate for another coding agent that will review your output. "
    "Work only on the task below. Do not ask clarifying questions; state assumptions instead. "
    "End with a final message that contains the complete answer (findings, file paths with line "
    "numbers, and anything you could not verify).\n\n---\n\n"
)


def find_codex() -> str | None:
    override = os.environ.get("CODEX_BIN")
    if override:
        return shutil.which(override) or (override if Path(override).exists() else None)
    found = shutil.which("codex")
    if found:
        return found
    bin_dir = LOCAL_PREFIX / "node_modules" / ".bin"
    for name in ("codex.cmd", "codex") if os.name == "nt" else ("codex",):
        candidate = bin_dir / name
        if candidate.exists():
            return str(candidate)
    return None


def require_codex(auth: bool = True) -> str:
    exe = find_codex()
    if not exe:
        sys.exit("codex CLI not found. Run: python codex_bridge.py setup")
    if auth and not logged_in(exe)[0]:
        # Without this, codex exec retries 401s until the timeout.
        sys.exit("codex is not logged in. Run: python codex_bridge.py setup (or login)")
    return exe


def logged_in(exe: str) -> tuple[bool, str]:
    r = subprocess.run([exe, "login", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    text = (r.stdout + r.stderr).strip()
    # Report only the auth mode, never anything that could echo a key.
    if r.returncode != 0:
        return False, "not logged in"
    mode = "ChatGPT" if "chatgpt" in text.lower() else "API key" if "api key" in text.lower() else "logged in"
    return True, mode


def cmd_setup(args: argparse.Namespace) -> int:
    exe = find_codex()
    if not exe:
        npm = shutil.which("npm")
        if not npm:
            print("npm not found; install Node.js 18+ or put codex on PATH (or set CODEX_BIN).", file=sys.stderr)
            return 2
        print(f"installing @openai/codex into {LOCAL_PREFIX} ...", file=sys.stderr)
        LOCAL_PREFIX.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([npm, "install", "--prefix", str(LOCAL_PREFIX), "@openai/codex"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("npm install failed:\n" + "\n".join((r.stderr or r.stdout).splitlines()[-15:]), file=sys.stderr)
            return 2
        exe = find_codex()
        if not exe:
            print("install finished but codex binary not found", file=sys.stderr)
            return 2
    version = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip()
    print(f"codex: {exe} ({version})")

    ok, mode = logged_in(exe)
    if ok:
        print(f"auth: {mode}")
        return 0

    auth_json = os.environ.get("CODEX_AUTH_JSON")
    access_token = os.environ.get("CODEX_ACCESS_TOKEN")
    if auth_json:
        try:
            json.loads(auth_json)
        except ValueError:
            print("CODEX_AUTH_JSON is set but is not valid JSON; not written.", file=sys.stderr)
            return 3
        CODEX_HOME.mkdir(parents=True, exist_ok=True)
        target = CODEX_HOME / "auth.json"
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(auth_json)
        print(f"auth: restored from CODEX_AUTH_JSON into {target}")
    elif access_token:
        r = subprocess.run([exe, "login", "--with-access-token"], input=access_token, capture_output=True, text=True)
        if r.returncode != 0:
            print("auth: login with CODEX_ACCESS_TOKEN failed (exit %d)" % r.returncode, file=sys.stderr)
            return 3
    elif args.allow_api_key and os.environ.get("OPENAI_API_KEY"):
        # Bills the OpenAI API account, not the ChatGPT subscription, so only on explicit request.
        r = subprocess.run([exe, "login", "--with-api-key"], input=os.environ["OPENAI_API_KEY"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("auth: login with OPENAI_API_KEY failed (exit %d)" % r.returncode, file=sys.stderr)
            return 3
    else:
        print("auth: not logged in. Run `python codex_bridge.py login` (device code), or provide "
              "CODEX_AUTH_JSON / CODEX_ACCESS_TOKEN in the environment.")
        return 1

    ok, mode = logged_in(exe)
    print(f"auth: {mode}" if ok else "auth: credentials written but `codex login status` still fails")
    return 0 if ok else 3


def cmd_login(_: argparse.Namespace) -> int:
    exe = require_codex(auth=False)
    # Streams the verification URL and one-time code; the person approves it in their own browser.
    return subprocess.call([exe, "login", "--device-auth"])


def cmd_status(_: argparse.Namespace) -> int:
    exe = find_codex()
    if not exe:
        print("codex: not installed")
        return 1
    version = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip()
    ok, mode = logged_in(exe)
    print(f"codex: {exe} ({version})\nauth: {mode}")
    for tier, (env, default) in TIERS.items():
        print(f"tier {tier}: {os.environ.get(env) or default}" + (f"  (from {env})" if os.environ.get(env) else ""))
    return 0 if ok else 1


def resolve_model(args: argparse.Namespace) -> str | None:
    if args.model:
        return args.model
    if args.tier:
        env, default = TIERS[args.tier]
        return os.environ.get(env) or default
    return None  # Codex config default


def read_prompt(args: argparse.Namespace, required: bool = True, preamble: bool = True) -> str:
    if args.prompt_file:
        text = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.prompt:
        text = args.prompt
    elif required:
        text = sys.stdin.read()
    else:
        return ""
    if not text.strip():
        sys.exit("empty prompt (use --prompt, --prompt-file or stdin)")
    return PREAMBLE + text if preamble else text


def remember_thread(thread: str, record: dict) -> None:
    # One file per thread, so parallel runs never race on a shared index.
    THREADS.mkdir(parents=True, exist_ok=True)
    (THREADS / f"{thread}.json").write_text(json.dumps(record), encoding="utf-8")


def recorded_thread(thread: str) -> dict:
    try:
        return json.loads((THREADS / f"{thread}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def require_dir(path: Path) -> Path:
    if not path.is_dir():
        # A removed worktree must not silently become the main checkout.
        sys.exit(f"directory not found: {path}. Pass --cd with the directory to use.")
    return path


def git_lines(path: Path, *args: str) -> list[str] | None:
    try:
        r = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return r.stdout.splitlines() if r.returncode == 0 else None


def write_problem(path: Path) -> str | None:
    """Why Codex must not write in `path`, or None if it is a scratch linked worktree."""
    lines = git_lines(path, "rev-parse", "--git-dir", "--git-common-dir", "--show-toplevel")
    if not lines or len(lines) < 3:
        return "it is not inside a git repository (or git is not on PATH)"
    git_dir, common_dir, top = ((path / line).resolve() for line in lines[:3])
    if git_dir == common_dir:
        return "it is the repository's main working tree, not a linked worktree"
    # The session itself may run in a linked worktree; that one is not scratch either.
    caller = git_lines(Path.cwd(), "rev-parse", "--show-toplevel")
    if caller and (Path.cwd() / caller[0]).resolve() == top:
        return "it is the checkout the bridge was run from"
    return None


def guard_writes(dirs: list[Path], skip: bool) -> None:
    if skip:
        return
    for d in dirs:
        problem = write_problem(require_dir(d))
        if problem:
            sys.exit(f"refusing to let Codex write in {d}: {problem}. Run the bridge from your own checkout with "
                     "--cd on a scratch worktree from `git worktree add`, or pass --no-worktree-check for a "
                     "directory outside git.")


def clip(text: str, limit: int, full_path: Path) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    cut = text.rfind("\n", 0, limit)
    if cut < limit // 2:
        cut = limit
    rest = text[cut:]
    return (text[:cut].rstrip() + f"\n\n[... {len(rest)} more characters ({rest.count(chr(10))} lines) "
            f"not printed. Full message: {full_path}]")


def session_model(thread: str | None) -> str | None:
    """The model of the thread's latest turn, so a resumed turn reports what it ran on."""
    if not thread:
        return None
    model = None
    for path in (CODEX_HOME / "sessions").glob(f"**/*{thread}.jsonl"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("type") == "turn_context":
                model = row.get("payload", {}).get("model") or model
    return model


def run_codex(argv: list[str], prompt: str, timeout: int, cwd: Path) -> tuple[int, str, str]:
    # The npm `codex` is a launcher that spawns the native binary, so a timeout has to kill the whole
    # process group; killing only the launcher leaves Codex working on the thread.
    group = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
             else {"start_new_session": True})
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace", cwd=cwd, **group)
    try:
        out, err = proc.communicate(prompt, timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        print(f"codex timed out after {timeout}s", file=sys.stderr)
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        out, err = proc.communicate()
        return 124, out, err


def execute(make_argv, prompt: str, args: argparse.Namespace, label: str, cwd: Path, record: dict) -> int:
    """Run Codex with argv from make_argv(common flags), print the final message and a receipt."""
    logs = BRIDGE_HOME / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codex-bridge-") as d:
        out_file = Path(d) / "last_message.txt"
        argv = make_argv(common_flags(args, out_file))
        started = time.time()
        code, stdout, stderr = run_codex(argv, prompt, args.timeout, cwd)
        elapsed = time.time() - started
        final = out_file.read_text(encoding="utf-8").strip() if out_file.exists() else ""

    thread, usage, errors, commands, files = None, None, [], [], []
    for line in stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        kind = ev.get("type")
        if kind == "thread.started":
            thread = ev.get("thread_id")
        elif kind == "turn.completed":
            usage = ev.get("usage")
        elif kind in ("error", "turn.failed"):
            errors.append(ev.get("message") or json.dumps(ev.get("error", ev))[:500])
        elif kind == "item.completed":
            item = ev.get("item", {})
            if item.get("type") == "command_execution":
                commands.append(item.get("command", "?"))
            elif item.get("type") == "file_change":
                files += [f"{c.get('kind', '?')} {c.get('path', '?')}" for c in item.get("changes", [])]

    if thread:
        remember_thread(thread, {"cwd": str(cwd), **record})
    log = logs / f"{time.strftime('%Y%m%d-%H%M%S')}-{label}-{thread or 'nothread'}.log"
    log.write_text(f"argv: {argv}\ncwd: {cwd}\nexit: {code}\n--- stdout (events) ---\n{stdout}\n"
                   f"--- stderr ---\n{stderr}", encoding="utf-8")

    final_path = log.with_name(log.stem + ".final.md")
    if final:
        final_path.write_text(final + "\n", encoding="utf-8")
        print(clip(final, args.max_output, final_path))
    receipt = {
        "exit": code,
        "thread": thread,
        "requested_model": record.get("model"),
        "model": session_model(thread),
        "seconds": round(elapsed),
        "usage": usage,
        "commands_run": len(commands),
        "files_changed": files,
        "errors": errors,
        "cwd": str(cwd),
        "final": str(final_path) if final else None,
        "log": str(log),
    }
    print("\n--- codex receipt: " + json.dumps(receipt))
    if code != 0 or not final:
        tail = "\n".join(stderr.strip().splitlines()[-12:])
        print(f"codex failed (exit {code}); stderr tail:\n{tail}", file=sys.stderr)
        return code or 1
    return 0


def common_flags(args: argparse.Namespace, out_file: Path) -> list[str]:
    flags = ["--skip-git-repo-check", "--json", "-o", str(out_file)]
    model = resolve_model(args)
    if model:
        flags += ["-m", model]
    if args.effort:
        flags += ["-c", f'model_reasoning_effort="{args.effort}"']
    if args.schema:
        flags += ["--output-schema", str(Path(args.schema).resolve())]
    if args.ephemeral:
        flags.append("--ephemeral")
    return flags


def cmd_run(args: argparse.Namespace) -> int:
    sandbox = "workspace-write" if args.write else args.sandbox
    cd = require_dir(Path(args.cd).resolve())
    add_dirs = [Path(extra).resolve() for extra in args.add_dir or []]
    if sandbox == "workspace-write":
        guard_writes([cd, *add_dirs], args.no_worktree_check)
    exe = require_codex()
    prompt = read_prompt(args, preamble=not args.raw)
    extra = [arg for d in add_dirs for arg in ("--add-dir", str(d))]
    record = {"sandbox": sandbox, "model": resolve_model(args), "unchecked": args.no_worktree_check}
    return execute(lambda flags: [exe, "exec", *flags, "-s", sandbox, "-C", str(cd), *extra, "-"],
                   prompt, args, args.tier or "default", cd, record)


def cmd_resume(args: argparse.Namespace) -> int:
    # `codex exec resume` takes no --cd or --sandbox and runs where it is started, so restore both.
    recorded = recorded_thread(args.thread)
    cd = require_dir(Path(args.cd or recorded.get("cwd") or ".").resolve())
    sandbox = "workspace-write" if args.write else recorded.get("sandbox", "read-only")
    if not recorded:
        hint = "" if args.write else " (pass --write to let it edit a scratch worktree)"
        print(f"no record for thread {args.thread}; resuming with a {sandbox} sandbox in {cd}{hint}",
              file=sys.stderr)
    if sandbox == "workspace-write":
        # A recorded --no-worktree-check covers only the directory it was given for.
        guard_writes([cd], args.no_worktree_check or (recorded.get("unchecked") and not args.cd))
    exe = require_codex()
    prompt = read_prompt(args, preamble=False)
    record = {"sandbox": sandbox, "model": resolve_model(args) or recorded.get("model"),
              "unchecked": args.no_worktree_check or (recorded.get("unchecked", False) and not args.cd)}
    return execute(lambda flags: [exe, "exec", "resume", *flags, "-c", f'sandbox_mode="{sandbox}"',
                                  args.thread, "-"],
                   prompt, args, "resume", cd, record)


def cmd_review(args: argparse.Namespace) -> int:
    cd = require_dir(Path(args.cd).resolve())
    prompt = read_prompt(args, required=False, preamble=False)
    target = (["--base", args.base] if args.base else ["--commit", args.commit] if args.commit
              else ["--uncommitted"] if args.uncommitted else [])
    if bool(target) == bool(prompt):
        sys.exit("review takes exactly one of --base, --commit, --uncommitted, or --prompt/--prompt-file: "
                 "Codex rejects custom instructions combined with a diff target.")
    exe = require_codex()
    record = {"sandbox": "read-only", "model": resolve_model(args), "unchecked": False}
    return execute(lambda flags: [exe, "exec", "review", *flags, "-c", 'sandbox_mode="read-only"',
                                  *(target or ["-"])],
                   prompt, args, f"review-{args.tier or 'default'}", cd, record)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("setup", help="install codex if missing; restore login from the environment")
    s.add_argument("--allow-api-key", action="store_true",
                   help="fall back to OPENAI_API_KEY (bills the API account, not the subscription)")
    s.set_defaults(fn=cmd_setup)
    sub.add_parser("login", help="device-code login with ChatGPT").set_defaults(fn=cmd_login)
    sub.add_parser("status", help="show install, auth and tier mapping").set_defaults(fn=cmd_status)

    def task_flags(q: argparse.ArgumentParser) -> None:
        q.add_argument("--tier", choices=sorted(TIERS), help="luna (bulk) | sol (judgment) | astra (explicit only)")
        q.add_argument("--model", help="exact model id; overrides --tier")
        q.add_argument("--effort", help="model_reasoning_effort override (e.g. low, medium, high)")
        q.add_argument("--prompt", help="task text (else --prompt-file, else stdin)")
        q.add_argument("--prompt-file")
        q.add_argument("--schema", help="JSON Schema file the final message must match")
        q.add_argument("--ephemeral", action="store_true", help="do not persist the Codex session (no resume)")
        q.add_argument("--timeout", type=int, default=1800, help="seconds (default 1800)")
        q.add_argument("--max-output", type=int, default=DEFAULT_MAX_OUTPUT,
                       help=f"print at most this many characters of the final message; the full text is saved "
                            f"to the receipt's `final` path (default {DEFAULT_MAX_OUTPUT}, 0 prints all)")

    def write_flags(q: argparse.ArgumentParser) -> None:
        q.add_argument("--no-worktree-check", action="store_true",
                       help="allow writes outside a scratch linked git worktree (for a directory outside git)")

    r = sub.add_parser("run", help="run one task through `codex exec`")
    task_flags(r)
    write_flags(r)
    r.add_argument("--cd", default=".", help="working root Codex sees (default: current directory)")
    r.add_argument("--sandbox", default="read-only", choices=["read-only", "workspace-write"])
    r.add_argument("--write", action="store_true", help="shorthand for --sandbox workspace-write")
    r.add_argument("--add-dir", action="append", help="extra writable directory (workspace-write only)")
    r.add_argument("--raw", action="store_true", help="send the prompt without the delegate preamble")
    r.set_defaults(fn=cmd_run)

    c = sub.add_parser("resume", help="follow up on an earlier thread, in its recorded directory and sandbox")
    c.add_argument("thread", help="thread id from a previous receipt")
    task_flags(c)
    write_flags(c)
    c.add_argument("--cd", help="directory to resume in (default: the one recorded for the thread)")
    c.add_argument("--write", action="store_true",
                   help="workspace-write sandbox, for a thread with no record (checked like run --write)")
    c.set_defaults(fn=cmd_resume)

    v = sub.add_parser("review", help="Codex's built-in review, read-only: a diff target or custom instructions")
    task_flags(v)
    v.add_argument("--cd", default=".", help="repository to review (default: current directory)")
    v.add_argument("--base", help="review changes against this base branch")
    v.add_argument("--commit", help="review the changes one commit introduced")
    v.add_argument("--uncommitted", action="store_true", help="review staged, unstaged and untracked changes")
    v.set_defaults(fn=cmd_review)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
