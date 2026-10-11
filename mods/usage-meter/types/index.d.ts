export type Tally = {
  input: number
  output: number
  cacheRead: number
  cacheWrite: number
  requests: number
}

export type AgentRow = {
  id: string
  label: string
  models: Record<string, Tally>
  status: 'running' | 'done' | 'failed'
  startedAt: number
  endedAt?: number
  effort?: string
  /** Model and size of the last step's context (input, cache reads, cache writes and output). */
  lastModel?: string
  contextTokens?: number
}

/** One plan window: percent this session used, the last reading, and when the window resets. */
export type Drain = { used: number; last: number; resetsAt?: string }

export type Progress = { title?: string; total?: number; accepted?: number; phase?: string }

declare module 'claude-code' {
  interface PluginState {
    'usage-meter': {
      rows: AgentRow[]
      lastMainAt: number
      tick: number
      progress: Progress
      autoCompact: boolean
      /** The lastMainAt value of the idle stretch already auto-compacted, so it runs once per stretch. */
      autoCompactedFor: number
      drain: Record<string, Drain>
      /** When End session was pressed; 0 while the session is live. */
      endedAt: number
    }
  }
}
