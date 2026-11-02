import { CheckCircle2, Database, MapPin, XCircle } from 'lucide-react'
import { Badge, Card, EmptyState, ErrorState, LoadingBlock, PageHeader, StatCard } from '../components/ui'
import { useCollection } from '../context/CollectionContext'
import { hrefFor } from '../hooks/useHashRoute'
import { primaryButton } from '../utils/styles'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import { formatDate } from '../utils/format'

export function OverviewPage() {
  const stats = useAsync(() => api.stats(), 'stats')
  const { last } = useCollection()

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle="Live numbers from your Supabase database, read through the FastAPI backend."
        action={<Badge tone="live">● Live data</Badge>}
      />

      {stats.loading && <LoadingBlock rows={2} label="Loading statistics" />}
      {stats.error && <ErrorState error={stats.error} onRetry={stats.reload} />}

      {stats.data && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Saved forecast records" value={stats.data.total_records} icon={Database} hint="Rows in the forecasts table" />
          <StatCard label="Cities saved" value={stats.data.total_cities} icon={MapPin} hint="Distinct cities in the database" />
          <StatCard
            label="Last collection: succeeded"
            value={last ? last.response.succeeded : '–'}
            icon={CheckCircle2}
            tone="good"
            hint={last ? `of ${last.response.requested} cities` : 'No collection in this session yet'}
          />
          <StatCard
            label="Last collection: failed"
            value={last ? last.response.failed : '–'}
            icon={XCircle}
            tone={last && last.response.failed > 0 ? 'bad' : 'accent'}
            hint={last ? `Finished ${last.finishedAt.toLocaleTimeString()}` : 'No collection in this session yet'}
          />
        </div>
      )}

      {last && (
        <Card className="mt-6">
          <h2 className="text-base font-semibold text-white">Most recent collection (this session)</h2>
          <p className="mt-1 text-sm text-slate-400">
            {last.response.requested} cities × {last.days} days →{' '}
            {last.response.total_records_saved} records saved.
            {last.response.failed > 0
              ? ` ${last.response.failed} failed: ${last.response.failures.map((f) => f.city).join(', ')}.`
              : ' Every city succeeded.'}
          </p>
        </Card>
      )}

      {stats.data && stats.data.cities.length === 0 && (
        <div className="mt-6">
          <EmptyState
            title="No forecasts saved yet"
            message="Collect weather for a few cities and the results will appear here."
            action={<a className={primaryButton} href={hrefFor('collect')}>Collect weather</a>}
          />
        </div>
      )}

      {stats.data && stats.data.cities.length > 0 && (
        <Card className="mt-6 overflow-x-auto">
          <h2 className="mb-4 text-base font-semibold text-white">Saved cities</h2>
          <table className="w-full min-w-[32rem] text-left text-sm">
            <caption className="sr-only">Cities with saved forecasts</caption>
            <thead className="text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th scope="col" className="pb-3 font-medium">City</th>
                <th scope="col" className="pb-3 font-medium">Country</th>
                <th scope="col" className="pb-3 font-medium">Records</th>
                <th scope="col" className="pb-3 font-medium">Dates</th>
                <th scope="col" className="pb-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {stats.data.cities.map((c) => (
                <tr key={c.city}>
                  <th scope="row" className="py-3 font-medium text-white">{c.city}</th>
                  <td className="py-3 text-slate-300">{c.country}</td>
                  <td className="py-3 text-slate-300">{c.records}</td>
                  <td className="py-3 text-slate-300">{formatDate(c.first_date, false)} – {formatDate(c.last_date, false)}</td>
                  <td className="py-3 text-right">
                    <a className="text-sky-300 hover:underline" href={hrefFor('forecasts', { city: c.city })}>
                      View<span className="sr-only"> forecasts for {c.city}</span>
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </>
  )
}
