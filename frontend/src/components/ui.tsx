import { AlertTriangle, Inbox, RefreshCw } from 'lucide-react'
import type { ComponentType, ReactNode } from 'react'
import type { ApiError } from '../services/api'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`glass p-5 ${className}`}>{children}</section>
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle: string
  action?: ReactNode
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">{title}</h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-400">{subtitle}</p>
      </div>
      {action}
    </div>
  )
}

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = 'accent',
}: {
  label: string
  value: string | number
  hint?: string
  icon: ComponentType<{ className?: string; 'aria-hidden'?: boolean }>
  tone?: 'accent' | 'good' | 'bad' | 'warn'
}) {
  const tones = {
    accent: 'text-sky-300 bg-sky-400/10',
    good: 'text-emerald-300 bg-emerald-400/10',
    bad: 'text-rose-300 bg-rose-400/10',
    warn: 'text-amber-300 bg-amber-400/10',
  }
  return (
    <div className="glass lift p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{label}</p>
        <span className={`grid size-9 place-items-center rounded-lg ${tones[tone]}`}>
          <Icon className="size-4.5" aria-hidden />
        </span>
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  )
}

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode
  tone?: 'neutral' | 'live' | 'good' | 'bad'
}) {
  const tones = {
    neutral: 'bg-white/5 text-slate-300 border-white/10',
    live: 'bg-sky-400/10 text-sky-300 border-sky-400/30',
    good: 'bg-emerald-400/10 text-emerald-300 border-emerald-400/30',
    bad: 'bg-rose-400/10 text-rose-300 border-rose-400/30',
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  )
}

export function LoadingBlock({ rows = 3, label = 'Loading…' }: { rows?: number; label?: string }) {
  return (
    <div role="status" aria-live="polite" className="space-y-3">
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton h-16" />
      ))}
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  return (
    <div role="alert" className="glass border-rose-400/30! p-5">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 size-5 shrink-0 text-rose-300" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="font-medium text-rose-200">Something went wrong</p>
          <p className="mt-1 text-sm text-slate-300">{error.message}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-200 transition hover:bg-white/10"
            >
              <RefreshCw className="size-4" aria-hidden /> Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title: string
  message: string
  action?: ReactNode
}) {
  return (
    <div className="glass flex flex-col items-center gap-2 px-6 py-12 text-center">
      <span className="grid size-12 place-items-center rounded-full bg-white/5">
        <Inbox className="size-6 text-slate-400" aria-hidden />
      </span>
      <p className="font-medium text-white">{title}</p>
      <p className="max-w-md text-sm text-slate-400">{message}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
