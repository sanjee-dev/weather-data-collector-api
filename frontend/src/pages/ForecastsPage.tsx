import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { ForecastCard } from '../components/ForecastCard'
import { Badge, Card, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/ui'
import { hrefFor } from '../hooks/useHashRoute'
import { primaryButton } from '../utils/styles'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import { formatDate } from '../utils/format'

export function ForecastsPage({ initialCity }: { initialCity: string }) {
  const [draft, setDraft] = useState(initialCity)
  const [city, setCity] = useState(initialCity)
  const saved = useAsync(() => api.stats(), 'stats')

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    setCity(draft.trim())
  }

  return (
    <>
      <PageHeader title="Forecasts" subtitle="Browse the forecasts that were saved in Supabase earlier." action={<Badge tone="live">● Saved data</Badge>} />

      <Card>
        <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="city" className="text-sm font-medium text-white">City</label>
            <input
              id="city"
              list="saved-cities"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Choose a saved city or type a name"
              className="mt-2 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-sky-400"
            />
            <datalist id="saved-cities">
              {saved.data?.cities.map((c) => <option key={c.city} value={c.city} />)}
            </datalist>
          </div>
          <button type="submit" className={primaryButton}><Search className="size-4" aria-hidden /> Show forecasts</button>
        </form>
        {saved.data && saved.data.cities.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2" aria-label="Saved cities">
            {saved.data.cities.map((c) => (
              <button
                key={c.city}
                type="button"
                onClick={() => { setDraft(c.city); setCity(c.city) }}
                className={`rounded-full border px-3 py-1 text-xs transition ${
                  c.city.toLowerCase() === city.toLowerCase()
                    ? 'border-sky-400/50 bg-sky-400/15 text-sky-200'
                    : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                }`}
              >
                {c.city}
              </button>
            ))}
          </div>
        )}
      </Card>

      <div className="mt-6">
        {city ? <Results key={city} city={city} /> : (
          <EmptyState title="Pick a city" message="Choose one of your saved cities above to see its forecasts." />
        )}
      </div>
    </>
  )
}

function Results({ city }: { city: string }) {
  const { data, error, loading, reload } = useAsync(() => api.forecasts(city), `forecasts:${city}`)

  if (loading) return <LoadingBlock rows={2} label={`Loading forecasts for ${city}`} />
  if (error?.status === 404) {
    return (
      <EmptyState
        title={`No saved forecasts for “${city}”`}
        message="Nothing is stored under that name yet. Collect it first, then come back."
        action={<a className={primaryButton} href={hrefFor('collect')}>Collect weather</a>}
      />
    )
  }
  if (error) return <ErrorState error={error} onRetry={reload} />
  if (!data) return null

  const first = data.forecasts[0]
  const last = data.forecasts[data.forecasts.length - 1]
  return (
    <section aria-label={`Forecasts for ${data.city}`}>
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-white">
          {data.city} <span className="font-normal text-slate-400">· {data.country}</span>
        </h2>
        <p className="text-sm text-slate-400">
          {data.count} records · {formatDate(first.date, false)} – {formatDate(last.date, false)}
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 2xl:grid-cols-7">
        {data.forecasts.map((f) => <ForecastCard key={f.date} forecast={f} />)}
      </div>
    </section>
  )
}
