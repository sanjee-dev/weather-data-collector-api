import { BarChart3, CalendarDays, CloudSun, LayoutDashboard, CloudDownload, X } from 'lucide-react'
import type { ComponentType } from 'react'
import { hrefFor, type RouteName } from '../hooks/useHashRoute'

const NAV: { name: RouteName; label: string; icon: ComponentType<{ className?: string }> }[] = [
  { name: 'overview', label: 'Overview', icon: LayoutDashboard },
  { name: 'collect', label: 'Collect Weather', icon: CloudDownload },
  { name: 'forecasts', label: 'Forecasts', icon: CalendarDays },
  { name: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export function Sidebar({
  active,
  open,
  onClose,
}: {
  active: RouteName
  open: boolean
  onClose: () => void
}) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-white/10 bg-ink-900/95 backdrop-blur transition-transform duration-200 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Main navigation"
      >
        <div className="flex h-16 items-center justify-between px-5">
          <a href={hrefFor('overview')} className="flex items-center gap-2.5" onClick={onClose}>
            <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-sky-400 to-indigo-500">
              <CloudSun className="size-5 text-white" aria-hidden />
            </span>
            <span className="text-sm font-semibold leading-tight text-white">
              Weather
              <br />
              <span className="font-normal text-slate-400">Data Collector</span>
            </span>
          </a>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-400 hover:bg-white/5 lg:hidden"
            onClick={onClose}
            aria-label="Close menu"
          >
            <X className="size-5" />
          </button>
        </div>

        <nav className="mt-2 flex-1 space-y-1 px-3">
          {NAV.map(({ name, label, icon: Icon }) => {
            const isActive = name === active
            return (
              <a
                key={name}
                href={hrefFor(name)}
                onClick={onClose}
                aria-current={isActive ? 'page' : undefined}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/25'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                <Icon className="size-4.5" />
                {label}
              </a>
            )
          })}
        </nav>

        <p className="px-5 pb-5 text-xs text-slate-500">Data: Open-Meteo · Storage: Supabase</p>
      </aside>
    </>
  )
}
