import { expect, mock, test } from 'claude-code/testing'

for (const surface of ['terminal', 'desktop'] as const)
  test(`pane shows main and subagent usage on ${surface}`, async ($, on) => {
    mock.clock(on)
    on('turn.step', async function* (_$, e) {
      return {
        turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn',
        usage: { model: e.model, input_tokens: 100, output_tokens: 50, cache_read_input_tokens: 900, cache_creation_input_tokens: 0 },
      }
    })
    on('agent.list', async () => ({ value: [{ id: 'abc123', description: 'bulk edits', type: 'grunt', status: 'running' }] }))
    on('session.usage', async () => ({ value: { startedAt: 0, context: { tokens: 1000, window: 1_000_000 }, rateLimits: [], cost: { usd: 1.23 } } }))

    for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-opus-5-5', messageCount: 1 })) {}
    for await (const _ of $.turn.step({ turnId: 't2', index: 0, model: 'claude-haiku-5-5', messageCount: 1, agentId: 'abc123' })) {}

    const pane = await $.ui.mount({ plugin: 'usage-meter', surface, component: 'Pane', requestId: 'usage-meter', props: {} as never })
    const text = JSON.stringify(await pane.drawn())
    expect(text).toContain('$1.23')
    expect(text).toContain('Subagent grunt: bulk edits')
    expect(text).toContain('Haiku 5.5')
    expect(text).toContain('90%')
    expect(text).toContain('Not needed yet')
  })
