// USD per million tokens. Cache writes cost 2x input on the 1-hour TTL (main session) and 1.25x on 5 minutes (subagents).
type Price = { input: number; output: number; cacheRead: number }

const PRICES: Array<[string, Price]> = [
  ['fable', { input: 10, output: 50, cacheRead: 0.25 }],
  ['mythos', { input: 10, output: 50, cacheRead: 0.25 }],
  ['opus-5-5', { input: 4, output: 20, cacheRead: 0.2 }],
  ['opus', { input: 5, output: 25, cacheRead: 0.5 }],
  ['sonnet-5', { input: 2, output: 10, cacheRead: 0.2 }],
  ['sonnet', { input: 3, output: 15, cacheRead: 0.3 }],
  ['haiku-5-5', { input: 0.1, output: 0.5, cacheRead: 0.01 }],
  ['haiku', { input: 1, output: 5, cacheRead: 0.1 }],
]

export function priceOf(model: string): Price | undefined {
  return PRICES.find(([key]) => model.includes(key))?.[1]
}

export function costOf(
  model: string,
  t: { input: number; output: number; cacheRead: number; cacheWrite: number },
  writeMultiplier = 2,
): number | undefined {
  const p = priceOf(model)
  if (!p) return undefined
  return (t.input * p.input + t.output * p.output + t.cacheRead * p.cacheRead + t.cacheWrite * p.input * writeMultiplier) / 1e6
}
