import { useEffect, useState } from 'react'

export type RouteName = 'overview' | 'collect' | 'forecasts' | 'analytics'
const ROUTES: RouteName[] = ['overview', 'collect', 'forecasts', 'analytics']

export interface Route {
  name: RouteName
  params: URLSearchParams
}

function parse(): Route {
  // "#/forecasts?city=Colombo" -> { name: "forecasts", params: city=Colombo }
  const raw = window.location.hash.replace(/^#\/?/, '')
  const [path, query = ''] = raw.split('?')
  const name = ROUTES.find((r) => r === path) ?? 'overview'
  return { name, params: new URLSearchParams(query) }
}

export function useHashRoute(): Route {
  const [route, setRoute] = useState<Route>(parse)
  useEffect(() => {
    const onChange = () => setRoute(parse())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export const hrefFor = (name: RouteName, params?: Record<string, string>): string => {
  const query = params ? `?${new URLSearchParams(params).toString()}` : ''
  return `#/${name}${query}`
}
