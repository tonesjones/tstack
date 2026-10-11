import { expect, test } from 'claude-code/testing'

import { advise, cacheCountdown, shouldAutoCompact } from '../hooks/compact'

test('compact advice', async () => {
  expect(advise({ contextTokens: 50_000, idleMs: 0, hasRequests: true }).state).toBe('not-needed')
  expect(advise({ contextTokens: 200_000, idleMs: 0, hasRequests: true }).state).toBe('next-break')
  expect(advise({ contextTokens: 200_000, idleMs: 61 * 60_000, hasRequests: true }).state).toBe('avoid')
  expect(advise({ contextTokens: 50_000, idleMs: 0, hasRequests: true }).level).toBe('none')
  expect(advise({ contextTokens: 200_000, idleMs: 10 * 60_000, hasRequests: true }).isGoodTime).toBe(false)
  expect(advise({ contextTokens: 200_000, idleMs: 55 * 60_000, hasRequests: true }).isGoodTime).toBe(true)
  expect(advise({ contextTokens: 200_000, idleMs: 61 * 60_000, hasRequests: true }).text).toContain('expired')
  expect(advise({ contextTokens: 500_000, idleMs: 0, hasRequests: true, cacheReadPrice: 0.2 }).text).toContain('$0.100 per turn')
})

test('cache countdown shows minutes, then m:ss in the last 10 minutes, then Expired', () => {
  expect(cacheCountdown(undefined)).toBeUndefined()
  expect(cacheCountdown(42 * 60_000)).toBe('42 min left')
  expect(cacheCountdown(4 * 60_000 + 5_000)).toBe('4:05 left')
  expect(cacheCountdown(0)).toBe('Expired')
  expect(advise({ contextTokens: 50_000, idleMs: 18 * 60_000, hasRequests: true }).cacheLeftMs).toBe(42 * 60_000)
  expect(advise({ contextTokens: 50_000, idleMs: 0, hasRequests: false }).cacheLeftMs).toBeUndefined()
})

test('auto-compact runs once, near expiry, on a large idle context', () => {
  const near = advise({ contextTokens: 200_000, idleMs: 56 * 60_000, hasRequests: true })
  const base = { isOn: true, advice: near, isAgentRunning: false, alreadyDone: false }
  expect(shouldAutoCompact(base)).toBe(true)
  expect(shouldAutoCompact({ ...base, isOn: false })).toBe(false)
  expect(shouldAutoCompact({ ...base, isAgentRunning: true })).toBe(false)
  expect(shouldAutoCompact({ ...base, alreadyDone: true })).toBe(false)
  expect(shouldAutoCompact({ ...base, advice: advise({ contextTokens: 50_000, idleMs: 56 * 60_000, hasRequests: true }) })).toBe(false)
  expect(shouldAutoCompact({ ...base, advice: advise({ contextTokens: 200_000, idleMs: 40 * 60_000, hasRequests: true }) })).toBe(false)
  expect(shouldAutoCompact({ ...base, advice: advise({ contextTokens: 200_000, idleMs: 61 * 60_000, hasRequests: true }) })).toBe(false)
})
