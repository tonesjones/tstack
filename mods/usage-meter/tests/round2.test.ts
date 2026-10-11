import { expect, mock, test } from 'claude-code/testing'

import { friendlyName, windowOf } from '../hooks/models'

const step = (model: string, input: number, output: number, cacheRead: number) => ({
  model, input_tokens: input, output_tokens: output, cache_read_input_tokens: cacheRead, cache_creation_input_tokens: 0,
})

// Mocks the engine ops the meter reads, with a live agent list and a fixed session cost.
function world(on: Parameters<Parameters<typeof test>[1]>[1], agents: Array<{ id: string; description: string; type: string; status: string }> = []) {
  let usage = step('claude-haiku-5-5', 100, 50, 900)
  on('turn.step', async function* (_$, e) {
    return {
      turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn',
      usage: { ...usage, model: e.model },
    }
  })
  on('agent.list', async () => ({ value: agents as never }))
  on('session.usage', async () => ({ value: { startedAt: 0, context: { tokens: 1000, window: 1_000_000 }, rateLimits: [], cost: { usd: 2.5 } } }))
  on('session.start', async () => ({ cwd: '/' }))
  on('command.register', async () => ({ value: undefined as never }))
  on('tool.register', async () => ({ value: undefined as never }))
  on('ui.open', async () => ({ value: { isPlaced: true } as never }))
  on('turn.complete', async () => ({ text: '' }))
  const counts = { status: 0 }
  on('ui.status', async () => { counts.status += 1; return { value: undefined as never } })
  return { counts, setUsage: (u: typeof usage) => { usage = u } }
}

async function drawn($: any, surface: 'terminal' | 'desktop', component = 'Pane') {
  const view = await $.ui.mount({ plugin: 'usage-meter', surface, component, requestId: 'usage-meter', props: (component === 'Pane' ? {} : { hasSurvey: false, isWorking: false, maxRows: 5 }) as never })
  const out = JSON.stringify(await view.drawn())
  await view.unmount()
  return out
}

test('item 1, 2, 3, 4: lifecycle, effort, context fill and friendly names', async ($, on) => {
  const clock = mock.clock(on)
  world(on)
  on('agent.spawn', async () => ({ model: 'claude-haiku-5-5', agentId: 'sub1' }))

  await $.agent.spawn({ tool_use_id: 'x', prompt: 'p', description: 'bulk edits', subagentType: 'grunt' } as never)
  await clock.advance(65_000)
  for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-haiku-5-5', effort: 'low', messageCount: 1, agentId: 'sub1' } as never)) {}
  let text = await drawn($, 'desktop')
  expect(text).toContain('Running')

  await $.turn.complete({ turnId: 't1', answer: 'ok', durationMs: 1, isAborted: false, reason: 'answer', agentId: 'sub1' } as never)
  text = await drawn($, 'desktop')
  expect(text).toContain('Done')
  expect(text).toContain('1m 5s')
  expect(text).toContain('Haiku 5.5, low effort')
  // 100 + 900 + 0 + 50 tokens over a 1M window.
  expect(text).toContain('Context used')
})

test('item 3: context fill is a percentage of the window', async ($, on) => {
  mock.clock(on)
  const w = world(on)
  w.setUsage(step('claude-haiku-4-5', 20_000, 5_000, 75_000))
  for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-haiku-4-5', messageCount: 1 } as never)) {}
  expect(await drawn($, 'terminal')).toContain('50%')
})

test('item 4: friendly model names', () => {
  expect(friendlyName('claude-opus-5-5')).toBe('Opus 5.5')
  expect(friendlyName('claude-haiku-4-5-20251001')).toBe('Haiku 4.5')
  expect(friendlyName('claude-sonnet-5')).toBe('Sonnet 5')
  expect(friendlyName('claude-3-5-haiku-20241022')).toBe('Haiku 3.5')
  expect(friendlyName('some-other-model')).toBe('some-other-model')
  expect(windowOf('claude-haiku-4-5')).toBe(200_000)
  expect(windowOf('claude-opus-5-5')).toBe(1_000_000)
})

