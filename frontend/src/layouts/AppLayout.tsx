import { useState, type ReactNode } from 'react'
import { Sidebar } from '../components/Sidebar'
import { TopBar } from '../components/TopBar'
import type { RouteName } from '../hooks/useHashRoute'

const TITLES: Record<RouteName, string> = {
  overview: 'Overview',
  collect: 'Collect Weather',
  forecasts: 'Forecasts',
  analytics: 'Analytics',
}

export function AppLayout({ route, children }: { route: RouteName; children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false)
  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-sky-500 focus:px-3 focus:py-2 focus:text-slate-950">
        Skip to content
      </a>
      <Sidebar active={route} open={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="lg:pl-64">
        <TopBar title={TITLES[route]} onMenu={() => setMenuOpen(true)} />
        <main id="main" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
          {children}
        </main>
      </div>
    </div>
  )
}
