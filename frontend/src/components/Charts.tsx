import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DailyForecast } from '../types/api'
import { formatDate } from '../utils/format'

const AXIS = { stroke: '#94a3b8', fontSize: 12 }
const GRID = 'rgba(255,255,255,0.08)'
const TOOLTIP = {
  contentStyle: {
    background: '#0b1020',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 10,
    color: '#e2e8f0',
  },
  labelStyle: { color: '#e2e8f0', fontWeight: 600 },
}

const SERIES_COLORS = ['#38bdf8', '#fb923c', '#a78bfa', '#34d399', '#f472b6', '#facc15']

// Temperature axes zoom in on the data instead of always starting at 0°.
const TEMP_DOMAIN: [(min: number) => number, (max: number) => number] = [
  (min) => Math.floor(min - 2),
  (max) => Math.ceil(max + 2),
]

const tickDate = (v: string) => formatDate(v, false)

export function TemperatureChart({ data }: { data: DailyForecast[] }) {
  return (
    <div className="h-72 w-full" role="img" aria-label="Line chart of daily maximum and minimum temperature">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tickFormatter={tickDate} {...AXIS} />
          <YAxis unit="°" domain={TEMP_DOMAIN} {...AXIS} />
          <Tooltip {...TOOLTIP} labelFormatter={(v) => formatDate(String(v))} formatter={(v) => `${v}°C`} />
          <Legend />
          <Line type="monotone" dataKey="temp_max" name="Max temp" stroke="#fb923c" strokeWidth={2.5} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="temp_min" name="Min temp" stroke="#60a5fa" strokeWidth={2.5} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function PrecipitationChart({ data }: { data: DailyForecast[] }) {
  return (
    <div className="h-72 w-full" role="img" aria-label="Bar chart of daily precipitation in millimetres">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tickFormatter={tickDate} {...AXIS} />
          <YAxis unit=" mm" {...AXIS} />
          <Tooltip {...TOOLTIP} labelFormatter={(v) => formatDate(String(v))} formatter={(v) => `${v} mm`} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
          <Bar dataKey="precipitation" name="Precipitation" fill="#34d399" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** One line per city. `rows` looks like [{ date: "2026-11-02", Colombo: 31, London: 12 }, ...]. */
export function ComparisonChart({
  rows,
  cities,
  unit,
}: {
  rows: Record<string, string | number | null>[]
  cities: string[]
  unit: string
}) {
  return (
    <div className="h-80 w-full" role="img" aria-label={`Line chart comparing ${cities.join(', ')}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tickFormatter={tickDate} {...AXIS} />
          <YAxis unit={unit === '°C' ? '°' : ` ${unit}`} domain={unit === '°C' ? TEMP_DOMAIN : [0, 'auto']} {...AXIS} />
          <Tooltip {...TOOLTIP} labelFormatter={(v) => formatDate(String(v))} formatter={(v) => `${v}${unit === '°C' ? '°C' : ` ${unit}`}`} />
          <Legend />
          {cities.map((city, i) => (
            <Line
              key={city}
              type="monotone"
              dataKey={city}
              stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
              strokeWidth={2.5}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
