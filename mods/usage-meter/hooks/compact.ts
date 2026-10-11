// Main-conversation cache TTL on a Claude subscription within plan usage; it drops to 5 minutes on usage credits.
export const CACHE_TTL_MS = 60 * 60_000
// Below this the context is cheap to keep; above SOON it is worth compacting at the next break.
export const LARGE_TOKENS = 150_000
export const SOON_TOKENS = 400_000
// Warn this long before the cache expires, so a compact can still read it.
export const EXPIRY_WARNING_MS = 10 * 60_000

// Auto-compact this long before the cache expires: late enough that you are likely away, early enough to read the warm cache.
export const AUTO_COMPACT_LEFT_MS = 5 * 60_000
export const AUTO_COMPACT_INSTRUCTIONS =
  'Keep the current task, its plan and progress, open decisions, and the paths of files being edited.'

// What to do about compacting, shown as a label: `now` (green), `next-break` (amber), `not-needed`, `avoid` (cache expired).
export type CompactState = 'not-needed' | 'next-break' | 'now' | 'avoid'

// cacheLeftMs is undefined until the main session has made a request.
export type Advice = { level: 'none' | 'large' | 'soon'; isGoodTime: boolean; state: CompactState; text: string; cacheLeftMs?: number }

const k = (n: number) => `${Math.round(n / 1000)}k`

// "42 min left" while there is time to spare, "4:05 left" in the last 10 minutes.
export function cacheCountdown(leftMs: number | undefined): string | undefined {
  if (leftMs === undefined) return undefined
  if (leftMs <= 0) return 'Expired'
  if (leftMs >= EXPIRY_WARNING_MS) return `${Math.ceil(leftMs / 60_000)} min left`
  const secs = Math.ceil(leftMs / 1000)
  return `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')} left`
}

// /compact reads the whole history: cheap while the cache is warm, full price once it has expired.
export function advise(s: { contextTokens: number; idleMs: number; hasRequests: boolean; cacheReadPrice?: number }): Advice {
  return { ...adviseState(s), cacheLeftMs: s.hasRequests ? Math.max(0, CACHE_TTL_MS - s.idleMs) : undefined }
}

function adviseState(s: { contextTokens: number; idleMs: number; hasRequests: boolean; cacheReadPrice?: number }): Advice {
  const { contextTokens: tokens } = s
  const perTurn = s.cacheReadPrice ? `, about $${((tokens * s.cacheReadPrice) / 1e6).toFixed(3)} per turn from cache` : ''
  const leftMs = CACHE_TTL_MS - s.idleMs
  const minsLeft = Math.max(0, Math.ceil(leftMs / 60_000))
  const level = tokens >= SOON_TOKENS ? 'soon' : 'large'

  if (tokens < LARGE_TOKENS)
    return { level: 'none', isGoodTime: false, state: 'not-needed', text: `Not needed yet. Context is ${k(tokens)} tokens.` }
  if (s.hasRequests && leftMs <= 0)
    return {
      level,
      isGoodTime: false,
      state: 'avoid',
      text: `The cache has expired. A /compact now re-reads all ${k(tokens)} tokens at full price. If you're starting new work, use /clear instead.`,
    }
  if (s.hasRequests && leftMs <= EXPIRY_WARNING_MS)
    return { level, isGoodTime: true, state: 'now', text: `The cache expires in about ${minsLeft} min. If you're stepping away, run /compact now.` }
  return {
    level,
    isGoodTime: level === 'soon',
    state: level === 'soon' ? 'now' : 'next-break',
    text: `Context is ${k(tokens)} tokens${perTurn}. Run /compact at your next break between tasks. The cache stays warm for about ${minsLeft} min.`,
  }
}

export function shouldAutoCompact(s: { isOn: boolean; advice: Advice; isAgentRunning: boolean; alreadyDone: boolean }): boolean {
  const left = s.advice.cacheLeftMs
  return (
    s.isOn &&
    !s.isAgentRunning &&
    !s.alreadyDone &&
    s.advice.level !== 'none' &&
    left !== undefined &&
    left > 0 &&
    left <= AUTO_COMPACT_LEFT_MS
  )
}