for (const surface of ['terminal', 'desktop'] as const)
  test(`item 5 and 7: groups in order, graphics on ${surface}`, async ($, on) => {
    const clock = mock.clock(on)
    world(on)
    let n = 0
    on('agent.spawn', async () => ({ model: "claude-haiku-5-5", agentId: `a${++n}` }))
    await $.agent.spawn({ tool_use_id: 'x', prompt: 'p', description: 'first', subagentType: 'grunt' } as never)
    await $.agent.spawn({ tool_use_id: 'y', prompt: 'p', description: 'second', subagentType: 'scout' } as never)
    for await (const _ of $.turn.step({ turnId: 't0', index: 0, model: 'claude-opus-5-5', messageCount: 1 } as never)) {}
    for (const id of ['a1', 'a2'])
      for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-haiku-5-5', messageCount: 1, agentId: id } as never)) {}
    await clock.advance(5000)
    await $.turn.complete({ turnId: 't1', answer: 'x', durationMs: 1, isAborted: false, reason: 'answer', agentId: 'a1' } as never)

    const text = await drawn($, surface)
    const at = (s: string) => text.indexOf(s)
    expect(at('Main session')).toBeGreaterThan(-1)
    expect(at('Running subagents (')).toBeGreaterThan(at('Main session'))
    expect(at('Finished subagents (')).toBeGreaterThan(at('Running subagents ('))
    expect(at('Subagent scout: second')).toBeLessThan(at('Finished subagents ('))
    expect(at('Subagent grunt: first')).toBeGreaterThan(at('Finished subagents ('))
    if (surface === 'desktop') {
      expect(text).toContain('Svg')
      expect(text).toContain('Cache hits')
    } else {
      expect(text).not.toContain('Svg')
      expect(text).toContain('done')
      expect(text).toContain('5s')
    }
  })

test('item 6: one timer after a restart, ticking while an agent runs', async ($, on) => {
  const clock = mock.clock(on)
  const w = world(on)
  let n = 0
  on('agent.spawn', async () => ({ model: "claude-haiku-5-5", agentId: `a${++n}` }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
  await $.agent.spawn({ tool_use_id: 'x', prompt: 'p', description: 'd', subagentType: 't' } as never)
  const before = await drawn($, 'terminal')
  await clock.advance(3000)
  const after = await drawn($, 'terminal')
  expect(before).toContain('running, 0s')
  expect(after).toContain('running, 3s')
  // One status refresh per second means one timer, not two.
  expect(w.counts.status).toBe(3)
})

test('item 8: band shows session cost, cache and running agents', async ($, on) => {
  mock.clock(on)
  world(on)
  on('agent.spawn', async () => ({ model: 'claude-haiku-5-5', agentId: 'a1' }))
  await $.agent.spawn({ tool_use_id: 'x', prompt: 'p', description: 'd', subagentType: 't' } as never)
  for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-haiku-5-5', messageCount: 1, agentId: 'a1' } as never)) {}
  const text = await drawn($, 'terminal', 'AbovePrompt')
  expect(text).toContain('Session $2.50, cache 90%, 1 agent running')
})

test('item 9: progress tool shows in the band and pane', async ($, on) => {
  mock.clock(on)
  world(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
  const out = await $.tool.call({ tool: 'mcp__usage-meter__usage_meter_progress', tool_use_id: 'u1', title: 'Round 2', total: 5, accepted: 3, phase: 'build' } as never)
  expect(JSON.stringify(out)).toContain('3 of 5 tasks accepted')
  expect(await drawn($, 'terminal', 'AbovePrompt')).toContain('Round 2: 3 of 5 tasks accepted, phase build')
  expect(await drawn($, 'terminal')).toContain('Plan progress: ')
  // A later call with only some fields keeps the rest.
  await $.tool.call({ tool: 'mcp__usage-meter__usage_meter_progress', tool_use_id: 'u2', accepted: 4 } as never)
  expect(await drawn($, 'terminal', 'AbovePrompt')).toContain('4 of 5 tasks accepted')
})
