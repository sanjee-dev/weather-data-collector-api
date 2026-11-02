import { useState } from 'react'
import { ComparisonChart, PrecipitationChart, TemperatureChart } from '../components/Charts'
import { Card, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/ui'
import { hrefFor } from '../hooks/useHashRoute'
import { primaryButton } from '../utils/styles'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type { ForecastsResponse } from '../types/api'

type Metric = 'temp_max' | 'temp_min' | 'precipitation'
const METRICS: { key: Metric; label: string; unit: string }[] = [
  { key: 'temp_max', label: 'Max temperature', unit: '°C' },
  { key: 'temp_min', label: 'Min temperature', unit: '°C' },
  { key: 'precipitation', label: 'Precipitation', unit: 'mm' },
]

export function AnalyticsPage() {
  const stats = useAsync(() => api.stats(), 'stats')
  const [selected, setSelected] = useState<string[] | null>(null)

  if (stats.loading) return <><PageHeader title="Analytics" subtitle="Charts built from your saved forecasts." /><LoadingBlock rows={3} /></>
  if (stats.error) return <><PageHeader title="Analytics" subtitle="Charts built from your saved forecasts." /><ErrorState error={stats.error} onRetry={stats.reload} /></>

  const all = stats.data?.cities.map((c) => c.city) ?? []
  if (all.length === 0) {
    return (
      <>
        <PageHeader title="Analytics" subtitle="Charts built from your saved forecasts." />
        <EmptyState
          title="Nothing to chart yet"
          message="Charts use the forecasts saved in your database. Collect some weather first."
          action={<a className={primaryButton} href={hrefFor('collect')}>Collect weather</a>}
        />
      </>
    )
  }

  const chosen = selected ?? all.slice(0, 3)
  const toggle = (city: string) =>
    setSelected(chosen.includes(city) ? chosen.filter((c) => c !== city) : [...chosen, city])

  return (
    <>
      <PageHeader title="Analytics" subtitle="Every chart below is drawn from forecasts stored in Supabase (read through the backend)." />
      <Card>
        <fieldset>
          <legend className="text-sm font-medium text-white">Cities to include</legend>
          <div className="mt-3 flex flex-wrap gap-2">
            {all.map((city) => (
              <label
                key={city}
                className={`cursor-pointer rounded-full border px-3 py-1 text-xs transition has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-sky-400 ${
                  chosen.includes(city) ? 'border-sky-400/50 bg-sky-400/15 text-sky-200' : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                }`}
              >
                <input type="checkbox" className="sr-only" checked={chosen.includes(city)} onChange={() => toggle(city)} />
                {city}
              </label>
            ))}
          </div>
        </fieldset>
      </Card>
      <div className="mt-6">
        {chosen.length === 0
          ? <EmptyState title="No city selected" message="Select at least one city above." />
          : <Charts key={chosen.join('|')} cities={chosen} />}
      </div>
    </>
  )
}

function Charts({ cities }: { cities: string[] }) {
  const { data, error, loading, reload } = useAsync(
    () => Promise.all(cities.map((c) => api.forecasts(c))),
    `charts:${cities.join('|')}`,
  )
  const [focus, setFocus] = useState<string | null>(null)
  const [metric, setMetric] = useState<Metric>('temp_max')

  if (loading) return <LoadingBlock rows={2} label="Loading chart data" />
  if (error) return <ErrorState error={error} onRetry={reload} />
  if (!data) return null

  const focused: ForecastsResponse = data.find((d) => d.city === focus) ?? data[0]
  const meta = METRICS.find((m) => m.key === metric)!

  // One row per date, one column per city: [{ date, Colombo: 31, London: 12 }, ...]
  const dates = [...new Set(data.flatMap((d) => d.forecasts.map((f) => f.date)))].sort()
  const rows = dates.map((date) => {
    const row: Record<string, string | number | null> = { date }
    for (const d of data) row[d.city] = d.forecasts.find((f) => f.date === date)?.[metric] ?? null
    return row
  })

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-base font-semibold text-white">Temperature range</h2>
            <label className="flex items-center gap-2 text-xs text-slate-400">
              City
              <select value={focused.city} onChange={(e) => setFocus(e.target.value)} className="rounded-md border border-white/10 bg-ink-800 px-2 py-1 text-sm text-white">
                {data.map((d) => <option key={d.city}>{d.city}</option>)}
              </select>
            </label>
          </div>
          <TemperatureChart data={focused.forecasts} />
        </Card>
        <Card>
          <h2 className="mb-4 text-base font-semibold text-white">Precipitation · {focused.city}</h2>
          <PrecipitationChart data={focused.forecasts} />
        </Card>
      </div>

      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-semibold text-white">City comparison</h2>
          <label className="flex items-center gap-2 text-xs text-slate-400">
            Metric
            <select value={metric} onChange={(e) => setMetric(e.target.value as Metric)} className="rounded-md border border-white/10 bg-ink-800 px-2 py-1 text-sm text-white">
              {METRICS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
            </select>
          </label>
        </div>
        {data.length < 2 && <p className="mb-2 text-sm text-slate-400">Select two or more cities above to compare them.</p>}
        <ComparisonChart rows={rows} cities={data.map((d) => d.city)} unit={meta.unit} />
      </Card>
    </div>
  )
}
