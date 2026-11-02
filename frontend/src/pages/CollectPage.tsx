import { CheckCircle2, Database, Layers, Loader2, MapPin, XCircle } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { ForecastCard } from '../components/ForecastCard'
import { Card, ErrorState, PageHeader, StatCard } from '../components/ui'
import { useCollection } from '../context/CollectionContext'
import { primaryButton } from '../utils/styles'
import { hrefFor } from '../hooks/useHashRoute'
import { ApiError, api } from '../services/api'
import type { CollectResponse } from '../types/api'
import { MAX_CITIES, MAX_DAYS, MIN_DAYS, parseCities } from '../utils/format'

export function CollectPage() {
  const { setLast } = useCollection()
  const [input, setInput] = useState('')
  const [days, setDays] = useState(7)
  const [validation, setValidation] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)
  const [error, setError] = useState<ApiError | null>(null)
  const [result, setResult] = useState<CollectResponse | null>(null)

  const live = parseCities(input)
  const cityCount = live.cities.length

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const parsed = parseCities(input)
    setValidation(parsed.error)
    if (parsed.error) return

    setLoading(true)
    setError(null)
    setResult(null)
    setPendingCount(parsed.cities.length)
    try {
      // The result is only shown AFTER the backend has answered.
      const response = await api.collect(parsed.cities, days)
      setResult(response)
      setLast({ response, days, finishedAt: new Date() })
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError('Something went wrong.', 'invalid'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Collect Weather"
        subtitle={`Fetch forecasts for up to ${MAX_CITIES} cities at once. The backend downloads them from Open-Meteo, retries temporary failures, and saves them to Supabase.`}
      />

      <Card>
        <form onSubmit={onSubmit} noValidate className="grid gap-5 lg:grid-cols-[1fr_16rem]">
          <div>
            <label htmlFor="cities" className="text-sm font-medium text-white">Cities</label>
            <textarea
              id="cities"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={4}
              placeholder="Colombo, London, Tokyo"
              aria-describedby="cities-help cities-error"
              aria-invalid={validation !== null}
              disabled={loading}
              className="mt-2 w-full resize-y rounded-lg border border-white/10 bg-black/30 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-sky-400 disabled:opacity-60"
            />
            <div className="mt-1.5 flex justify-between gap-3 text-xs">
              <p id="cities-help" className="text-slate-400">Separate names with commas or new lines.</p>
              <p className={cityCount > MAX_CITIES ? 'text-rose-300' : 'text-slate-400'}>{cityCount} / {MAX_CITIES} cities</p>
            </div>
            <p id="cities-error" role="alert" className="mt-1 min-h-5 text-sm text-rose-300">{validation}</p>
          </div>

          <div className="flex flex-col justify-between gap-4">
            <div>
              <label htmlFor="days" className="flex items-center justify-between text-sm font-medium text-white">
                Forecast days <span className="text-sky-300">{days}</span>
              </label>
              <input
                id="days"
                type="range"
                min={MIN_DAYS}
                max={MAX_DAYS}
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                disabled={loading}
                className="mt-3 w-full accent-sky-400"
              />
              <div className="flex justify-between text-xs text-slate-400"><span>{MIN_DAYS}</span><span>{MAX_DAYS}</span></div>
            </div>
            <button type="submit" disabled={loading} className={primaryButton}>
              {loading ? <><Loader2 className="size-4 animate-spin" aria-hidden /> Collecting…</> : 'Start collection'}
            </button>
          </div>
        </form>
      </Card>

      {loading && (
        <Card className="mt-6">
          <div role="status" aria-live="polite">
            <p className="text-sm font-medium text-white">Waiting for the backend…</p>
            <p className="mt-1 text-sm text-slate-400">
              Fetching {pendingCount} {pendingCount === 1 ? 'city' : 'cities'} ({days} days each). Failed requests may be retried
              after 1, 2 and 4 seconds, so this can take a little while.
            </p>
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10">
              <div className="indeterminate-bar h-full w-1/4 rounded-full bg-sky-400" />
            </div>
          </div>
        </Card>
      )}

      {error && <div className="mt-6"><ErrorState error={error} /></div>}

      {result && <Results result={result} days={days} />}
    </>
  )
}

function Results({ result, days }: { result: CollectResponse; days: number }) {
  return (
    <div className="mt-6 space-y-6" aria-live="polite">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Cities requested" value={result.requested} icon={MapPin} />
        <StatCard label="Succeeded" value={result.succeeded} icon={CheckCircle2} tone="good" />
        <StatCard label="Failed" value={result.failed} icon={XCircle} tone={result.failed > 0 ? 'bad' : 'accent'} />
        <StatCard label="Records saved" value={result.total_records_saved} icon={Database} hint={`${days} days per city`} />
      </div>

      {result.failures.length > 0 && (
        <Card className="border-rose-400/30!">
          <h2 className="flex items-center gap-2 text-base font-semibold text-rose-200"><XCircle className="size-4.5" aria-hidden /> Failed cities</h2>
          <ul className="mt-3 divide-y divide-white/5">
            {result.failures.map((f) => (
              <li key={f.city} className="flex flex-wrap justify-between gap-2 py-2.5 text-sm">
                <span className="font-medium text-white">{f.city}</span>
                <span className="text-slate-300">{f.reason}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {result.successes.map((c) => (
        <Card key={c.city}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="flex items-center gap-2 text-base font-semibold text-white">
                <CheckCircle2 className="size-4.5 text-emerald-300" aria-hidden /> {c.city}
                <span className="font-normal text-slate-400">· {c.country}</span>
              </h2>
              <p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-400">
                <Layers className="size-3.5" aria-hidden /> {c.records_saved} records saved ·
                {' '}{c.latitude.toFixed(2)}, {c.longitude.toFixed(2)}
              </p>
            </div>
            <a className="text-sm text-sky-300 hover:underline" href={hrefFor('forecasts', { city: c.city })}>
              Open saved forecasts →
            </a>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4 2xl:grid-cols-7">
            {c.forecasts.map((f) => <ForecastCard key={f.date} forecast={f} />)}
          </div>
        </Card>
      ))}
    </div>
  )
}
