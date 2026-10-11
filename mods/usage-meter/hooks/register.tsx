import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { AgentRow, Drain, Progress, Tally } from '../types'
import { advise, AUTO_COMPACT_INSTRUCTIONS, cacheCountdown, EXPIRY_WARNING_MS, shouldAutoCompact } from './compact'
import type { Advice } from './compact'
import { drainLine, drainStep, modelSplit } from './limits'
import type { ModelUse } from './limits'
import { agentCard, summaryCard } from './svg'
import { friendlyName, windowOf } from './models'
import { costOf, priceOf } from './pricing'

const PANE = 'usage-meter'
const PROGRESS_TOOL = 'mcp__usage-meter__usage_meter_progress'
const rows = atom({ plugin: 'usage-meter', key: 'rows' } as const, [])
const lastMainAt = atom({ plugin: 'usage-meter', key: 'lastMainAt' } as const, 0)
const tick = atom({ plugin: 'usage-meter', key: 'tick' } as const, 0)
const progress = atom({ plugin: 'usage-meter', key: 'progress' } as const, {})
const autoCompact = atom({ plugin: 'usage-meter', key: 'autoCompact' } as const, true)
const autoCompactedFor = atom({ plugin: 'usage-meter', key: 'autoCompactedFor' } as const, 0)
const drain = atom({ plugin: 'usage-meter', key: 'drain' } as const, {} as Record<string, Drain>)
const endedAt = atom({ plugin: 'usage-meter', key: 'endedAt' } as const, 0)

const EMPTY: Tally = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, requests: 0 }

const k = (n: number) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : `${n}`)
const usd = (n: number) => `$${n.toFixed(n < 0.01 ? 4 : n < 1 ? 3 : 2)}`
const hitRate = (t: Tally) => {
  const total = t.input + t.cacheRead + t.cacheWrite
  return total ? `${Math.round((t.cacheRead / total) * 100)}%` : '-'
}
const hitShare = (t: Tally) => {
  const total = t.input + t.cacheRead + t.cacheWrite
  return total ? t.cacheRead / total : 0
}
const duration = (ms: number) => {
  const s = Math.max(0, Math.round(ms / 1000))
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}
const progressText = (p: Progress) => {
  const count =
    p.accepted !== undefined && p.total !== undefined
      ? `${p.accepted} of ${p.total} tasks accepted`
      : p.accepted !== undefined
        ? `${p.accepted} tasks accepted`
        : p.total !== undefined
          ? `${p.total} tasks`
          : ''
  const text = [count, p.phase ? `phase ${p.phase}` : ''].filter(Boolean).join(', ')
  if (!text && !p.title) return ''
  return p.title ? (text ? `${p.title}: ${text}` : p.title) : text
}

// Cost, cache and request totals across every row; costs are list-price estimates.
function summarize(list: AgentRow[]) {
  let estimate = 0
  const all: Tally = { ...EMPTY }
  const costs: Record<string, number> = {}
  const byModel: Record<string, ModelUse> = {}
  for (const row of list) {
    costs[row.id] = 0
    for (const [model, t] of Object.entries(row.models)) {
      const c = costOf(model, t, writeMultiplierFor(row.id)) ?? 0
      costs[row.id] += c
      const use = (byModel[friendlyName(model)] ??= { cost: 0, requests: 0 })
      use.cost += c
      use.requests += t.requests
      estimate += c
      all.input += t.input
      all.output += t.output
      all.cacheRead += t.cacheRead
      all.cacheWrite += t.cacheWrite
      all.requests += t.requests
    }
  }
  return { estimate, all, costs, byModel }
}

const modelName = (row: AgentRow, model: string) =>
  `${friendlyName(model)}${row.effort && model === row.lastModel ? `, ${row.effort} effort` : ''}`

// A hot reload runs this module again; the old timer's stop function lives here so it can be called first.
const stash = globalThis as { __usageMeterStop?: () => void }

