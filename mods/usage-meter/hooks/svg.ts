// Desktop drawings for the Usage pane. SVGs render as images, so colors follow
// prefers-color-scheme inside each drawing instead of the app's CSS variables.
import type { CompactState } from './compact'

const W = 520

const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!)

const STYLE = `<style>
  .bg{fill:#f6f6f4}.line{stroke:#e2e1dc}.track{fill:#e7e6e1}
  .t{fill:#1f1f1d;font:600 13px system-ui,sans-serif}.big{fill:#1f1f1d;font:600 22px system-ui,sans-serif}
  .lbl{fill:#6b6a65;font:12px system-ui,sans-serif}.sm{fill:#6b6a65;font:11px system-ui,sans-serif}
  .ok{fill:#2e9e5b}.warn{fill:#c98a14}.mute{fill:#8d8c86}.bad{fill:#c4513d}.blue{fill:#3b82c4}
  @media (prefers-color-scheme: dark){
    .bg{fill:#262624}.line{stroke:#3a3a37}.track{fill:#3a3a37}
    .t,.big{fill:#ecebe6}.lbl,.sm{fill:#a3a29c}
  }
</style>`

const svg = (h: number, body: string) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${h}" width="${W}" height="${h}">${STYLE}<rect class="bg" x="0.5" y="0.5" width="${W - 1}" height="${h - 1}" rx="10"/>${body}</svg>`

// A labelled meter: label on the left, value on the right, bar underneath.
function meter(x: number, y: number, w: number, label: string, share: number, cls: string) {
  const p = Math.max(0, Math.min(1, share))
  return `<text class="lbl" x="${x}" y="${y}">${esc(label)}</text>
<text class="t" x="${x + w}" y="${y}" text-anchor="end">${Math.round(p * 100)}%</text>
<rect class="track" x="${x}" y="${y + 7}" width="${w}" height="6" rx="3"/>
<rect class="${cls}" x="${x}" y="${y + 7}" width="${Math.max(p > 0 ? 6 : 0, w * p)}" height="6" rx="3"/>`
}

const COMPACT: Record<CompactState, { word: string; cls: string }> = {
  'not-needed': { word: 'Not needed', cls: 'mute' },
  'next-break': { word: 'At your next break', cls: 'warn' },
  now: { word: 'Now', cls: 'ok' },
  avoid: { word: 'Not now, cache expired', cls: 'bad' },
}

export function summaryCard(s: {
  cost: string
  hitShare: number
  contextShare: number
  contextLabel: string
  compact: CompactState
  cache?: string
  progress?: string
}) {
  const c = COMPACT[s.compact]
  const col = (W - 48) / 3
  const cache = s.cache
    ? `<text class="lbl" x="${W - 20}" y="116" text-anchor="end">Cache <tspan class="t">${esc(s.cache)}</tspan></text>`
    : ''
  const prog = s.progress ? `<text class="sm" x="20" y="150">${esc(s.progress)}</text>` : ''
  return svg(
    s.progress ? 168 : 140,
    `<text class="lbl" x="20" y="32">Session cost</text>
<text class="big" x="20" y="60">${esc(s.cost)}</text>
${meter(16 + col + 8, 32, col - 12, 'Cache hits', s.hitShare, 'ok')}
${meter(16 + 2 * col + 16, 32, col - 12, s.contextLabel, s.contextShare, 'blue')}
<line class="line" x1="20" x2="${W - 20}" y1="84" y2="84"/>
<text class="lbl" x="20" y="116">Compact</text>
<circle class="${c.cls}" cx="86" cy="112" r="5"/>
<text class="t" x="98" y="116">${esc(c.word)}</text>${cache}${prog}`,
  )
}

export function agentCard(a: {
  title: string
  subtitle: string
  status?: string
  cost: string
  hitShare: number
  contextShare?: number
}) {
  const half = (W - 48) / 2
  const ctx = a.contextShare === undefined ? '' : meter(36 + half, 88, half - 4, 'Context used', a.contextShare, 'blue')
  const status = a.status ? `<text class="sm" x="${W - 20}" y="52" text-anchor="end">${esc(a.status)}</text>` : ''
  return svg(
    120,
    `<text class="t" x="20" y="30">${esc(a.title.length > 58 ? a.title.slice(0, 57) + '…' : a.title)}</text>
<text class="t" x="${W - 20}" y="30" text-anchor="end">${esc(a.cost)}</text>
<text class="sm" x="20" y="52">${esc(a.subtitle)}</text>${status}
${meter(20, 88, half - 4, 'Cache hits', a.hitShare, 'ok')}${ctx}`,
  )
}
