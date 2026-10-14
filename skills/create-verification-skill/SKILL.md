---
name: "create-verification-skill"
description: "Run with /create-verification-skill. Generates a project-local verify skill under .claude/skills/ that launches the app, drives it the way a user does, and captures evidence, for any language, framework, or platform. Use for 'make a verify skill for this repo' or when a project has no scripted way to prove UI, CLI, or service behavior. Keep it current with /maintain-verification-skill."
disable-model-invocation: true
---

# Create a verification skill

Version: 1.0.1 (2026-10-14)

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, use a feature the way a user would, and capture evidence. This skill writes that as a project-local skill at `.claude/skills/verify-<app>/`, tailored to the repo. The reader is the next agent, not a human. It will read the skill cold, mid-task, having never seen the app.

## 1. Interview the repo, not the user

Answer these from the codebase. Ask the user only what you can't observe.

- **Surface.** What does a user actually touch? A web UI, a CLI or TUI, a desktop app, an API, a mobile app, a library? A repo can have several. Pick the primary one and note the rest.
- **Run.** How does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart). Note ports, env vars, seed data, and auth.
- **Drive.** How can an agent interact with it programmatically? Look for existing harnesses first: Playwright or Cypress specs, expect scripts, PTY helpers, curl-able endpoints, a debug port. Only then pick a generic recipe: Playwright or CDP for web and Electron, a tmux or PTY harness for a CLI or TUI, plain HTTP for services.
- **Observe.** What evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate.** Can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill. Refusing to double-drive a shared instance beats corrupting the user's session.

If the checkout doesn't build or start as-is, fix that first, or report exactly what fails, before you generate anything. A skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, marked as verification scaffolding, and remove it in cleanup.

The drive recipe must be something any session can rerun from a shell. A browser MCP tool in this session (Claude in Chrome, the built-in browser) is fine for exploring the app while you interview it, but the generated skill drives through a script or CLI in the repo, so a session without those tools can still verify.

## 2. Generate the skill

Write `.claude/skills/verify-<app>/SKILL.md`. It needs YAML frontmatter with `name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it. Without frontmatter the skill never registers. Fill each section below from what the interview found. Leave no placeholders.

- **Launch.** The exact command that starts the app for verification, and how to tell it's ready: a log line, a port answering, a prompt. Include teardown. For a long-lived server, say to start it in the background (Bash `run_in_background`, or `nohup` with a log file) and poll for readiness instead of sleeping. A short-lived CLI or TUI has no server to keep alive. Launch means build the binary or install deps once, then start each drive in its own isolated PTY or tmux session.
- **Doctor.** One read-only check that answers "is this instance worth driving?": process up, right version or build, port owned by us, auth valid. An agent runs it first, and again whenever anything looks off.
- **Drive.** The harness recipe with real selectors and commands from this repo, not examples. Prefer stable handles (ARIA roles and names, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Evidence.** What to capture for a proof and where it goes. State the proof standards:
  - Exercise the real user path, not internal setters or test-only endpoints.
  - Capture the action and the resulting state, not only the final screen.
  - Verify side effects (files written, rows inserted, messages sent) alongside what's visible.
  - Use mocks only where a production boundary already isolates the external system.
  - When the safe path is a dry-run or test mode, check what it actually skips by observing files, network, and git refs. Don't trust its name. Some dry-runs still touch the network or open a browser.
  - Open each screenshot with the Read tool and confirm it shows what the proof claims before you cite it.
- **Cleanup.** How to tear down what the run created. Never kill by process name. Kill the PIDs you started. Cleanup removes instances and scratch state, never the evidence. Proof artifacts survive teardown, in a location the skill names. Keep that location out of commits (add it to `.gitignore` if it sits in the repo).
- **Helpers.** Any script the skill ships is executable (`chmod +x`) and its invocation appears in the skill body. A helper the reader has to reverse-engineer is not a helper.

## 3. Seed the feature map

Create `.claude/skills/verify-<app>/features/README.md` plus one file per user-facing feature you can identify. Start with the top 3 to 5, found from routes, commands, menus, or docs. Follow the shape in [`references/feature-map-example/`](references/feature-map-example/): a README index and one file per feature.

Each feature file answers, from the user's point of view, what the feature is, how to reach it, how to drive it with the harness, and what observable end state proves it works. Use exactly these four H2s, in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`.

The map is the repo's maintained verification source. A proof that drives one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive one mapped feature, capture evidence, clean up. One feature is enough. The map exists so later runs can cover the rest. After cleanup, confirm the evidence still exists at the named location. A cleanup that eats the proof fails this step.

Fix what fails. Run the generated cleanup after every failed attempt too, so broken attempts don't strand processes and ports. A generated skill that was never executed is a draft, not a deliverable.

Claude Code picks up a new `.claude/skills/` folder at session start. If `/verify-<app>` doesn't appear in this session, follow the SKILL.md by reading it directly for the proof run, and tell the user a new session will list it.

## 5. Hand it over

Tell the user what was generated, which feature the proof run drove, and where its evidence is. Suggest committing the folder so every person and agent drives the app the same way. Point them at `/maintain-verification-skill` for keeping the map honest as the app changes. Suggest a cadence only if they ask.
