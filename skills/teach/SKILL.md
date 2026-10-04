---
name: "teach"
description: "Run with /teach. Explains a body of work plainly so a person actually understands it: what it is, how it works, and why it is built that way. Explores the code itself and, when the reasons matter, digs through git history and any connected tools. Use for 'teach me this', 'help me really understand X', and 'explain this change or subsystem'."
disable-model-invocation: true
---

# Teach

Version: 1.0.0 (2026-10-03)

**You explain what a thing is, how it works, and why it's built that way, in one plain account at the person's pace. The goal is that they understand it, not that you change anything.**

Teach covers three kinds of question with one voice:

- **What and how.** Runtime flow, architecture, ownership, where something should live.
- **Why.** The forces behind a design: decisions, tradeoffs, regressions, thresholds.
- **Both.** The usual case for "teach me X".

You do the reading, delegate the digging when it pays, and write the explanation yourself. Subagents return evidence. They never write the answer the person sees. If you can't spawn subagents (a chat without the Agent tool), do the same work inline. This skill works best in Claude Code, where it can read the repo and run git.

## Steps

1. **Pick what they should walk away understanding.** Choose a few things from why they're asking (about to change it, reviewing it, debugging it, new to it) and what they already know. Read both from the conversation, open files, and recent edits. Don't quiz them. Skip what they plainly know. Put the depth where their question is. If the target is vague, state your best guess and proceed. They can redirect.

2. **Size the work to the question.**

   | Question | What to do |
   |---|---|
   | One function, module, or small change | Read the code yourself and answer. No subagents. |
   | A subsystem, cross-cutting feature, or architecture | Spawn explorers (see How). |
   | Why something is the way it is | Anchor in git, then widen if git leaves the answer thin (see Why). |
   | "Teach me X" on something big | Build the code anchor first, then spawn the How explorers and any Why investigators together in one message. |

   When in doubt, take the smaller path. The person can always ask for more.

3. **Gather.** Read the code yourself first to get oriented. Delegate the wide sweeps.

4. **Explain.** Follow the teaching rules below.

## How: explore the code

Decompose the question into 2 to 4 distinct slices of the subsystem. Spawn one explorer per slice in a single message:

- `subagent_type`: `Explore` (no file edits)
- `model`: `sonnet`
- Prompt: `reference/how.md`, with the question and that explorer's slice filled in, and ask for "very thorough" breadth.

Fact-gathering does not need Opus. Reconcile the explorers' findings yourself, and check the code directly where they overlap or disagree. Anything they marked as an open question stays open in your answer.

## Why: dig for motivation

Code doesn't carry its own motivation. Be a careful, cautious investigator and read `reference/why.md` before you start. It holds the confidence tiers and phrasing you must follow.

**Default (narrow).** Build the code anchor yourself:

- File paths, line ranges, key symbols.
- `git blame` on the target lines, `git log --follow` and pickaxe (`-S`, `-G`) for when it appeared.
- PR numbers from commit subjects, then `gh pr view` for bodies, reviews, and linked issues.
- Nearby comments, tests, and changelog entries.
- If the target looks defensive (null checks, retries, timeouts, rate limits, flags, guards), also look in git for incident traces: messages like "fix for incident" or "add defensive check", and a revert followed by a re-apply.

If `gh` is missing or not authenticated, or the repo has no GitHub remote, say so and count it as a gap.

Always say in your answer what you searched and what you skipped. Narrow is a scoping choice you report, not a silent one.

**Wide (when git leaves the answer at Inferred or below, or the user asks for a thorough sweep).** You may run a scoped wide pass on the one or two most relevant categories and report the rest as skipped by choice. For a full sweep, list the MCP servers in this session (tools named `mcp__<server>__*`, including deferred ones). Server names are often opaque IDs, so classify each by its server instructions and tool names, not the name alone. Map each to one evidence category in `reference/sources.md`: issue tracker, long-form docs, team chat, infrastructure observability, error tracking, product analytics warehouse. Spawn one investigator per matched category in a single message:

