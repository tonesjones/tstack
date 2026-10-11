# usage-meter

usage-meter is a Claude Code mod that shows what a session costs while you work. It adds a **Usage** pane and a one-line band above the prompt. Together they show:

- The session cost, and an estimated cost for each subagent with its model, effort, and request count.
- The cache hit rate: how much of each request was read from the prompt cache instead of sent fresh.
- How full the context window is, and a countdown to when the cache expires.
- When to run `/compact`, and an automatic compact if you leave a large session idle.
- An end-of-session summary, including how much of your plan's 5-hour and weekly limits the session used.

## Why it costs almost no tokens

Every reply from the model already carries a usage report: tokens in, tokens out, cache reads, and cache writes. Claude Code also tracks the session cost and, on a subscription, your plan-limit percentages. The mod reads those figures on your machine and draws them. Showing the pane, the band, the countdown, and the summary never calls the model. A session with the mod runs the same model requests as a session without it.

The mod adds tokens in two places:

- **The `usage_meter_progress` tool.** The mod registers this tool so Claude can report plan progress, for example "3 of 5 tasks accepted". The tool's name and description go into every request, which adds under 200 tokens. Those tokens sit in the cached part of the prompt, so after the first request they cost the cache-read price. On Opus 5.5 that's $0.20 per million tokens, or about $0.00004 per request. Claude calls the tool only when it's tracking a plan, and each call adds a few dozen tokens.
- **Auto-compact.** When it runs, it makes one `/compact` request. It runs only when that request is cheaper than the alternative. See [Auto-compact while you're away](#auto-compact-while-youre-away).

## Install

The mod needs Claude Code with mod support. Clone this repository, then start Claude Code with the mod's folder:

```bash
claude --plugin-dir mods/usage-meter
```

To load the mod in every session, add the folder's full path to the `CLAUDE_CODE_PLUGIN_DIRS` environment variable.

The Usage pane opens when the session starts. If you're on API pricing, read [Set it up for your plan](#set-it-up-for-your-plan) before you rely on the compact advice.

## Set it up for your plan

The defaults match a Claude Pro subscription used within plan usage. On that plan, the main session's prompt cache lasts 1 hour and a subagent's lasts 5 minutes. On API pricing, a cloud provider, or usage credits, both caches last 5 minutes. To match those plans, change these values:

| Setting | File | Pro default | API pricing or usage credits |
|---|---|---|---|
| `CACHE_TTL_MS` | `hooks/compact.ts` | `60 * 60_000` (1 hour) | `5 * 60_000` (5 minutes), unless `promptCacheTtl` sets another value |
| `EXPIRY_WARNING_MS` | `hooks/compact.ts` | `10 * 60_000` | `2 * 60_000`, so the warning fits inside the shorter cache |
| `AUTO_COMPACT_LEFT_MS` | `hooks/compact.ts` | `5 * 60_000` | `1 * 60_000`, or turn auto-compact off |
| `writeMultiplierFor` | `hooks/register.tsx` | `2` for the main session, `1.25` for subagents | `1.25` for both |
| `PRICES` | `hooks/pricing.ts` | API list prices per million tokens, checked 2026-10-11 | Your provider's prices, if they differ |

`writeMultiplierFor` sets the price of a cache write as a multiple of the input price. A 1-hour cache write costs 2 times input, and a 5-minute write costs 1.25 times input.

The session cost at the top of the pane comes from Claude Code and needs no setup. The per-agent costs are estimates at the prices in `PRICES`. On a subscription you aren't billed per token, so treat the estimates as a way to compare agents. The Haiku 5.5 cache-read price in `PRICES` is an assumption, so check it against the current price list.

## Read the pane

The summary card at the top shows the session cost and two meters:

- **Cache hits** is the share of input tokens read from the cache. Higher is cheaper, because a cache read costs a tenth of fresh input or less.
- **Context used** is how full the main session's context window is.

Below the meters, the **Compact** row shows a colored dot and the cache countdown. The countdown reads "42 min left", then switches to minutes and seconds in the last 10 minutes ("4:05 left"), then reads "Expired". Each model request in the main session restarts the countdown, including each step Claude takes inside one reply. Subagent requests don't restart it, because subagents have their own caches.

Below the summary card, the pane shows a card for the main session and one for each subagent, split into **Running subagents** and **Finished subagents**. The band above the prompt shows the session cost, the cache hit rate, the countdown, and the number of running subagents.

## When to compact

`/compact` replaces the conversation with a summary. To write that summary, it reads the whole history. While the cache is warm that read costs the cache-read price. After the cache expires, it costs full price. The Compact dot uses this to tell you when compacting is cheap:

| Dot | Label | When | What to do |
|---|---|---|---|
| Grey | Not needed | Context under 150k tokens | Nothing. |
| Yellow | At your next break | 150k to 400k tokens, cache still warm | Run `/compact` at your next break between tasks. |
| Green | Now | 400k+ tokens with a warm cache, or 150k+ tokens with under 10 minutes of cache left | Run `/compact` now, while it reads from the cache. |
| Red | Not now, cache expired | 150k+ tokens and idle for over 60 minutes | Skip `/compact`, because it would re-read everything at full price. If you're starting new work, use `/clear` instead. |

Green means a good time to compact, not that a compact is overdue. Red appears only after an hour away. The **Context used** meter shows how close the session is to the model's limit, where Claude Code compacts on its own. The 150k and 400k thresholds are `LARGE_TOKENS` and `SOON_TOKENS` in `hooks/compact.ts`.

## Auto-compact while you're away

Auto-compact is on by default. It runs `/compact` for you once per idle stretch, when all of these are true:

- The main session's cache has 5 minutes or less left. On Pro, that means you've been idle for 55 minutes.
- The context is 150k tokens or more.
- No subagent is running.

At that moment the compact reads from the warm cache, so it costs little. Without it, your first message after the cache expires pays full price to write the whole context into the cache again. On Opus 5.5, writing a 300k-token context into the 1-hour cache costs about $2.40, at 2 times the $4 input price. Reading it from a warm cache costs about $0.06. The compact tells the summary to keep the current task, its plan and progress, open decisions, and the paths of files being edited. A toast reports the result, for example "Auto-compacted 230k to 15k tokens while you were away."

A compact loses detail, such as exact file contents and earlier wording. To keep the full history for one session, run:

```
/usage-meter auto-compact off
```

The setting lasts for the current session, and the pane shows whether auto-compact is on.

## End a session

When you're done with a session, press **End session and show summary** at the bottom of the pane. A summary appears at the top of the pane:

- How long the session ran, what it cost, and how many model requests it made.
- Each model's share of the cost and of the requests, for example "Opus 5.5: 84% of cost, 120 requests (62%)". The cost shares come from the estimates at the prices in `PRICES`.
- How much of your **5-hour window** and **Weekly window** the session used, where each window stands now, and when it resets.

Auto-compact stops after you press the button. To return to the normal pane, press **Back to live view**.

Claude Code reports the window percentages after each response, to a tenth of a percent. The mod adds up how much each window rises during the session. The session's first response isn't counted, because there's no earlier reading to compare it with. The windows are shared across your account, so other Claude sessions or chats that run at the same time count too. If a window resets during the session, the summary adds the usage from before and after the reset.

On API pricing there are no plan windows. The summary shows the run time, the cost, and the requests, and the cost is your actual spend. If you use a Claude gateway with a spend limit, the summary shows how much of that limit the session used.

## Commands

| Command | What it does |
|---|---|
| `/usage-meter` | Show or hide the Usage pane. |
| `/usage-meter auto-compact off` | Turn auto-compact off for this session. |
| `/usage-meter auto-compact on` | Turn auto-compact back on. |

## Check the mod

```bash
claude plugin validate mods/usage-meter
claude plugin test mods/usage-meter
```
