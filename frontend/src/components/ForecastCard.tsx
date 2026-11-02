import { Droplets, ThermometerSun, ThermometerSnowflake } from 'lucide-react'
import type { DailyForecast } from '../types/api'
import { formatDate, formatRain, formatTemp } from '../utils/format'

export function ForecastCard({ forecast }: { forecast: DailyForecast }) {
  return (
    <article className="glass lift p-4">
      <h3 className="text-sm font-semibold text-white">{formatDate(forecast.date)}</h3>
      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex items-center justify-between gap-2">
          <dt className="flex items-center gap-1.5 text-slate-400">
            <ThermometerSun className="size-4 text-orange-400" aria-hidden /> Max
          </dt>
          <dd className="whitespace-nowrap font-medium text-white">{formatTemp(forecast.temp_max)}</dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="flex items-center gap-1.5 text-slate-400">
            <ThermometerSnowflake className="size-4 text-blue-400" aria-hidden /> Min
          </dt>
          <dd className="whitespace-nowrap font-medium text-white">{formatTemp(forecast.temp_min)}</dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="flex items-center gap-1.5 text-slate-400">
            <Droplets className="size-4 text-emerald-400" aria-hidden /> Rain
          </dt>
          <dd className="whitespace-nowrap font-medium text-white">{formatRain(forecast.precipitation)}</dd>
        </div>
      </dl>
    </article>
  )
}