- `subagent_type`: `Explore` (no file edits), or `general-purpose` if you need it to run queries
- `model`: `sonnet`
- Prompt: the investigator brief in `reference/why.md` (the section under the `---`), the matching playbook from `reference/sources.md`, the code anchor, and the question. Name the exact MCP tools it should load, for example `ToolSearch select:mcp__x__search,mcp__x__get`. If the target looks defensive (null checks, retries, timeouts, rate limits, feature flags, guards), add the incident angle from the same file.
- One investigator owns one category. Cross-source links go back to you as leads, not chased.
- Tell each investigator to write nothing and change nothing in any system. Nothing enforces that except the instruction.

In a full sweep, skip a category only when no MCP covers it (a gap) or it is provably irrelevant (a build script has no runtime errors). Either way, say so in your answer.

Then weigh the evidence yourself. Spot-check any citation you will lean on before you state it.

## Teaching rules

1. **Start with a plain definition.** Name the thing and say what it is in general terms, the way a senior engineer would say it out loud, with its common name if it has one. Then tie it to the case in front of you ("in X, we use this to ...") and build from there: how it works, the deeper reasons, the edge cases. For each part, explain the idea so it clicks: the problem it solves and how it works. Walk through what happens as the person does the thing (opens a long chat, scrolls up) when that makes it land. Listing functions and constants is reference, not teaching. Give the smallest complete answer first, a sentence or two, then stop. Add layers when they ask. Never a wall of text.

2. **Keep the confidence language from Why intact.** Its hedges are findings, not style. "This exists because X" needs a citation next to it. "It appears" and "likely" mark your inference. When the record is silent, say what you searched and that you found nothing. If the person's question carries a guess ("I assume it's for performance?"), check it against the evidence. Don't confirm it by default. These rules govern claims about why (intent, history, decisions), not descriptions of what the code does. A mechanism sentence like "it re-renders because the key changed" needs no citation. Everything else you can reword freely for teaching.

3. **Keep it a conversation, not a lecture or a performance.** Offer to go deeper or move on, and follow their lead. No quizzes. No pacing theater. Don't print "Pause", don't ask them to say it back, and don't flag a part as important or hard. Just say it. When you would pause, stop and let them respond. Don't print framing labels ("the key insight", "at its core", "TL;DR"). Don't echo the structure of these steps as headers. If there is no live human, deliver it cleanly and put the offer to go deeper at the end.

4. **Show, don't only tell, and build the picture up diagram by diagram.** Open the diff, the code, or the debugger when that is the fastest way to land it. Draw when a picture lands faster than words. For anything with three or more moving parts, never draw one diagram with all of them. Draw a short series where each diagram redraws the last and adds one part, so the reader watches the system assemble. To teach A to B to C, draw it three times: A to B, then A to B to C, then add the return edge or the next piece. A single all-at-once diagram saved for the end is a reference, not teaching. Use a mermaid block for a flow or structure where labels carry the meaning, or ASCII for something small. When the idea is spatial (layout, overlap, scroll position, before and after) and this session offers a visual tool such as an artifact or inline widget, use it. Otherwise describe the layout in a plain ASCII sketch. The build-up rule holds there too. A single simple point needs no figure.

5. **Follow the `unslop` skill's rules** (load it once if installed; the name may be namespaced) and write in plain spoken English, the way you'd explain it to a colleague. Be tight, not terse. Cut filler hedging, but never the evidence hedges from rule 2. Keep the part that makes it click. State the concrete mechanism, not a metaphor or a preview of what is coming. Say "`UserService` calls `AuthClient.refresh()`", not "the service delegates to the client". Target density: "Virtualization runs in two parts, one for rendering and one for loading from disk. When an item scrolls out past the buffer, both its DOM node and its in-memory data are evicted." Normal sentence case. No em dashes. Prefer periods over commas, and keep each sentence to one or two commas. Give each concept one name and keep it. Avoid mirror sentences ("A without B, or B without A") and tidy closers ("the rest follows"). The words in these steps are directions to you, not labels to print.

## If they're about to change the code

When the question comes right before an edit, end with the lineage turned into constraints: what to **preserve**, what is safe to **change**, what to **avoid**, and the **risks**. Add where to start in the code. Keep it short and cite what each one rests on.

## Reply

The explanation itself, never a report about what you did or delivered. Lead with the main point, then the plain account of what it is, how it works, and why. End with the threads worth pulling next. Always say what was searched. After a wide Why, give one line per source, including the ones that came back empty, and one sentence on overall confidence.
