# Weather Data Collector

A FastAPI service that downloads daily forecasts from [Open-Meteo](https://open-meteo.com)
and stores them in Supabase. An optional React dashboard provides collection, forecast, and
analytics pages.

## Features

- `POST /collect` geocodes cities, fetches forecasts concurrently, and reports per-city results.
- Retries transient weather API failures with exponential backoff; limits concurrency to five cities.
- Upserts records into Supabase on `(city, date)` to avoid duplicate rows.
- `GET /forecasts/{city}`, `GET /stats`, and `GET /health` endpoints.
- React dashboard built with Vite, TypeScript, Tailwind CSS, and Recharts.
- Backend tests with mocked external services; credentials are kept out of source control.

## Project layout

```text
backend/       FastAPI app, Supabase access, and Python tests
database/      Supabase table schema
frontend/      React + Vite dashboard
README.md      Setup and usage
```

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js 20.19+ or 22.12+ and npm (for the dashboard)
- A Supabase project for database-backed collection

## Setup

### 1. Configure Supabase

Create a Supabase project. In its SQL Editor, run [`database/schema.sql`](database/schema.sql)
once to create `public.forecasts`.

Copy `backend/.env.example` to `backend/.env` and set your project URL and secret key:

```dotenv
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_KEY=YOUR-SUPABASE-SECRET-KEY
```

Keep the secret key only in `backend/.env` or your hosting provider's secret settings.
Never commit it or put it in the frontend.

### 2. Install backend dependencies

From the repository root, run:

```powershell
cd backend
uv sync
```

### 3. Install frontend dependencies

In a second terminal:

```powershell
cd frontend
npm install
```

The frontend defaults to the local backend at `http://127.0.0.1:8000`. To override it,
copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.
Restart Vite after changing this value.

## Run locally

Start the backend from the `backend` directory:

```powershell
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Start the dashboard from the `frontend` directory in another terminal:

```powershell
npm run dev
```

Open:

- Dashboard: <http://localhost:5173>
- API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

If port 8000 is already in use, stop the other backend process or start this backend on
another port and set `VITE_API_BASE_URL` to match.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns API health status. |
| `POST` | `/collect` | Fetches and saves forecasts for 1–10 cities and 1–14 days. |
| `GET` | `/forecasts/{city}` | Reads saved forecasts for a city, ordered by date. |
| `GET` | `/stats` | Returns saved record and city totals. |

Example request:

```json
{
  "cities": ["Colombo", "London"],
  "days": 7
}
```

Send it to `POST /collect` from `/docs` or with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/collect \
  -H "Content-Type: application/json" \
  -d "{\"cities\":[\"Colombo\",\"London\"],\"days\":7}"
```

The endpoint returns successes and failures for each city. An HTTP 200 response does not
necessarily mean every city was saved; inspect the `succeeded` and `failed` counts.

## Tests and lint

Run from the `backend` directory:

```powershell
uv run pytest
uv run ruff check .
```

Tests mock weather HTTP calls and Supabase, so they do not write to your database.

## Deploy

The API and dashboard can be deployed separately. Configure these environment variables
in the hosting provider:

- **Backend:** `SUPABASE_URL`, `SUPABASE_KEY`, and `CORS_ORIGINS` (the deployed frontend URL).
- **Frontend:** `VITE_API_BASE_URL` (the deployed backend URL; used at build time).

For Vercel, use `backend` as the API project's root directory and `frontend` as the
dashboard project's root directory. After setting environment variables, redeploy the
corresponding project. Do not expose the Supabase secret key to the frontend.

## Security and troubleshooting

- `.env` files and application logs are ignored by Git. Check `git status` before pushing.
- `Database is not configured`: check the backend `.env` values and restart the API.
- Database unavailable: check the backend logs for the sanitized database error.
- CORS error: add the exact frontend origin to `CORS_ORIGINS`, then restart the backend.
- No saved rows: run `/collect` and inspect its response, then refresh `public.forecasts`
  in the Supabase Table Editor.
