-- Run this ONCE in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.

create table if not exists public.forecasts (
  id            bigint generated always as identity primary key,
  city          text             not null,
  country       text             not null,
  date          date             not null,
  temp_max      double precision,
  temp_min      double precision,
  precipitation double precision,
  created_at    timestamptz      not null default now(),
  -- One row per city per day. The API's upsert(on_conflict="city,date") relies on this.
  constraint forecasts_city_date_key unique (city, date)
);

-- The backend uses the secret (service role) key, which bypasses Row Level Security.
-- Turning RLS on with no policies means the public "anon" key can NOT read or write this table.
alter table public.forecasts enable row level security;
