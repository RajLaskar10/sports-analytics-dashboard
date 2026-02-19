-- StatsBomb 2018 World Cup — PostgreSQL Schema
-- Run this before loading data with pipeline/load.py

-- matches: one row per match in the tournament
CREATE TABLE IF NOT EXISTS matches (
    match_id    INTEGER PRIMARY KEY,
    match_date  DATE,
    home_team   TEXT,
    away_team   TEXT,
    home_score  INTEGER,
    away_score  INTEGER,
    competition TEXT,
    season      TEXT
);
COMMENT ON TABLE matches IS 'Match-level data: one row per game with teams and final score.';

-- players: unique players seen across all events
CREATE TABLE IF NOT EXISTS players (
    player_id   INTEGER PRIMARY KEY,
    player_name TEXT,
    team        TEXT
);
COMMENT ON TABLE players IS 'Unique players extracted from event data. Team is the team they appeared for most.';

-- events: one row per on-ball action (pass, shot, carry, tackle, etc.)
CREATE TABLE IF NOT EXISTS events (
    event_id    TEXT PRIMARY KEY,
    match_id    INTEGER REFERENCES matches(match_id),
    index       INTEGER,
    period      INTEGER,
    timestamp   TEXT,
    minute      INTEGER,
    second      INTEGER,
    event_type  TEXT,
    team        TEXT,
    player_id   INTEGER,
    player_name TEXT,
    location_x  NUMERIC,
    location_y  NUMERIC,
    outcome     TEXT
);
COMMENT ON TABLE events IS 'All on-ball events. Each row is a single action (pass, shot, pressure, carry, etc.) with x/y coordinates.';

-- shots: shot-specific attributes, one row per shot event
CREATE TABLE IF NOT EXISTS shots (
    event_id       TEXT PRIMARY KEY REFERENCES events(event_id),
    match_id       INTEGER REFERENCES matches(match_id),
    team           TEXT,
    player_id      INTEGER,
    player_name    TEXT,
    minute         INTEGER,
    location_x     NUMERIC,
    location_y     NUMERIC,
    xg             NUMERIC,
    shot_outcome   TEXT,
    shot_technique TEXT,
    shot_body_part TEXT
);
COMMENT ON TABLE shots IS 'Shot events with xG, outcome, technique, and body part. One row per shot.';

-- passes: pass-specific attributes, one row per pass event
CREATE TABLE IF NOT EXISTS passes (
    event_id        TEXT PRIMARY KEY REFERENCES events(event_id),
    match_id        INTEGER REFERENCES matches(match_id),
    team            TEXT,
    player_id       INTEGER,
    player_name     TEXT,
    minute          INTEGER,
    pass_length     NUMERIC,
    pass_angle      NUMERIC,
    pass_recipient  TEXT,
    pass_outcome    TEXT,
    pass_through_ball BOOLEAN,
    pass_switch     BOOLEAN
);
COMMENT ON TABLE passes IS 'Pass events with length, angle, recipient, and flags for through balls and switches.';

-- lineups: which players started/appeared in each match
CREATE TABLE IF NOT EXISTS lineups (
    match_id      INTEGER REFERENCES matches(match_id),
    team          TEXT,
    player_id     INTEGER,
    player_name   TEXT,
    jersey_number INTEGER,
    position      TEXT,
    PRIMARY KEY (match_id, player_id)
);
COMMENT ON TABLE lineups IS 'Match lineups: which players appeared in each game with position and jersey number.';

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_events_match_id ON events(match_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_shots_player_id ON shots(player_id);
CREATE INDEX IF NOT EXISTS idx_passes_player_id ON passes(player_id);
