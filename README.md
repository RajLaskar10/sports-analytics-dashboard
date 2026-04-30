# Sports Analytics Dashboard

A football analytics pipeline that ingests StatsBomb event-level data for the 2018 FIFA World Cup, loads it into a normalized Supabase schema, computes KPIs via SQL views, and surfaces them in an interactive Streamlit dashboard.

> **Live demo**: *(add Streamlit Cloud URL after deployment)*

## Why Event-Level Data?

Most football stats you see online are box-score aggregates — goals, assists, possession percentage. StatsBomb event data is different: every pass, shot, carry, dribble, tackle, and press is a separate record with x/y coordinates on the pitch. This makes it possible to calculate things like expected goals (xG), pressing intensity, progressive passes, and shot maps — the kind of analysis you'd see from professional football analytics teams.

## Dataset

This project uses [StatsBomb open data](https://github.com/statsbomb/open-data), which is free for non-commercial use. The open dataset covers several competitions including:

- **2018 FIFA World Cup** (used in this project)
- La Liga (multiple seasons)
- FA Women's Super League
- UEFA Euro 2020
- And others

No API key is required. The data is served as JSON files from the StatsBomb GitHub repository.

## Tech Stack

| Component       | Technology           |
|----------------|----------------------|
| Language        | Python 3.11          |
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
├── docs/
│   ├── data-model.md               # Schema explanation and entity relationships
│   ├── kpi-definitions.md          # What each KPI means and how it's calculated
│   └── statsbomb-guide.md          # Quick guide to working with StatsBomb data
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

Fill in your Supabase connection details in `.env` (see step 4).

### 2. Ingest data from StatsBomb

```bash
python pipeline/ingest.py
```

Downloads all 2018 World Cup match, event, and lineup JSON files into `data/raw/`. Files that already exist are skipped, so re-running is safe.

### 3. Transform JSON into CSVs

```bash
python pipeline/transform.py
```

Flattens the nested StatsBomb JSON into six tabular CSVs in `data/processed/`: matches, events, shots, passes, players, and lineups.

### 4. Set up Supabase

1. Create a free project at [supabase.com](https://supabase.com).
2. Go to **Project Settings → Database** and note your connection parameters.
3. Open the **SQL Editor** and run `db/schema.sql` to create the tables.
4. Fill in `.env` with your Supabase credentials (see `.env.example`).

### 5. Load data into Supabase

```bash
python pipeline/load.py
```

Truncates all tables and bulk-inserts from the CSVs. Safe to re-run.

### 6. Create KPI views

In the Supabase **SQL Editor**, run `db/views.sql`.

### 7. Run the Streamlit dashboard locally

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml with your Supabase credentials
streamlit run streamlit_app.py
```

### 8. Connect Power BI (optional)

See [powerbi/setup.md](powerbi/setup.md) for instructions on connecting Power BI Desktop to the Supabase views.

## Design Decisions

- **Separate shots and passes tables** rather than one flat events table. Shot-specific columns (xG, technique) and pass-specific columns (length, angle, through ball) would be mostly NULL in a single table. Separate tables are cleaner and make the SQL views simpler. See [docs/data-model.md](docs/data-model.md).

- **SQL views as the KPI layer**. All analytics logic lives in SQL views, not in Python or DAX. This means the KPIs are version-controlled and reusable across any BI tool. Both Streamlit and Power BI connect to the views, not the raw tables. See [docs/kpi-definitions.md](docs/kpi-definitions.md).

- **Approximate "per 90" stats**. StatsBomb open data doesn't include player minutes, so per-90 stats are approximated using match count × 90. This is noted wherever it applies.

- **Pressing success is estimated**. A pressure is counted as successful if a Ball Recovery by the same team follows within 5 events. This is a rough proxy — the real metric would need tracking data. See [docs/kpi-definitions.md](docs/kpi-definitions.md).
