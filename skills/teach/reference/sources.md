# Source playbooks

One investigator per evidence category. Each playbook is generic. Adapt it to whichever MCP server is connected, and inspect that server's tool schema first, since tool names vary. If a server isn't authenticated or a page isn't accessible, stop and report a gap. Never make up findings.

Time-bound every query to a window around the code's ship date (about 30 days either side, wider only with a reason). Return compact summaries, not raw dumps.

| Category | Examples |
|---|---|
| [Source control and in-repo](#source-control-and-in-repo) | git, `gh` |
| [Issue tracker](#issue-tracker) | Linear, Jira, GitHub Issues, Shortcut |
| [Long-form docs](#long-form-docs) | Notion, Confluence, Google Docs |
| [Team chat](#team-chat) | Slack, Discord, Teams |
| [Infrastructure observability](#infrastructure-observability) | Datadog, Grafana, New Relic, Honeycomb |
| [Error tracking](#error-tracking) | Sentry, Rollbar, Bugsnag |
| [Product analytics warehouse](#product-analytics-warehouse) | Databricks, Snowflake, BigQuery |
| [Incident angle](#incident-angle-cross-cutting) | Cross-cutting, for defensive code |

## Source control and in-repo

Always available. The most trustworthy source, since it is tied directly to the code. The main agent covers it inline as the code anchor, so don't spawn an investigator for it. Use these commands as the checklist.

Holds: commits, PR bodies and review threads, inline comments and TODOs, ADRs, tests (names and assertions often encode the edge case), co-changed files, changelog entries, ticket IDs in messages.

```bash
git log --follow --oneline -- <file>          # history through renames
git log -S '<exact string>' -- <file>         # commits that added or removed this text
git log -G '<regex>' -- <file>                # same, for a pattern
git blame -L <start>,<end> <file>             # who and when, per line
git show <hash>                               # one commit in full
git log -1 --format=%B <hash>                 # message, to find the PR number
gh pr view <n> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews,files
```

Review comments and the `comments` and `reviews` fields are where the real signal is. Also search for ADRs (`docs/adr`), `TODO|FIXME|HACK|NOTE` near the target, and tests that reference the symbol.

Good evidence: a PR body that explains the problem, a review thread where alternatives were debated, an inline comment on a non-obvious constraint, a test named for an edge case, a commit that cites a ticket or incident.

Pitfalls:

- **Squash merges** erase branch history. Fall back to the PR body and comments.
- **Misleading messages.** "Small refactor" can hide a behavior change. Read the diff.
- **Cargo-culted patterns.** If the pattern was copied, investigate the commit it came from.
- **Bot commits** (Dependabot, Renovate, backports) rarely carry intent.

Return, for each commit, PR, or comment: exact quote, hash or PR number or file:line, author and date, direct or circumstantial.

## Issue tracker

The product and business layer: "customer X asked for this", "Q3 compliance initiative".

Holds: issues, comments, parent and sub-issues, project docs, labels (`customer-request`, `compliance`, `perf`), milestones, linked PRs.

Search:

1. Fetch tickets named in commits or PRs first, in full with comments.
2. Search by feature name, symbol, and business term. Try several phrasings.
3. Walk up to the parent. Sub-issues are tactical, parents carry the why.
4. Read attached project docs and specs.
5. Check labels and milestones for the kind of motivation and the deadline.

Pitfalls: scope drift across reopen cycles, boilerplate "Why" sections ("improve user experience" is not an answer), stale tickets (compare dates to ship date), duplicate chains (follow to the canonical ticket), inaccessible issues (a gap, not a guess).

Return: ticket ID and title, the motivation quoted verbatim, labels, parent and project, author and dates, link.

## Long-form docs

Where the why is often written out before it becomes code: PRDs, RFCs, ADRs, design-review notes, postmortems, runbooks.

Search by feature name, key symbols, author handles, error strings, and user-visible terms. Fetch full pages, because rationale is often buried mid-document. Follow child pages ("alternatives considered", appendices). Check meeting-notes databases for the decision. Check the author's personal space if one exists.

Good evidence: a "Problem statement" or "Motivation" section matching the code, "Alternatives considered", a postmortem that names the code as the fix, an ADR filled in non-trivially.

Pitfalls: docs written before implementation and never updated (cross-check the PR and flag any divergence), boilerplate, unlinked docs (broad searches help), multiple drafts (find the final one, check dates), restricted pages (a gap).

Return: title and URL, authors and last-updated date, the motivation quoted with its section, linked pages, final or draft.

## Team chat

Where real decisions often got made, especially small ones that never got a doc. Also the most ephemeral source: retention limits, archived channels, DMs not searchable.

Search:

1. Messages from the PR author around the merge date.
2. Feature name and key symbols, including casual phrasings and misspellings.
3. The PR URL or `/pull/<n>`.
4. Error strings the code handles.
5. Likely channels: engineering, project, incident, the owning team's.
6. Always fetch the whole thread. The decision often sits in the replies.

Good evidence: tradeoffs debated explicitly, an incident message describing the bug the code prevents, a reviewer question and an authoritative answer, a PM or support engineer explaining a customer ask.

Pitfalls: a retention cliff (name it), unsearchable DMs (a known miss), joking messages mistaken for decisions, single messages without their thread, auth failures (report the gap).

Return: channel, permalink, participants, dates, key quotes with attribution, what discussion it belonged to.

## Infrastructure observability

The runtime record: what production was doing when the code was written.

Holds: metrics (a metric's existence shows someone cared about that number), monitors and alerts (a threshold is frequently the answer to "why clamped at N?"), dashboards, traces and spans, logs, incident records, notebooks.

Search: find the owning service first. Look at dashboards and monitors covering the target, then at metrics around it, and note whether a metric moved near the change date. Search logs with symbols or error strings in a tight time window and aggregate rather than dump. Use spans for timeout, retry, and slow-path questions. Check incident records around the ship date.

Good evidence: a monitor whose threshold matches the constraint in the code, a dashboard built by the author, a metric spike just before the merge that settles after, an incident naming the same symbols or error strings.

Pitfalls: correlation is not causation (check neighboring PRs), a chart reflects its maker's framing, renamed or expired telemetry is a gap and not a null result, log noise at scale, and "instrumented" does not mean "caused".

Return: type, name and ID, owner and dates, the specific query, threshold, or quote, and how strong the link is.

## Error tracking

Often the direct motivation for defensive or corrective code: the exceptions, stack traces, and frequencies that pushed someone to add a check, catch, retry, or fallback. Its strength is temporal correlation, for example an issue that peaked, then vanished after the release that shipped the check.

Search: find the org and project, then search issues by the exception class the code handles, the target's function name, error strings it checks for, and its file path. For a candidate issue, read first seen, last seen, affected releases, and the frequency curve. Open a full event: does the stack trace pass through the target? Cross-reference release dates with the PR merge date. Treat any AI root-cause summaries as hypotheses, not evidence.

Pitfalls: grouping drift (a renamed frame can restart an issue under a new ID), noisy release correlation (a release holds many commits), silent upstream fixes, "resolved" as a human marker and not proof of a code fix, sampling hiding rare errors.

Return: issue ID and title, project, first and last seen, event count and sampling if known, affected releases, a verbatim stack-trace excerpt, correlation with the ship date, link, and any author comments.

## Product analytics warehouse

The product and data view: what users did, which experiments ran, where a threshold constant came from.

Holds: product event tables, usage and billing events, experiment and feature-flag exposures, system tables (query history, billing, audit), pipeline lineage. Notebooks are usually not queryable. If you suspect the rationale lives in one, name it as a gap.

Search: schemas are company-specific. Probe with `SHOW TABLES` and `DESCRIBE` before trusting a name. Time-bound every query. Prefer typed, deduplicated models over raw event tables. Patterns that pay off:

1. **Usage trajectory.** Daily counts across a window around the merge. A step from zero to steady volume right after the merge suggests the PR launched the feature. A decay to zero suggests deprecation.
2. **Guard-rail origin.** The distribution (median, p99, max) of the relevant property in the 14 days before the PR. A p99 matching the code's threshold suggests the number came from data.
3. **Experiments and flags.** Find the exposure table, then pull exposure by variant for the flag near the PR date.
4. **Expensive queries.** Query history filtered by table or symbol in a tight window can show the load that motivated a migration or rewrite.
5. **Lineage.** If the target reads a pipeline model, that model's own git history may hold the rationale. Hand that back as a lead.

Pitfalls: "instrumented" does not mean "caused", a volume step may be new logging and not new behavior (look for instrumentation PRs), schema drift over time, refresh lag on typed models, tables you never confirmed exist, retention cliffs (a gap, not "no activity").

Return: type, fully qualified table and the exact query, window, compact numeric summary, correlation with the ship date, and strength (direct, circumstantial, weak).

## Incident angle (cross-cutting)

Add this when the target looks defensive: null checks, retries, timeouts, rate limits, feature flags, egress guards, OOM handlers. Incidents often motivate such code ("we added this after the X outage"). Within your own source, look for:

- **Docs:** postmortems naming the file, feature, or error string, and their action items.
- **Tracker:** tickets labeled `incident`, `sev-*`, `postmortem-action-item`, `reliability`.
- **Chat:** incident channels around the date the code was added.
- **Git:** messages like "fix for incident", "add defensive check", or a revert followed by a re-apply.
- **Observability:** incident records, plus dashboards and monitors created as action items.
- **Error tracking:** issues whose first and last seen bracket the ship date, with stack traces through the target.
- **Analytics:** an error-classifying event that spikes in the incident window and drops after the fix.

If you find an incident link, fetch the full postmortem. Its action items tie directly to code changes. Evidence is strongest when several sources point at the same incident. Skip this angle for code that doesn't look defensive.
