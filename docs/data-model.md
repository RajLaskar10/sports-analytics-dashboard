# Data Model

How the database schema maps to StatsBomb event data.

## What is StatsBomb Event Data?

StatsBomb event data records every on-ball action in a football match. Each row in the events table is a single action — a pass, shot, carry, tackle, dribble, or pressure — with x/y coordinates on the pitch and metadata about the outcome.

This is much richer than traditional box-score stats. Instead of just knowing that a team had 15 shots, you know the exact location, xG value, body part, and outcome of each shot.

## Entity Relationships

```
matches (1) ──→ (many) events
matches (1) ──→ (many) lineups
events  (1) ──→ (0 or 1) shots     (only for Shot events)
events  (1) ──→ (0 or 1) passes    (only for Pass events)
players (1) ──→ (many) events      (via player_id)
```

- Each **match** has many **events** (typically 3,000-4,000 per game).
- Each **match** has a **lineup** entry for each player who appeared.
- **Shots** and **passes** are one-to-one extensions of events — they hold the type-specific columns that only apply to that event type.
- **Players** are extracted as unique entries from the events data.

## Why Separate Shots and Passes Tables?

Shot events have columns like `xg`, `shot_outcome`, `shot_technique`, and `shot_body_part`. Pass events have `pass_length`, `pass_angle`, `pass_recipient`, `pass_through_ball`, and `pass_switch`. If you put all of these into the events table, most rows would have NULLs in most of these columns (only ~2% of events are shots, ~30% are passes).

Separate tables keep the schema clean:
- The events table holds columns common to all events.
- The shots table holds shot-specific attributes.
- The passes table holds pass-specific attributes.
- You join them when needed.

## Coordinate System

StatsBomb uses a coordinate system where:
- **Origin** is the top-left corner of the pitch
- **X-axis** runs along the length of the pitch: 0 to 120 yards
- **Y-axis** runs along the width: 0 to 80 yards
- A shot from the penalty spot is at roughly (108, 40)
- The center circle is at roughly (60, 40)

Both `location_x` and `location_y` are stored as numeric values in the events, shots, and passes tables.

## Known Limitations

- **No player minutes data**. StatsBomb open data doesn't include how many minutes each player was on the pitch. This means "per 90" stats are approximate — we estimate using match count × 90 minutes, which overstates playing time for substitutes.

- **Pressing stats are approximate**. There's no explicit "press success" flag in the data. We approximate it by checking if a Ball Recovery by the same team follows a Pressure event within 5 events in the sequence. This is a rough proxy.

- **Player team assignment**. A player's team in the players table is taken from the events data. If a player appeared for multiple teams (unlikely in a World Cup but possible in league data), only one team is stored.
