# Note: After loading data, run db/views.sql separately to create the KPI views.

"""
Loads processed CSVs into Supabase (PostgreSQL).

Reads all six CSVs from data/processed/, truncates the target tables,
bulk-inserts using psycopg2 execute_values, and runs ANALYZE on each table.

DB connection config is read from environment variables (see .env.example).
Copy .env.example to .env and fill in your Supabase connection details.
"""

import os
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# Table load order matters because of foreign key constraints.
# Load parents first, then children.
TABLES = [
    {
        "name": "matches",
        "csv": "matches.csv",
        "columns": ["match_id", "match_date", "home_team", "away_team",
                     "home_score", "away_score", "competition", "season"],
    },
    {
        "name": "players",
        "csv": "players.csv",
        "columns": ["player_id", "player_name", "team"],
    },
    {
        "name": "events",
        "csv": "events.csv",
        "columns": ["event_id", "match_id", "index", "period", "timestamp",
                     "minute", "second", "event_type", "team", "player_id",
                     "player_name", "location_x", "location_y", "outcome"],
    },
    {
        "name": "shots",
        "csv": "shots.csv",
        "columns": ["event_id", "match_id", "team", "player_id", "player_name",
                     "minute", "location_x", "location_y", "xg", "shot_outcome",
                     "shot_technique", "shot_body_part"],
    },
    {
        "name": "passes",
        "csv": "passes.csv",
        "columns": ["event_id", "match_id", "team", "player_id", "player_name",
                     "minute", "pass_length", "pass_angle", "pass_recipient",
                     "pass_outcome", "pass_through_ball", "pass_switch"],
    },
    {
        "name": "lineups",
        "csv": "lineups.csv",
        "columns": ["match_id", "team", "player_id", "player_name",
                     "jersey_number", "position"],
    },
]


def get_connection():
    """Create a Supabase (PostgreSQL) connection using environment variables."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
        sslmode="require",
    )


def _to_python(val):
    """Convert numpy scalars and NaN to Python-native types for psycopg2."""
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.bool_):
        return bool(val)
    return val


def load_table(cursor, table_config):
    """Truncate a table and bulk-insert rows from the corresponding CSV."""
    name = table_config["name"]
    csv_path = os.path.join(PROCESSED_DIR, table_config["csv"])
    columns = table_config["columns"]

    df = pd.read_csv(csv_path)

    # Truncate before loading so re-running is safe
    cursor.execute(f"TRUNCATE TABLE {name} CASCADE;")

    if len(df) == 0:
        print(f"  {name}: 0 rows (empty CSV)")
        return

    # Build tuples for execute_values, converting numpy types and NaN → None
    col_list = ", ".join(columns)
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"
    insert_sql = f"INSERT INTO {name} ({col_list}) VALUES %s"

    rows = [tuple(_to_python(row[col]) for col in columns) for _, row in df.iterrows()]
    execute_values(cursor, insert_sql, rows, template=template, page_size=1000)
    print(f"  {name}: {len(rows)} rows inserted")


def main():
    print("=== Loading Data into PostgreSQL ===\n")

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        for table_config in TABLES:
            load_table(cursor, table_config)

        conn.commit()
        print("\nAll tables loaded. Running ANALYZE...")

        conn.autocommit = True
        for table_config in TABLES:
            cursor.execute(f"ANALYZE {table_config['name']};")
            print(f"  ANALYZE {table_config['name']} done")

        print("\n=== Load complete ===")

    except Exception as e:
        conn.rollback()
        print(f"\nError during load: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
