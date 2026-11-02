# Requirements checklist

Status meanings: **Complete** = built and checked (method shown) · **Not Verified** = built or documented, but it could not be run in the build environment · **Your action** = only you can do it · **Not implemented** = deliberately left out.

"Mock/stub E2E" = the real FastAPI server was started and called with `curl` and a real headless browser, with Open-Meteo and Supabase replaced by a local stand-in. It proves the code paths, not the real services.

## Part 1 – Setup and study the API

| Requirement | Where | Verification | Status |
|---|---|---|---|
| `uv init` project, add libraries + dev tools | `backend/pyproject.toml`, `uv.lock` | `uv sync` + `uv run pytest` | Complete |
| Read Open-Meteo docs, call both endpoints once and look at the JSON | – | Endpoint parameters follow the PDF; the build environment cannot reach open-meteo.com | **Your action** |
| Supabase account, URL + secret key in `.env` as `SUPABASE_URL`, `SUPABASE_KEY`, `.env` in `.gitignore` | `backend/.env.example`, `.gitignore` | `git status` must not list `.env` | **Your action** (file/ignore rules Complete) |

## Part 2 – Models and API client

| Requirement | Where | Verification | Status |
|---|---|---|---|
| Pydantic `City`, `DailyForecast` | `backend/models.py` | `tests/test_models.py` (valid + invalid data) | Complete |
| Async `WeatherClient` with `httpx.AsyncClient`; `geocode()` raises clear error if not found; `get_forecast(city, days)` | `backend/weather_client.py` | `tests/test_weather_client.py` | Complete |
| Timeout on every request | `REQUEST_TIMEOUT_SECONDS = 10` in `weather_client.py` | `test_client_has_a_timeout_by_default` | Complete |
| Own exceptions (`CityNotFoundError`, `APIError`, …) | `backend/exceptions.py` | used and asserted in tests | Complete |
| Type hints on every function | all backend modules | read through; no type checker is configured | Complete (not machine-checked) |

## Part 3 – Retry and concurrency

| Requirement | Where | Verification | Status |
|---|---|---|---|
| Own retry (no library): max 3 retries on timeout, network error, 5xx | `WeatherClient._get_json` | `test_500_then_success…`, `test_timeout_is_retried…`, `test_network_error_retried_until_exhausted` | Complete |
| Exponential backoff 1 s, 2 s, 4 s | `BACKOFF_BASE_SECONDS`, `_get_json` | tests assert delays `[1.0, 2.0, 4.0]`; mock/stub E2E log showed real waits of 1 s, 2 s, 4 s | Complete |
| No retry on 4xx or city not found | `_try_once`, `geocode` | `test_4xx_is_not_retried` (400/404/429), `test_geocode_city_not_found_does_not_retry` | Complete |
| `asyncio.gather` for all cities | `forecast_service.collect_forecasts` | `test_cities_are_processed_concurrently` | Complete |
| Max 5 at once with `asyncio.Semaphore` | `MAX_CONCURRENCY = 5` | `test_concurrency_is_limited_to_five` (10 cities, max 5 in flight) | Complete |
| One city's failure never stops the others; successes and failures collected separately | `_collect_one`, `CollectionOutcome` | `test_one_failure_does_not_stop_the_others`, `test_unexpected_exception_is_contained_and_hidden` | Complete |

## Part 4 – Supabase

| Requirement | Where | Verification | Status |
|---|---|---|---|
| `forecasts` table: id, city, country, date, temp_max, temp_min, precipitation, created_at + unique (city, date) | `database/schema.sql` | Written to the PDF; **not run** against a real Postgres | Not Verified (you run it in the SQL Editor) |
| `create_client` once, in its own file, URL/key from `.env` | `backend/db.py` (`get_client`, cached) | `test_missing_credentials_raise_clear_error` | Complete (live connection Not Verified) |
| `upsert(..., on_conflict="city,date")` | `db.save_forecasts` | `test_save_uses_upsert_with_city_date_conflict`, `test_collect_success_saves_with_upsert` | Complete (against mock) |
| Function that reads saved forecasts for one city sorted by date | `db.get_forecasts` | `test_get_forecasts_sorted_by_date_and_parsed` (checks `.order("date")`) | Complete (against mock) |
| Secret key never in code / GitHub / frontend | env vars only; `.gitignore`; frontend has no Supabase code | searched the source for the key variable; only `config.py` reads it | Complete |

## Part 5 – FastAPI and logging

| Requirement | Where | Verification | Status |
|---|---|---|---|
| `GET /health` → `{"status":"ok"}` | `main.py` | `test_health`; curl | Complete |
| `POST /collect`, max 10 cities, days 1–14, concurrent fetch, save, return successes + failures with reason | `main.py`, `models.CollectRequest` | `test_collect_*`, 422 tests; mock/stub E2E curl | Complete |
| `GET /forecasts/{city}` or 404 | `main.py` | `test_forecasts_returns_404_when_no_data`; curl | Complete |
| `logging` (not `print`); retry = warning, failure = error; console + `app.log` | `logging_config.py` | `test_retries_are_logged_as_warnings`; server log inspected in mock/stub E2E | Complete |
| Run locally with `uv run uvicorn main:app --reload` and test from `/docs` | README §9 | Server started (via uvicorn) in the mock/stub E2E; `/docs` not opened | Not Verified against real Supabase |

