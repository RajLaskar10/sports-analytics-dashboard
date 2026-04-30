# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A football analytics pipeline for the 2018 FIFA World Cup using StatsBomb open event-level data. The pipeline fetches JSON from GitHub, flattens it into CSVs, loads them into Supabase (PostgreSQL), and exposes KPI SQL views consumed by a Streamlit dashboard and Power BI.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in Supabase DB credentials
```

## Running the Pipeline

Run steps in order:

```bash
python pipeline/ingest.py       # downloads JSON to data/raw/ (skips existing files)
python pipeline/transform.py    # flattens JSON into data/processed/ CSVs
# In Supabase SQL Editor: run db/schema.sql
python pipeline/load.py         # truncates and reloads all tables (reads .env automatically)
# In Supabase SQL Editor: run db/views.sql
```

`load.py` always truncates before inserting, so re-running any step is safe.

## Running the Dashboard Locally

```bash
streamlit run streamlit_app.py
```

Credentials are read from `.streamlit/secrets.toml` (local) or Streamlit Cloud secrets (deployed). See `.streamlit/secrets.toml.example` for the expected shape.

## Architecture

**Data flow**: StatsBomb GitHub → `data/raw/` JSON → `data/processed/` CSVs → Supabase tables → SQL views → Streamlit / Power BI

**Pipeline modules** (`pipeline/`):
- `ingest.py`: Downloads competitions, matches, events, and lineups JSON for competition_id=43, season_id=3 (2018 World Cup)
- `transform.py`: Flattens nested JSON into six flat DataFrames. Shot-specific and pass-specific fields are extracted into separate DataFrames rather than kept in a wide events table
- `load.py`: Reads env vars via `python-dotenv`, connects to Supabase with `sslmode=require`, truncates tables in FK-safe order (matches → players → events → shots/passes → lineups), bulk-inserts via `psycopg2.execute_values`

**Database schema** (`db/`):
- `schema.sql`: Six tables. `shots` and `passes` are one-to-one extensions of `events` (share `event_id` PK), holding type-specific columns. This avoids ~30+ NULL columns in a single wide events table
- `views.sql`: All KPI logic lives here — Streamlit and Power BI connect to views, not raw tables. Views: `player_shooting_stats`, `player_passing_stats`, `team_pressing_stats`, `match_xg_summary`, `top_chance_creators`
- `queries.sql`: Ad-hoc exploration queries (run in Supabase SQL Editor)

**Streamlit app** (`streamlit_app.py`):
- 4 tabs mirroring the dashboard pages: Tournament Overview, Player Shooting, Player Passing, Pressing
- Connects to Supabase via `sqlalchemy` + `psycopg2`; caches queries with `@st.cache_data(ttl=3600)`
- Credentials: reads from `st.secrets["supabase"]` when deployed, falls back to env vars locally

**StatsBomb coordinate system**: origin = top-left, x = 0–120 (length), y = 0–80 (width). Penalty spot ≈ (108, 40).

## Key Caveats in the Data

- **Pass completion**: in StatsBomb data, a completed pass has `pass_outcome IS NULL`; an incomplete pass has a named outcome
- **Progressive passes** (`pass_length > 25`) is a rough proxy — it counts long sideways passes too
- **Pressing success** (Ball Recovery within 5 events of a Pressure) is an approximation; the 5-event window is arbitrary
- **Per-90 stats** are approximated as `count / matches` because player minutes are not in the open data
- **xG** values are StatsBomb's pre-computed `statsbomb_xg` field; not comparable to xG from other providers

## Repository Conventions

- **Sole contributor**: RajLaskar. No co-author trailers on commits.
- **Branch naming**: `feat/<description>`, `fix/<description>`, `chore/<description>`, `docs/<description>`. Branch off `main`, PR back into `main`.
- **Commit messages**: conventional style — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`. No mention of AI tools or assistants anywhere in commits or PR descriptions.

## No Tests

There is no test suite. The pipeline scripts are verified by re-running end-to-end and spot-checking row counts in Supabase.
