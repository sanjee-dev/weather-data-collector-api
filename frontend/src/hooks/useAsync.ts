import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../services/api'

interface AsyncState<T> {
  data: T | null
  error: ApiError | null
  loading: boolean
  reload: () => void
}

/** Runs an async function when the component loads, and again when `key` changes. */
export function useAsync<T>(fn: () => Promise<T>, key: string): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)

  // Keep the latest function in a ref so the effect only re-runs when `key` changes.
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fnRef
      .current()
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setData(null)
        setError(err instanceof ApiError ? err : new ApiError('Something went wrong.', 'invalid'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [key, tick])

  return { data, error, loading, reload: () => setTick((t) => t + 1) }
}
