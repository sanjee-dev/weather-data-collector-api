# Daily note – Day 2: Python Backend Skills, Weather Data Collector

> This is a starting point. The facts below are true for this project. The sections about learning and
> getting stuck must be **your own** experience, so write them yourself after you run the project.

## What did I finish today?
- A FastAPI backend with `GET /health`, `POST /collect` and `GET /forecasts/{city}`.
- An async `WeatherClient` (Open-Meteo geocoding + forecast) with my own retry logic (1 s, 2 s, 4 s backoff).
- Concurrent fetching with `asyncio.gather` and an `asyncio.Semaphore(5)`, where one failed city does not stop the others.
- Saving to Supabase with `upsert(on_conflict="city,date")`, and reading saved forecasts sorted by date.
- Logging to the console and `app.log`.
- 75 automated tests (pytest, respx, unittest.mock) and a clean `ruff check`.
- An extra React dashboard.
- (Add: pushed to GitHub ☐ · deployed on Vercel ☐ · live URL tested ☐)

## What did I learn?
_(Write 3–5 sentences in your own words. Ideas: how exponential backoff works; why a semaphore limits concurrency;
why mocking HTTP with respx makes tests fast and reliable; what an upsert is and why `(city, date)` must be unique;
why the Supabase secret key must stay on the server.)_

## Where did I get stuck, and how did I solve it?
_(Be honest and specific: the error message, what you tried, what finally worked. Your mentor asked you to
write down what you already tried if you are stuck for more than 30 minutes.)_

## What would I improve if I had one more day?
- Add the Groq one-sentence summary (stretch goal) and store it in Supabase.
- Include the country in the unique key so two cities with the same name do not share rows.
- Add frontend tests and a rate limit on `/collect`.
