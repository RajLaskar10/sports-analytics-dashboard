# StatsBomb open data: https://github.com/statsbomb/open-data
# This data is free for non-commercial use under the StatsBomb Public Data License.
# See: https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf

"""
Downloads StatsBomb open data for the 2018 FIFA World Cup.
Target: competition_id=43, season_id=3.
Files are saved to data/raw/ and already-downloaded files are skipped.
"""

import os
import json
import requests

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

COMPETITION_ID = 43  # FIFA World Cup
SEASON_ID = 3        # 2018


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def download_file(url, dest_path):
    """Download a file if it doesn't already exist locally."""
    if os.path.exists(dest_path):
        print(f"  Skipping (exists): {dest_path}")
        return False

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    ensure_dir(os.path.dirname(dest_path))
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(resp.json(), f, indent=2)

    print(f"  Downloaded: {dest_path}")
    return True


def download_competitions():
    """Download competitions.json."""
    url = f"{BASE_URL}/competitions.json"
    dest = os.path.join(RAW_DIR, "competitions.json")
    download_file(url, dest)


def download_matches():
    """Download matches for the 2018 World Cup."""
    url = f"{BASE_URL}/matches/{COMPETITION_ID}/{SEASON_ID}.json"
    dest_dir = os.path.join(RAW_DIR, "matches", str(COMPETITION_ID))
    dest = os.path.join(dest_dir, f"{SEASON_ID}.json")
    download_file(url, dest)

    with open(dest, "r", encoding="utf-8") as f:
        matches = json.load(f)

    return matches


def download_events(matches):
    """Download event files for each match."""
    print(f"\nDownloading events for {len(matches)} matches...")
    events_dir = os.path.join(RAW_DIR, "events")
    ensure_dir(events_dir)

    for i, match in enumerate(matches, 1):
        match_id = match["match_id"]
        url = f"{BASE_URL}/events/{match_id}.json"
        dest = os.path.join(events_dir, f"{match_id}.json")
        print(f"  [{i}/{len(matches)}] Match {match_id}")
        download_file(url, dest)


def download_lineups(matches):
    """Download lineup files for each match."""
    print(f"\nDownloading lineups for {len(matches)} matches...")
    lineups_dir = os.path.join(RAW_DIR, "lineups")
    ensure_dir(lineups_dir)

    for i, match in enumerate(matches, 1):
        match_id = match["match_id"]
        url = f"{BASE_URL}/lineups/{match_id}.json"
        dest = os.path.join(lineups_dir, f"{match_id}.json")
        print(f"  [{i}/{len(matches)}] Match {match_id}")
        download_file(url, dest)


def main():
    print("=== StatsBomb Data Ingestion ===")
    print(f"Competition: FIFA World Cup 2018 (id={COMPETITION_ID}, season={SEASON_ID})\n")

    print("1. Downloading competitions.json...")
    download_competitions()

    print("\n2. Downloading matches...")
    matches = download_matches()
    print(f"   Found {len(matches)} matches")

    print("\n3. Downloading events...")
    download_events(matches)

    print("\n4. Downloading lineups...")
    download_lineups(matches)

    print("\n=== Ingestion complete ===")


if __name__ == "__main__":
    main()