export const register: Register = on => {
  let isOpen = false

  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'usage-meter', description: 'Show or hide the usage meter pane; "auto-compact on|off" sets auto-compact' })
    await $.tool.register({
      name: 'usage_meter_progress',
      description:
        'Report plan progress to the usage meter, for example 3 of 5 tasks accepted. Every field is optional; fields left out keep their last value.',
      inputSchema: {
        type: 'object',
        properties: {
          title: { type: 'string', description: 'Name of the plan' },
          total: { type: 'number', description: 'Number of tasks in the plan' },
          accepted: { type: 'number', description: 'Number of tasks accepted so far' },
          phase: { type: 'string', description: 'Current phase, for example build or review' },
        },
      },
      isDeferred: false,
    })
    isOpen = true
    void $.ui.open({ id: PANE, title: 'Usage' })

    stash.__usageMeterStop?.()
    let wasGoodTime = false
    let quietSeconds = 0
    let isBusy = false
    const timer = $.clock.every(1000, () => {
      if (isBusy) return
      isBusy = true
      void (async () => {
        const list = await read($, rows)
        const a = await adviceNow($)
        quietSeconds += 1
        // Every second while an agent runs or the compact countdown matters, else once a minute.
        const isCountingDown = a.cacheLeftMs !== undefined && a.cacheLeftMs > 0 && a.cacheLeftMs < EXPIRY_WARNING_MS
        if (!list.some(r => r.status === 'running' && r.id !== 'main') && a.level === 'none' && !isCountingDown && quietSeconds < 60) return
        quietSeconds = 0
        await update($, tick, n => n + 1)
        await maybeAutoCompact($, a, list)
        if (a.isGoodTime && !wasGoodTime) $.ui.toast(a.text)
        wasGoodTime = a.isGoodTime
        clearStatus($)
      })()
        .catch(() => {})
        .finally(() => {
          isBusy = false
        })
    })
    stash.__usageMeterStop = () => timer.cancel()
    return next(e)
  })

  on('command.run', { command: 'usage-meter' }, async ($, e) => {
    const setting = e.args.trim().match(/^auto-compact\s+(on|off)$/i)
    if (setting) {
      const isOn = setting[1]?.toLowerCase() === 'on'
      await update($, autoCompact, () => isOn)
      return { text: `Auto-compact is ${isOn ? 'on' : 'off'} for this session.` }
    }
    if (isOpen) {
      await $.ui.close({ id: PANE })
      return { text: 'Usage pane hidden.' }
    }
    isOpen = true
    await $.ui.open({ id: PANE, title: 'Usage' })
    return { text: 'Usage pane shown.' }
  })

  on('ui.close', async ($, e, next) => {
    if (e.id === PANE) isOpen = false
    return next(e)
  })

  on('agent.spawn', async ($, e, next) => {
    const r = await next(e)
    if ('deny' in r || !r.agentId) return r
    const id = r.agentId
    const now = await $.clock.now()
    const label = `Subagent ${e.subagentType}: ${e.description}`
    await update($, rows, list => {
      const row: AgentRow = { id, label, models: {}, status: 'running', startedAt: now }
      return list.some(x => x.id === id) ? list.map(x => (x.id === id ? { ...x, ...row, models: x.models } : x)) : [...list, row]
    })
    return r
  })

  on('session.measure', async ($, e, next) => {
    if (e.rateLimits.length > 0)
      await update($, drain, d => {
        const merged = { ...d }
        for (const r of e.rateLimits) merged[r.kind] = drainStep(d[r.kind], r)
        return merged
      })
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    const id = e.agentId
    if (!id) return r
    const now = await $.clock.now()
    await update($, rows, list =>
      list.map(x => (x.id === id ? { ...x, status: e.reason === 'answer' ? ('done' as const) : ('failed' as const), endedAt: now } : x)),
    )
    clearStatus($)
    return r
  })

  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    const u = result.usage
    if (!u) return result

    const now = await $.clock.now()
    if (!e.agentId) await update($, lastMainAt, () => now)
    const id = e.agentId ?? 'main'
    let label = 'Main session'
    if (e.agentId) {
      const info = (await $.agent.list()).find(a => a.id === e.agentId)
      label = info ? `Subagent ${info.type}: ${info.description}` : `Subagent ${e.agentId.slice(0, 6)}`
    }
    const effort = e.effort === undefined ? undefined : String(e.effort)
    const contextTokens = u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens + u.output_tokens

    await update($, rows, list => {
      const row: AgentRow = list.find(r => r.id === id) ?? { id, label, models: {}, status: 'running', startedAt: now }
      const t = row.models[u.model] ?? EMPTY
      const merged: AgentRow = {
        ...row,
        effort: effort ?? row.effort,
        lastModel: u.model,
        contextTokens,
        models: {
          ...row.models,
          [u.model]: {
            input: t.input + u.input_tokens,
            output: t.output + u.output_tokens,
            cacheRead: t.cacheRead + u.cache_read_input_tokens,
            cacheWrite: t.cacheWrite + u.cache_creation_input_tokens,
            requests: t.requests + 1,
          },
        },
      }
      return list.some(r => r.id === id) ? list.map(r => (r.id === id ? merged : r)) : [...list, merged]
    })

    clearStatus($)
    return result
  })

  on('tool.call', { tool: PROGRESS_TOOL }, async ($, e) => {
    const num = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? Math.max(0, Math.round(v)) : undefined)
    const str = (v: unknown) => (typeof v === 'string' && v.trim() ? v.trim().slice(0, 80) : undefined)
    const patch: Progress = {}
    const title = str(e.title)
    const total = num(e.total)
    const accepted = num(e.accepted)
    const phase = str(e.phase)
    if (title !== undefined) patch.title = title
    if (total !== undefined) patch.total = total
    if (accepted !== undefined) patch.accepted = accepted
    if (phase !== undefined) patch.phase = phase
    const next = await update($, progress, p => ({ ...p, ...patch }))
    return { result: `Progress recorded: ${progressText(next) || 'nothing to show'}.` }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const list = await read($, rows)
    const prog = progressText(await read($, progress))
    if (list.length === 0 && !prog) return next(e)

    const sessionCost = (await $.session.usage()).cost?.usd
    const { estimate, all } = summarize(list)
    const running = list.filter(r => r.status === 'running' && r.id !== 'main').length
    const advice = await adviceNow($)
    const parts = [
      `Session ${sessionCost !== undefined ? usd(sessionCost) : `about ${usd(estimate)}`}`,
      hitRate(all) !== '-' ? `cache ${hitRate(all)}` : '',
      advice.cacheLeftMs !== undefined ? `cache ${cacheCountdown(advice.cacheLeftMs)!.toLowerCase()}` : '',
      running ? `${running} ${running === 1 ? 'agent' : 'agents'} running` : '',
      prog,
      advice.isGoodTime ? advice.text : '',
    ].filter(Boolean)

    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box>
        <Text color={advice.isGoodTime ? 'green' : undefined}>{parts.join(', ')}</Text>
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Text, Button } = els
    const Svg = e.surface === 'desktop' && 'Svg' in els ? els.Svg : undefined
    const list = await read($, rows)
    await read($, tick)
    const prog = progressText(await read($, progress))
    const now = await $.clock.now()
    const usage = await $.session.usage()
    const advice = await adviceNow($)
    const { estimate, all, costs, byModel } = summarize(list)
    const cost = usage.cost?.usd !== undefined ? usd(usage.cost.usd) : `about ${usd(estimate)}`

    const main = list.filter(r => r.id === 'main')
    const running = list.filter(r => r.id !== 'main' && r.status === 'running')
    const finished = list.filter(r => r.id !== 'main' && r.status !== 'running')

    // Rows seen before this version loaded have no start time, so they get no timer.
    const status = (row: AgentRow) => {
      if (row.id === 'main') return undefined
      const time = Number.isFinite(row.startedAt) ? duration((row.endedAt ?? now) - row.startedAt) : ''
      const word = row.status === 'running' ? 'Running' : row.status === 'failed' ? 'Failed' : 'Done'
      return time ? `${word}, ${time}` : word
    }
    const subtitle = (row: AgentRow) => {
      const requests = Object.values(row.models).reduce((n, t) => n + t.requests, 0)
      const models = Object.keys(row.models).map(m => modelName(row, m)).join(', ')
      return `${models}, ${requests} ${requests === 1 ? 'request' : 'requests'}`
    }
    const contextShare = (row: AgentRow) =>
      row.contextTokens !== undefined && row.lastModel ? row.contextTokens / windowOf(row.lastModel) : undefined
    const tokens = (row: AgentRow) => {
      const t = summarize([row]).all
      return `Tokens: ${k(t.input)} new input, ${k(t.output)} output, ${k(t.cacheRead)} read from cache, ${k(t.cacheWrite)} written to cache`
    }

    const card = (row: AgentRow) => {
      const title = row.id === 'main' ? 'Main session' : row.label
      const t = summarize([row]).all
      const share = contextShare(row)
      if (Svg)
        return (
          <Box flexDirection="column" gap={1}>
            <Svg
              source={agentCard({ title, subtitle: subtitle(row), status: status(row), cost: `about ${usd(costs[row.id])}`, hitShare: hitShare(t), contextShare: share })}
              alt={`${title}: ${subtitle(row)}, about ${usd(costs[row.id])}, cache hits ${hitRate(t)}`}
            />
            <Text dimColor>{tokens(row)}</Text>
          </Box>
        )
      const st = status(row)
      return (
        <Box flexDirection="column">
          <Text bold>
            {title}{st ? `, ${st.toLowerCase()}` : ''}, about {usd(costs[row.id])}
          </Text>
          <Text>
            {subtitle(row)}. Cache hits {hitRate(t)}{share !== undefined ? `, context ${Math.round(share * 100)}% used` : ''}
          </Text>
          <Text dimColor>{tokens(row)}</Text>
        </Box>
      )
    }

    const mainShare = main[0] ? contextShare(main[0]) : undefined
    const isAutoOn = await read($, autoCompact)
    const COMPACT_WORD = { 'not-needed': 'Not needed', 'next-break': 'At your next break', now: 'Now', avoid: 'Not now, cache expired' }
    const COMPACT_COLOR = { 'not-needed': undefined, 'next-break': 'yellow', now: 'green', avoid: 'red' } as const

    const ended = await read($, endedAt)
    const drains = Object.entries(await read($, drain))
    const requests = list.reduce((n, r) => n + Object.values(r.models).reduce((m, t) => m + t.requests, 0), 0)
    const resetIn = (iso?: string) => {
      const ms = iso ? Date.parse(iso) - now : NaN
      if (!Number.isFinite(ms) || ms <= 0) return undefined
      const mins = Math.round(ms / 60_000)
      return mins >= 60 ? `in ${Math.floor(mins / 60)}h ${mins % 60}m` : `in ${mins}m`
    }
    const finalSummary = ended > 0 && (
      <Box flexDirection="column" gap={1}>
        <Text bold>Session summary</Text>
        <Text>
          Ran {Math.round((ended - usage.startedAt) / 60_000)} min, cost {cost}, {requests} model requests.
        </Text>
        {modelSplit(byModel).map(line => (
          <Text key={line}>{line}</Text>
        ))}
        {drains.length > 0 ? (
          drains.map(([kind, d]) => <Text key={kind}>{drainLine(kind, d, resetIn(d.resetsAt))}</Text>)
        ) : (
          <Text dimColor>No plan window readings. A Claude subscription reports them after the first reply. API billing has no plan windows, so the cost above is the whole picture.</Text>
        )}
        <Text dimColor>
          Plan windows are shared, so these figures include any other Claude sessions or chats that ran at the same time. Start a new session for your next task.
        </Text>
      </Box>
    )

    return (
      <Box flexDirection="column" gap={2} paddingY={1}>
        {finalSummary}
        {Svg ? (
          <Svg
            source={summaryCard({
              cost,
              hitShare: hitShare(all),
              contextShare: mainShare ?? 0,
              contextLabel: 'Context used',
              compact: advice.state,
              cache: cacheCountdown(advice.cacheLeftMs),
              progress: prog || undefined,
            })}
            alt={`Session cost ${cost}, cache hits ${hitRate(all)}, compact: ${COMPACT_WORD[advice.state]}`}
          />
        ) : (
          <Box flexDirection="column">
            <Text bold>Session cost: {cost}</Text>
            <Text>Cache hits: {hitRate(all)} of input came from the cache</Text>
            {prog && <Text>Plan progress: {prog}</Text>}
            <Text color={COMPACT_COLOR[advice.state]}>Compact: {COMPACT_WORD[advice.state]}</Text>
            {advice.cacheLeftMs !== undefined && <Text>Cache: {cacheCountdown(advice.cacheLeftMs)}</Text>}
          </Box>
        )}
        <Text dimColor>{advice.text}</Text>
        <Text dimColor>
          {isAutoOn
            ? 'Auto-compact is on. It runs once you have been idle 55 min with 150k+ tokens of context. To turn it off for this session, run /usage-meter auto-compact off.'
            : 'Auto-compact is off for this session. To turn it on, run /usage-meter auto-compact on.'}
        </Text>
        {list.length === 0 && <Text dimColor>No model requests yet.</Text>}
        {main.map(card)}
        {running.length > 0 && (
          <Box flexDirection="column" gap={1}>
            <Text bold>Running subagents ({running.length})</Text>
            {running.map(card)}
          </Box>
        )}
        {finished.length > 0 && (
          <Box flexDirection="column" gap={1}>
            <Text bold>Finished subagents ({finished.length})</Text>
            {finished.map(card)}
          </Box>
        )}
        <Box justifyContent="center">
          {ended > 0 ? (
            <Button label="Back to live view" onPress={() => update($, endedAt, () => 0)} />
          ) : (
            <Button
              variant="primary"
              label="End session and show summary"
              onPress={async () => {
                const at = await $.clock.now()
                await update($, endedAt, () => at)
                await update($, tick, n => n + 1)
              }}
            />
          )}
        </Box>
        <Box>
          <Text dimColor>
            Cache hits: share of input read from the cache, higher is cheaper. Context used: how full the model's context window is. Agent costs are estimates at API list prices; the session cost comes from Claude Code.
          </Text>
        </Box>
      </Box>
    )
  })
}

