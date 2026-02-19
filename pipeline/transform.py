"""
Flattens StatsBomb JSON event data into tabular CSVs for PostgreSQL loading.

Input:  data/raw/ JSON files (from ingest.py)
Output: data/processed/ CSV files (matches, events, shots, passes, players, lineups)

StatsBomb coordinate system:
  - Origin is top-left of the pitch
  - Pitch dimensions: 120 yards (length) x 80 yards (width)
  - location[0] = x (0-120, along the length)
  - location[1] = y (0-80, along the width)
"""

import os
import json
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

COMPETITION_ID = 43
SEASON_ID = 3


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def transform_matches():
    """Extract match-level data into a flat table."""
    matches_file = os.path.join(RAW_DIR, "matches", str(COMPETITION_ID), f"{SEASON_ID}.json")
    raw_matches = load_json(matches_file)

    rows = []
    for m in raw_matches:
        rows.append({
            "match_id": m["match_id"],
            "match_date": m["match_date"],
            "home_team": m["home_team"]["home_team_name"],
            "away_team": m["away_team"]["away_team_name"],
            "home_score": m["home_score"],
            "away_score": m["away_score"],
            "competition": m["competition"]["competition_name"],
            "season": m["season"]["season_name"],
        })

    return pd.DataFrame(rows)


def transform_events():
    """
    Flatten all event JSON files into an events table.
    Also extract shot-specific and pass-specific rows into separate tables.
    """
    events_dir = os.path.join(RAW_DIR, "events")
    event_files = [f for f in os.listdir(events_dir) if f.endswith(".json")]

    all_events = []
    all_shots = []
    all_passes = []

    for filename in event_files:
        match_id = int(filename.replace(".json", ""))
        raw_events = load_json(os.path.join(events_dir, filename))

        for evt in raw_events:
            location = evt.get("location", [None, None])
            loc_x = location[0] if location and len(location) >= 1 else None
            loc_y = location[1] if location and len(location) >= 2 else None

            event_type = evt.get("type", {}).get("name", "")
            team_name = evt.get("team", {}).get("name", "")
            player_info = evt.get("player", {})
            player_id = player_info.get("id")
            player_name = player_info.get("name", "")

            # Get outcome from the type-specific subdict where applicable
            outcome = None
            type_key = event_type.lower().replace(" ", "_")
            if type_key in evt and isinstance(evt[type_key], dict):
                outcome_info = evt[type_key].get("outcome", {})
                if isinstance(outcome_info, dict):
                    outcome = outcome_info.get("name")

            event_row = {
                "event_id": evt["id"],
                "match_id": match_id,
                "index": evt.get("index"),
                "period": evt.get("period"),
                "timestamp": evt.get("timestamp"),
                "minute": evt.get("minute"),
                "second": evt.get("second"),
                "event_type": event_type,
                "team": team_name,
                "player_id": player_id,
                "player_name": player_name,
                "location_x": loc_x,
                "location_y": loc_y,
                "outcome": outcome,
            }
            all_events.append(event_row)

            # Extract shot-specific data
            if event_type == "Shot" and "shot" in evt:
                shot = evt["shot"]
                shot_row = {
                    "event_id": evt["id"],
                    "match_id": match_id,
                    "team": team_name,
                    "player_id": player_id,
                    "player_name": player_name,
                    "minute": evt.get("minute"),
                    "location_x": loc_x,
                    "location_y": loc_y,
                    "xg": shot.get("statsbomb_xg"),
                    "shot_outcome": shot.get("outcome", {}).get("name"),
                    "shot_technique": shot.get("technique", {}).get("name"),
                    "shot_body_part": shot.get("body_part", {}).get("name"),
                }
                all_shots.append(shot_row)

            # Extract pass-specific data
            if event_type == "Pass" and "pass" in evt:
                pass_data = evt["pass"]
                pass_row = {
                    "event_id": evt["id"],
                    "match_id": match_id,
                    "team": team_name,
                    "player_id": player_id,
                    "player_name": player_name,
                    "minute": evt.get("minute"),
                    "pass_length": pass_data.get("length"),
                    "pass_angle": pass_data.get("angle"),
                    "pass_recipient": pass_data.get("recipient", {}).get("name"),
                    "pass_outcome": pass_data.get("outcome", {}).get("name"),
                    "pass_through_ball": pass_data.get("technique", {}).get("name") == "Through Ball",
                    "pass_switch": pass_data.get("switch", False),
                }
                all_passes.append(pass_row)

    events_df = pd.DataFrame(all_events)
    shots_df = pd.DataFrame(all_shots)
    passes_df = pd.DataFrame(all_passes)

    return events_df, shots_df, passes_df


def transform_players(events_df):
    """Extract unique players from the events table."""
    players = events_df[events_df["player_id"].notna()][["player_id", "player_name", "team"]].copy()
    players["player_id"] = players["player_id"].astype(int)
    players = players.drop_duplicates(subset=["player_id"]).reset_index(drop=True)
    return players


def transform_lineups():
    """Extract lineup data from lineup JSON files."""
    lineups_dir = os.path.join(RAW_DIR, "lineups")
    lineup_files = [f for f in os.listdir(lineups_dir) if f.endswith(".json")]

    rows = []
    for filename in lineup_files:
        match_id = int(filename.replace(".json", ""))
        raw_lineups = load_json(os.path.join(lineups_dir, filename))

        for team_data in raw_lineups:
            team_name = team_data["team_name"]
            for player in team_data.get("lineup", []):
                # Position comes from the positions array — take the first (starting) position
                positions = player.get("positions", [])
                position = positions[0].get("position", "") if positions else ""

                rows.append({
                    "match_id": match_id,
                    "team": team_name,
                    "player_id": player["player_id"],
                    "player_name": player["player_name"],
                    "jersey_number": player.get("jersey_number"),
                    "position": position,
                })

    return pd.DataFrame(rows)


def main():
    print("=== StatsBomb Data Transformation ===\n")
    ensure_dir(PROCESSED_DIR)

    print("1. Transforming matches...")
    matches_df = transform_matches()
    matches_df.to_csv(os.path.join(PROCESSED_DIR, "matches.csv"), index=False)
    print(f"   matches.csv: {len(matches_df)} rows")

    print("2. Transforming events, shots, and passes...")
    events_df, shots_df, passes_df = transform_events()
    events_df.to_csv(os.path.join(PROCESSED_DIR, "events.csv"), index=False)
    shots_df.to_csv(os.path.join(PROCESSED_DIR, "shots.csv"), index=False)
    passes_df.to_csv(os.path.join(PROCESSED_DIR, "passes.csv"), index=False)
    print(f"   events.csv: {len(events_df)} rows")
    print(f"   shots.csv: {len(shots_df)} rows")
    print(f"   passes.csv: {len(passes_df)} rows")

    print("3. Extracting unique players...")
    players_df = transform_players(events_df)
    players_df.to_csv(os.path.join(PROCESSED_DIR, "players.csv"), index=False)
    print(f"   players.csv: {len(players_df)} rows")

    print("4. Transforming lineups...")
    lineups_df = transform_lineups()
    lineups_df.to_csv(os.path.join(PROCESSED_DIR, "lineups.csv"), index=False)
    print(f"   lineups.csv: {len(lineups_df)} rows")

    print("\n=== Transformation complete ===")


if __name__ == "__main__":
    main()
