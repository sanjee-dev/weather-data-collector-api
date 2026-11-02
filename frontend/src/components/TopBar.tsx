import { Menu } from 'lucide-react'
import { api, API_BASE_URL } from '../services/api'
import { useAsync } from '../hooks/useAsync'

export function TopBar({ title, onMenu }: { title: string; onMenu: () => void }) {
  const health = useAsync(() => api.health(), 'health')
  const status = health.loading ? 'checking' : health.data?.status === 'ok' ? 'online' : 'offline'
  const styles = {
    checking: ['bg-amber-400', 'Checking API…'],
    online: ['bg-emerald-400', 'API online'],
    offline: ['bg-rose-400', 'API offline'],
  } as const

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-white/10 bg-ink-950/70 px-4 backdrop-blur-md sm:px-6">
      <button
        type="button"
        onClick={onMenu}
        className="rounded-lg p-2 text-slate-300 hover:bg-white/5 lg:hidden"
        aria-label="Open menu"
      >
        <Menu className="size-5" />
      </button>
      <p className="text-sm font-medium text-slate-300">{title}</p>

      <button
        type="button"
        onClick={health.reload}
        title={`Backend: ${API_BASE_URL} (click to re-check)`}
        className="ml-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/10"
      >
        <span className={`size-2 rounded-full ${styles[status][0]}`} aria-hidden />
        <span role="status">{styles[status][1]}</span>
      </button>
    </header>
  )
}
