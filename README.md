# Sports Analytics Dashboard

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sports-analytics-dashboard-lhyr8atch7cbxlybzdjxyb.streamlit.app/)

A football analytics pipeline that ingests StatsBomb event-level data for the 2018 FIFA World Cup, loads it into a normalized Supabase schema, computes KPIs via SQL views, and surfaces them in an interactive Streamlit dashboard.

## Dashboard

Four tabs covering the full tournament:

| Tab | What it shows |
|-----|--------------|
| 🏆 Tournament Overview | xG vs actual goals per team, match-by-match xG table |
| 🎯 Player Shooting | xG vs goals scatter, top-10 shooters by xG, team filter |
| 🎯 Player Passing | Completion rate, through balls, switches leaderboards |
| ⚡ Pressing | Pressing intensity and success rate by team |

## Dataset

64 matches · 227,849 events · 1,706 shots · 62,881 passes · 603 players

Uses [StatsBomb open data](https://github.com/statsbomb/open-data) — free for non-commercial use, no API key required. Data is served as JSON from the StatsBomb GitHub repository.

## Tech Stack

| Component       | Technology           |
|----------------|----------------------|
| Language        | Python 3.10+         |
| Data Processing | Pandas, NumPy        |
| HTTP Client     | Requests             |
| Database        | Supabase (PostgreSQL)|
| DB Driver       | psycopg2, SQLAlchemy |
| Dashboard       | Streamlit + Plotly   |
| BI Tool         | Power BI Desktop     |

## Project Structure

```
sports-analytics-dashboard/
├── data/
│   ├── raw/                        # StatsBomb JSON files (gitignored)
│   └── processed/                  # Transformed CSVs (gitignored)
├── pipeline/
│   ├── ingest.py                   # Download StatsBomb open data
│   ├── transform.py                # Flatten JSON into tabular format
│   └── load.py                     # Load processed CSVs into Supabase
├── db/
│   ├── schema.sql                  # Tables and indexes
│   ├── views.sql                   # KPI views (xG, press rate, etc.)
│   └── queries.sql                 # Ad-hoc queries for exploration
├── streamlit_app.py                # Interactive dashboard (4 tabs)
├── powerbi/
│   └── setup.md                    # Power BI connection instructions
├── .streamlit/
│   └── secrets.toml.example        # Credentials template for local dev
├── requirements.txt
├── .env.example
└── .gitignore
```

## How to Run

### 1. Set up the environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in your Supabase connection details in `.env` (see `.env.example`). If your password contains special characters (e.g. `@`, `#`), that's fine — the loader and dashboard both handle them correctly.

### 2. Run the pipeline

```bash
python pipeline/ingest.py       # downloads JSON to data/raw/ (~130 MB, skips existing)
python pipeline/transform.py    # flattens into data/processed/ CSVs
python pipeline/load.py         # truncates and reloads all Supabase tables
```

`load.py` always truncates before inserting, so re-running any step is safe.

### 3. Apply the database schema and views

In your Supabase **SQL Editor**, run in order:

1. `db/schema.sql` — creates the six tables and indexes
2. `db/views.sql` — creates the five KPI views

> **Tip**: If you have the [Supabase MCP server](https://supabase.com/docs/guides/getting-started/mcp) configured, you can apply these as migrations directly from your editor without touching the Supabase UI.

### 4. Run the Streamlit dashboard locally

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml with your Supabase credentials
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

### 5. Connect Power BI (optional)

See [powerbi/setup.md](powerbi/setup.md) for instructions on connecting Power BI Desktop to the Supabase KPI views.

## Design Decisions

**Separate shots and passes tables** — Shot-specific columns (xG, technique) and pass-specific columns (length, angle, through ball) would be mostly NULL in a single flat events table. The `shots` and `passes` tables each share `event_id` as a PK/FK with `events`, keeping the schema clean without wide NULL-heavy rows.

**SQL views as the KPI layer** — All analytics logic lives in `db/views.sql`, not in Python or DAX. KPIs are version-controlled and reusable across Streamlit, Power BI, or any other tool. Neither the dashboard nor Power BI queries raw tables directly.

**Approximate "per 90" stats** — StatsBomb open data doesn't include player minutes, so per-match rates are used as a proxy. This is noted wherever it applies.

**Pressing success is estimated** — A pressure is counted as successful if the same team records a Ball Recovery within 5 events. This is a rough proxy — real pressing metrics require tracking data.

## Key Caveats

- A **completed pass** has `pass_outcome IS NULL` in StatsBomb data; an incomplete pass has a named outcome
- **Progressive passes** (`pass_length > 25`) is a rough proxy — it includes long sideways passes
- **xG** values are StatsBomb's pre-computed `statsbomb_xg` field — not comparable to xG from other providers
- **StatsBomb coordinate system**: origin = top-left, x = 0–120 (length), y = 0–80 (width)
