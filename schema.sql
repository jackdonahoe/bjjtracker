create extension if not exists pg_trgm;

create table people (
    id            serial primary key,
    full_name     text not null,
    email         text,
    source        text not null,
    first_seen    timestamptz not null default now(),
    merged_into   int references people(id)
);

create table sessions (
    id          serial primary key,
    held_at     timestamptz not null,
    notes       text
);

create table check_ins (
    id          serial primary key,
    person_id   int not null references people(id),
    session_id  int not null references sessions(id),
    checked_in  timestamptz not null default now(),
    unique (person_id, session_id)
);

create table admins (
    id             serial primary key,
    email          text not null unique,
    password_hash  text not null,
    created_at     timestamptz not null default now()
);

create index on check_ins (person_id);
create index on check_ins (session_id);

-- One session per calendar day, in the club's local timezone (not UTC,
-- which is what Postgres would use by default on a server like Railway).
-- Without this, a practice held 8-10pm Eastern would roll into the next
-- UTC day partway through and get split across two "sessions".
create unique index sessions_one_per_day
on sessions (((held_at at time zone 'America/Chicago')::date));