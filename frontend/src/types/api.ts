// These types mirror the JSON that the FastAPI backend returns (see backend/models.py).

export interface DailyForecast {
  date: string // "2026-11-02"
  temp_max: number | null
  temp_min: number | null
  precipitation: number | null
}

export interface CollectedCity {
  city: string
  country: string
  latitude: number
  longitude: number
  records_saved: number
  forecasts: DailyForecast[]
}

export interface CityFailure {
  city: string
  reason: string
}

export interface CollectResponse {
  requested: number
  succeeded: number
  failed: number
  total_records_saved: number
  successes: CollectedCity[]
  failures: CityFailure[]
}

export interface StoredForecast extends DailyForecast {
  city: string
  country: string
  created_at: string | null
}

export interface ForecastsResponse {
  city: string
  country: string
  count: number
  forecasts: StoredForecast[]
}

export interface CitySummary {
  city: string
  country: string
  records: number
  first_date: string
  last_date: string
}

export interface StatsResponse {
  total_records: number
  total_cities: number
  cities: CitySummary[]
}

export interface HealthResponse {
  status: string
}
