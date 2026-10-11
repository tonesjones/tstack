// How much of each plan window this session used, built from the readings Claude Code reports after each response.
import type { Drain } from '../types'

export const WINDOW_NAME: Record<string, string> = { five_hour: '5-hour window', seven_day: 'Weekly window', spend_limit: 'Spend limit' }

// A resetsAt more than a minute later means the window reset mid-session, so the new reading counts from zero.
// The minute absorbs small drifts in how the reset time is reported.
export function drainStep(prev: Drain | undefined, reading: { percentUsed: number; resetsAt?: string }): Drain {
  const { percentUsed: now, resetsAt } = reading
  if (!prev) return { used: 0, last: now, resetsAt }
  if (Date.parse(resetsAt ?? '') - Date.parse(prev.resetsAt ?? '') > 60_000) return { used: prev.used + now, last: now, resetsAt }
  return { used: prev.used + Math.max(0, now - prev.last), last: now, resetsAt }
}

const pct = (n: number) => `${Math.round(n * 10) / 10}%`

export function drainLine(kind: string, d: Drain, resetText?: string): string {
  const name = WINDOW_NAME[kind] ?? kind
  return `${name}: this session used ${pct(d.used)}. Now at ${pct(d.last)}${resetText ? `, resets ${resetText}` : ''}.`
}

export type ModelUse = { cost: number; requests: number }

// "Opus 5.5: 84% of cost, 120 requests (62%)", largest cost first.
export function modelSplit(byModel: Record<string, ModelUse>): string[] {
  const entries = Object.entries(byModel)
  const cost = entries.reduce((n, [, u]) => n + u.cost, 0)
  const requests = entries.reduce((n, [, u]) => n + u.requests, 0)
  const share = (part: number, whole: number) => (whole > 0 ? Math.round((part / whole) * 100) : 0)
  return entries
    .sort(([, a], [, b]) => b.cost - a.cost)
    .map(([name, u]) => `${name}: ${share(u.cost, cost)}% of cost, ${u.requests} requests (${share(u.requests, requests)}%)`)
}
