// "claude-opus-5-5" becomes "Opus 5.5"; ids this does not recognize come back as they are.
const NEW_STYLE = /^claude-(opus|sonnet|haiku)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?$/
const OLD_STYLE = /^claude-(\d+)(?:-(\d{1,2}))?-(opus|sonnet|haiku)(?:-\d{8})?$/

const title = (family: string) => family[0].toUpperCase() + family.slice(1)

export function friendlyName(model: string): string {
  const a = NEW_STYLE.exec(model)
  if (a) return `${title(a[1])} ${a[3] ? `${a[2]}.${a[3]}` : a[2]}`
  const b = OLD_STYLE.exec(model)
  if (b) return `${title(b[3])} ${b[2] ? `${b[1]}.${b[2]}` : b[1]}`
  return model
}

// Version 4.5 and older (any family) have a 200k window; newer ones have 1M.
export function windowOf(model: string): number {
  const m = NEW_STYLE.exec(model)
  if (m) {
    const version = Number(m[2]) + Number(m[3] ?? 0) / 100
    return version <= 4.05 ? 200_000 : 1_000_000
  }
  if (OLD_STYLE.test(model) || /claude-(instant|2)/.test(model)) return 200_000
  return 1_000_000
}
