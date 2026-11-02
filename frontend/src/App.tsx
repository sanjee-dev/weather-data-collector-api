import { CollectionProvider } from './context/CollectionContext'
import { useHashRoute } from './hooks/useHashRoute'
import { AppLayout } from './layouts/AppLayout'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { CollectPage } from './pages/CollectPage'
import { ForecastsPage } from './pages/ForecastsPage'
import { OverviewPage } from './pages/OverviewPage'

export default function App() {
  const route = useHashRoute()
  return (
    <CollectionProvider>
      <AppLayout route={route.name}>
        {route.name === 'overview' && <OverviewPage />}
        {route.name === 'collect' && <CollectPage />}
        {route.name === 'forecasts' && (
          <ForecastsPage key={route.params.get('city') ?? ''} initialCity={route.params.get('city') ?? ''} />
        )}
        {route.name === 'analytics' && <AnalyticsPage />}
      </AppLayout>
    </CollectionProvider>
  )
}
