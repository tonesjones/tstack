# Tokenomics: the cost model

Read this only when it's unclear whether delegating a task pays off.

## Prices (per million tokens, Claude API list prices)

| Model | Input | Output | Cache read | Cache write (5 min / 1 h) |
|---|---:|---:|---:|---:|
| Opus 5.5 | $4.00 | $20.00 | $0.20 | $5.00 / $8.00 |
| Sonnet 5.5 | $2.00 | $10.00 | $0.20 | $2.50 / $4.00 |
| Haiku 5.5, prompt ≤ 100K tokens | $0.10 | $0.50 | $0.01 | $0.125 / $0.20 |
| Haiku 5.5, prompt > 100K tokens | $0.50 | $2.50 | $0.05 | $0.625 / $1.00 |

Opus and Sonnet rows as of 2026-09. Haiku 5.5 rows from the claude-api skill's
model table and migration guide (checked 2026-10-07): cache read is 0.1x the
input rate, 5-minute cache write 1.25x, 1-hour write 2x. Refresh from the
official pricing page (https://claude.com/pricing) when models change. On a
subscription plan these translate into usage-limit consumption rather than
dollars, but the ratios still hold.

## Cache facts that drive routing

- **Caches are per model and per prefix.** A subagent never reuses the main
  session's cache. It pays to write its own system prompt, tool schemas,
  CLAUDE.md, and brief before doing any work. Count on a few thousand to ~10K
  tokens of fixed overhead per spawn.
- **Switching the main session's model cold-starts everything.** The whole
  conversation is re-written to cache at the new model's write price. Use
  subagents, never `/model`, to reach cheaper tiers mid-task.
- **Warm re-reads are cheap.** Opus reads its cached context at $0.20/MTok, the
  same as Sonnet's cache read. Re-reading what Opus already holds is not the
  expensive part.
- **But context is re-read every turn.** Anything that lands in the main
  context (file contents, tool output, subagent reports) is paid for again on
  every later turn. Bulky reading done inline costs once to read and then keeps
  costing.
- **The cache expires** after its TTL, refreshed on every read. In Claude Code
  on a subscription within plan usage, the main conversation gets 1 hour and
  subagents get 5 minutes. On an API key, a cloud provider, or usage credits,
  both get 5 minutes. `promptCacheTtl` and `subagentPromptCacheTtl` override
  either (https://code.claude.com/docs/en/prompt-caching, checked 2026-10-05).
  A session idle past its TTL pays the write price again on its next turn.
- **Break-even for Sonnet.** With a few thousand to ~10K tokens of cold
  overhead per spawn, delegating to Sonnet starts to pay above about 3K tokens
  written or 6K tokens of new input read. Below both, keep the task in the
  main session.
- **Break-even for Haiku.** Haiku 5.5 reads fresh input at $0.10/MTok, half of
  what Opus pays to re-read its own cache. A 10K-token cold start costs about
  $0.001. What's left is Main's side: the brief Opus writes at $20/MTok and the
  report it re-reads every later turn. Delegate when the brief is clearly
  shorter than doing the work inline.
- **Minimum cacheable prefix** is 512 tokens on Opus 5.5, Sonnet 5.5, and
  Haiku 5.5. Shorter prefixes silently don't cache.

## Haiku 5.5 specifics

- **Price cliff at 100K prompt tokens.** A request whose prompt is over 100K
  tokens is billed at the higher row, 5x per token. A subagent's prompt grows
  with every file it reads and every turn it takes, so a long Haiku run can
  cross the line partway through. The skill caps Haiku packages at about 60K
  tokens of reading to stay clear of it.
- **Tokenizer.** Haiku 5.5 counts the same text as about 30% more tokens than
  Main's estimate. Size estimates in the routing table use Main's count; the
  cap allows for the difference.
- **Effort.** Thinking tokens bill as output. Going from low to medium effort
  more than doubles output tokens per attempt (claude-api migration guide). At
  $0.50/MTok that rarely matters; pick the level for quality, not price.

## Break-even rule of thumb

Delegate when the task's **new input + output** is large compared to a
subagent's fixed overhead (cold prefix + brief + returned summary). Keep it
inline when the task is small or its inputs are already in the main context.

Inline Opus cost ≈ new input × $4–5 + output × $20 + (growth of the main context × $0.20 × remaining turns)

Subagent cost ≈ (overhead + new input) × tier input price + output × tier output price + brief written by Opus × $20 + Opus review

For Haiku, multiply the subagent's token counts by about 1.3 for the tokenizer.

## Worked examples

**Bulk task: read ~40K tokens of files, write ~5K tokens.**
- Inline Opus: ~$0.20 to read + ~$0.10 to write ≈ **$0.30**. The 45K then stays
  in context: about another $0.01 per later turn, roughly $0.27 more over 30 turns.
- Sonnet `worker`: ~50K input incl. overhead ≈ $0.10–0.13, 5K output ≈ $0.05,
  brief and ~300-token report ≈ $0.01 ≈ **$0.17**, and the main context grows by
  only the report.
- Haiku `grunt`: ~65K tokens by Haiku's count, written to cache and re-read over
  its turns ≈ $0.015, ~6.5K output ≈ $0.003, brief and report ≈ $0.01 ≈
  **$0.03**. A third of that is Main's brief and report. Only if the task is
  pattern-following and objectively checkable.

**Search: find every caller of a function, ~12K tokens of grep output and excerpts, 5-line answer.**
- Inline Opus: ~$0.05 to read, then the 12K stays in context: about
  $0.07 more over 30 turns ≈ **$0.12**.
- Haiku `Explore`: ~26K tokens incl. overhead ≈ $0.005, ~100-token brief ≈
  $0.002, ~150-token report re-read for 30 turns ≈ $0.001 ≈ **$0.01**. Haiku
  wins by about 10x, and Main's context stays small.

**Small task: a 20-line edit in a file already in context.**
- Inline Opus: ~300 output tokens ≈ **$0.006**.
- Haiku `scout`: ~200-token brief ≈ $0.004, plus the subagent re-reading the
  file and a report ≈ **$0.006+**. A tie at best, and inline needs no review.
  On Sonnet the cold start alone adds ~$0.02. Inline wins.

**Escalation:** a Haiku attempt that fails and is redone by Sonnet costs both
runs plus Main's review of the failure. On Haiku 5.5 the failed run itself is
cheap; the waste is Main's second brief, the review, and the delay. Route down
only when "done when" is objective.