## Part 6 – Tests

| Requirement | Where | Verification | Status |
|---|---|---|---|
| Models valid/invalid | `tests/test_models.py` | `uv run pytest` | Complete |
| respx: success, not found, 500→success, 500 always (3 retries), 4xx no retry | `tests/test_weather_client.py` | `uv run pytest` | Complete |
| TestClient + mocked Supabase: `/health`, `/collect` 11 cities → 422, `/forecasts/{city}` 404 | `tests/test_api.py` | `uv run pytest` | Complete |
| Saving uses upsert with `on_conflict="city,date"` | `tests/test_db.py`, `tests/test_api.py` | `uv run pytest` | Complete |
| `uv run ruff check .` with no warnings | – | Output: `All checks passed!` | Complete |

Result of the last run: **75 passed, 0 failed** (`uv run pytest`), plus 1 third-party deprecation notice from Starlette's test client (not from this code, not a Ruff warning).

## Part 7 – GitHub, deploy, daily note

| Requirement | Where | Verification | Status |
|---|---|---|---|
| README (what, install `uv sync`, run, tests, endpoints) | `README.md` | – | Complete |
| Commit `pyproject.toml` + `uv.lock`, never `.env` / `app.log` | `.gitignore` | `git status` check is in README §15 | Your action |
| Push to a new GitHub repository | README §15 | – | **Your action** |
| Deploy to Vercel with env vars in the dashboard | README §16; `backend/main.py` at project root, `.python-version`, `uv.lock` | Matches Vercel's FastAPI docs (checked); **never deployed** | **Not Verified / Your action** |
| Test live URL: `/health`, `/docs`, `POST /collect` (3 cities), `GET /forecasts/{city}` | README §16a | – | **Your action** |
| Daily note | `daily-note.md` | Facts filled in; the personal parts are yours to write | **Your action** |

## Deliverables from the PDF

| Deliverable | Produced by |
|---|---|
| GitHub repository link | You (README §15) |
| Live URL of the deployed API | You (README §16a) – no URL has been invented |
| All tests passing, no ruff warnings | `uv run pytest` → 75 passed · `uv run ruff check .` → clean |
| Daily note | `daily-note.md` (finish it) |

## Stretch goal

| Requirement | Status |
|---|---|
| Groq one-sentence summary per city, saved in Supabase and returned by `GET /forecasts/{city}` | **Not implemented** (optional, "only if you finish early"). It would also need an extra `summary` column. |

## Extra: dashboard (from the second prompt)

| Requirement | Where | Verification | Status |
|---|---|---|---|
| React + Vite + TypeScript + Tailwind + Recharts + Lucide | `frontend/` | `npm run build` OK (`tsc -b` + Vite) | Complete |
| Pages: Overview, Collect Weather, Forecasts, Analytics (no fake pages) | `frontend/src/pages` | Real headless-browser run against the mock/stub E2E backend; screenshots reviewed (desktop + mobile) | Complete |
| Collect form respects 1–10 cities, 1–14 days; shows loading, results, failures, summary | `CollectPage.tsx` | Browser run: validation message, 2 succeeded / 1 failed shown after the backend answered | Complete |
| Only real backend data; no hard-coded chart arrays | `services/api.ts`, `AnalyticsPage.tsx` | Charts rendered from `/forecasts/{city}` responses | Complete |
| Frontend never touches Supabase; backend URL from `VITE_API_BASE_URL`; CORS configured | `services/api.ts`, `main.py` | CORS preflight checked with curl; browser run had 0 console errors | Complete |
| Frontend automated tests | – | – | Not implemented (backend tests are the priority) |
| `npm run lint` | – | 0 errors, 2 warnings (React-Compiler style hints about `setState` in an effect; harmless) | Complete |

## Where the two documents disagreed or were unclear

1. **Folder layout.** The prompt suggests `backend/app/main.py`; the PDF says `main.py` and `uv run uvicorn main:app`. **PDF followed:** modules sit directly in `backend/`.
2. **Logging.** The prompt says console logging is enough unless a file is required; the PDF requires `app.log`. **PDF followed**, with a console-only fallback on read-only hosts (Vercel).
3. **Extra endpoint.** `GET /stats` is not in the PDF. It only adds to the contract (the dashboard's overview and city list need it); the three required endpoints are unchanged.
4. **Unclear in the PDF:** the exact JSON shape of the `/collect` response (we use `successes` / `failures`); whether `/collect` should return an error status when every city fails (we return 200 with the list); whether "up to 3 retries" counts the first try (we do 1 + 3).
