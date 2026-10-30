create table if not exists public.events (
    id text primary key,
    type text not null check (type in ('study', 'exam')),
    title text not null,
    topic text not null default '',
    date date not null,
    start_hour integer not null default 16,
    start_time text not null,
    duration numeric not null default 0.5,
    location text not null default '',
    completed boolean not null default false,
    priority text not null default 'Normaal' check (priority in ('Laag', 'Normaal', 'Hoog')),
    created_at timestamptz not null default now()
);

create index if not exists events_date_time_idx on public.events (date, start_time);
create index if not exists events_type_idx on public.events (type);

-- This starter is designed for one trusted user / private prototype.
-- Before enabling public access or multiple user accounts, enable RLS,
-- add a user_id column, and create policies tied to auth.uid().
-- Do not expose a service_role key in the Streamlit app.
