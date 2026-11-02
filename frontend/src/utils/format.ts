export const formatTemp = (v: number | null): string => (v === null ? '–' : `${v.toFixed(1)}°C`)

export const formatRain = (v: number | null): string => (v === null ? '–' : `${v.toFixed(1)} mm`)

// "2026-11-02" -> "Mon, 2 Nov". We force UTC so the day never shifts by timezone.
export function formatDate(iso: string, withWeekday = true): string {
  const date = new Date(`${iso}T00:00:00Z`)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat('en-GB', {
    weekday: withWeekday ? 'short' : undefined,
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  }).format(date)
}

export const MAX_CITIES = 10
export const MIN_DAYS = 1
export const MAX_DAYS = 14

/** Turn "Colombo, London\nParis" into a clean list and report problems. */
export function parseCities(input: string): { cities: string[]; error: string | null } {
  const seen = new Set<string>()
  const cities: string[] = []
  for (const part of input.split(/[,\n;]+/)) {
    const name = part.trim()
    if (!name) continue
    if (name.length > 100) {
      return { cities: [], error: `"${name.slice(0, 20)}…" is too long (max 100 characters).` }
    }
    const key = name.toLowerCase()
    if (!seen.has(key)) {
      seen.add(key)
      cities.push(name)
    }
  }
  if (cities.length === 0) return { cities, error: 'Enter at least one city name.' }
  if (cities.length > MAX_CITIES) {
    return {
      cities,
      error: `You entered ${cities.length} cities. The limit is ${MAX_CITIES} per request.`,
    }
  }
  return { cities, error: null }
}