async function adviceNow($: EngineInterface) {
  const usage = await $.session.usage()
  const list = await read($, rows)
  const mainModel = Object.keys(list.find(r => r.id === 'main')?.models ?? {}).at(-1) ?? ''
  return advise({
    contextTokens: usage.context.tokens ?? 0,
    idleMs: (await $.clock.now()) - (await read($, lastMainAt)),
    hasRequests: (await read($, lastMainAt)) > 0,
    cacheReadPrice: priceOf(mainModel)?.cacheRead,
  })
}

// The band above the prompt shows the session figures, so the status line stays empty.
function clearStatus($: EngineInterface) {
  $.ui.status(undefined)
}

const writeMultiplierFor = (agentId: string) => (agentId === 'main' ? 2 : 1.25)

async function maybeAutoCompact($: EngineInterface, advice: Advice, list: AgentRow[]) {
  const stretch = await read($, lastMainAt)
  const isReady = shouldAutoCompact({
    isOn: await read($, autoCompact),
    advice,
    isAgentRunning: list.some(r => r.status === 'running' && r.id !== 'main'),
    alreadyDone: (await read($, autoCompactedFor)) === stretch,
  })
  if (!isReady || (await read($, endedAt)) > 0) return
  await update($, autoCompactedFor, () => stretch)
  const before = (await $.session.usage()).context.tokens ?? 0
  const result = await $.session.compact({ instructions: AUTO_COMPACT_INSTRUCTIONS })
  if ('skip' in result) return
  const after = (await $.session.usage()).context.tokens ?? 0
  $.ui.toast(`Auto-compacted ${Math.round(before / 1000)}k to ${Math.round(after / 1000)}k tokens while you were away.`)
}
