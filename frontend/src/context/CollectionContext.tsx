import { createContext, useContext, useState, type ReactNode } from 'react'
import type { CollectResponse } from '../types/api'

export interface LastCollection {
  response: CollectResponse
  days: number
  finishedAt: Date
}

interface CollectionContextValue {
  last: LastCollection | null
  setLast: (value: LastCollection) => void
}

const CollectionContext = createContext<CollectionContextValue | null>(null)

/** Remembers the most recent collection so the Overview page can show it. */
export function CollectionProvider({ children }: { children: ReactNode }) {
  const [last, setLast] = useState<LastCollection | null>(null)
  return (
    <CollectionContext.Provider value={{ last, setLast }}>{children}</CollectionContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCollection(): CollectionContextValue {
  const ctx = useContext(CollectionContext)
  if (!ctx) throw new Error('useCollection must be used inside <CollectionProvider>')
  return ctx
}
