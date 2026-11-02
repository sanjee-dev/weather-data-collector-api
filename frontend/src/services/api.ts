import type {
  CollectResponse,
  ForecastsResponse,
  HealthResponse,
  StatsResponse,
} from '../types/api'

/** Backend address. Set VITE_API_BASE_URL in frontend/.env (see .env.example). */
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
).replace(/\/+$/, '')

export type ApiErrorKind = 'network' | 'timeout' | 'http' | 'invalid'

export class ApiError extends Error {
  kind: ApiErrorKind
  status: number | null

  constructor(message: string, kind: ApiErrorKind, status: number | null = null) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
  }
}

// --- small runtime checks: we do not blindly trust the shape of the response ---

type Json = Record<string, unknown>
const isObject = (v: unknown): v is Json => typeof v === 'object' && v !== null
const isArray = Array.isArray

const isCollectResponse = (v: unknown): v is CollectResponse =>
  isObject(v) &&
  typeof v.requested === 'number' &&
  typeof v.succeeded === 'number' &&
  typeof v.failed === 'number' &&
  typeof v.total_records_saved === 'number' &&
  isArray(v.successes) &&
  isArray(v.failures)

const isForecastsResponse = (v: unknown): v is ForecastsResponse =>
  isObject(v) && typeof v.city === 'string' && typeof v.count === 'number' && isArray(v.forecasts)

const isStatsResponse = (v: unknown): v is StatsResponse =>
  isObject(v) &&
  typeof v.total_records === 'number' &&
  typeof v.total_cities === 'number' &&
  isArray(v.cities)

const isHealth = (v: unknown): v is HealthResponse => isObject(v) && typeof v.status === 'string'

/** FastAPI sends errors as {"detail": "text"} or {"detail": [{"msg": "..."}]}. */
function readDetail(body: unknown, fallback: string): string {
  if (isObject(body)) {
    const detail = body.detail
    if (typeof detail === 'string') return detail
    if (isArray(detail)) {
      const messages = detail
        .map((d) => (isObject(d) && typeof d.msg === 'string' ? d.msg : null))
        .filter((m): m is string => m !== null)
      if (messages.length > 0) return messages.join('; ')
    }
  }
  return fallback
}

async function request<T>(
  path: string,
  guard: (value: unknown) => value is T,
  init: RequestInit = {},
  timeoutMs = 60_000,
): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('The server took too long to answer.', 'timeout')
    }
    throw new ApiError(
      `Cannot reach the backend at ${API_BASE_URL}. Is it running, and is CORS_ORIGINS set correctly?`,
      'network',
    )
  } finally {
    clearTimeout(timer)
  }

  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    throw new ApiError(
      readDetail(body, `The server answered with HTTP ${response.status}.`),
      'http',
      response.status,
    )
  }
  if (!guard(body)) {
    throw new ApiError('The server sent data in an unexpected format.', 'invalid', response.status)
  }
  return body
}

export const api = {
  health: () => request('/health', isHealth, {}, 8_000),

  collect: (cities: string[], days: number) =>
    request('/collect', isCollectResponse, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cities, days }),
    }),

  forecasts: (city: string) =>
    request(`/forecasts/${encodeURIComponent(city)}`, isForecastsResponse),

  stats: () => request('/stats', isStatsResponse),
}
