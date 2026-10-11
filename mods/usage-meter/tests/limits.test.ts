import { expect, test } from 'claude-code/testing'

import { drainLine, drainStep } from '../hooks/limits'

test('drain adds increases, ignores drift, and restarts from zero after a window reset', () => {
  const r1 = '2026-10-11T20:00:00Z'
  const r2 = '2026-10-12T01:00:00Z'
  let d = drainStep(undefined, { percentUsed: 30, resetsAt: r1 })
  expect(d.used).toBe(0)
  d = drainStep(d, { percentUsed: 34.5, resetsAt: r1 })
  d = drainStep(d, { percentUsed: 36, resetsAt: '2026-10-11T20:00:20Z' })
  expect(d.used).toBe(6)
  d = drainStep(d, { percentUsed: 2, resetsAt: r2 })
  expect(d.used).toBe(8)
  expect(drainLine('five_hour', d, 'in 4h 10m')).toBe('5-hour window: this session used 8%. Now at 2%, resets in 4h 10m.')
  expect(drainLine('seven_day', { used: 1.25, last: 40 })).toBe('Weekly window: this session used 1.3%. Now at 40%.')
})
