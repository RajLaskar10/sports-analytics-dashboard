# Working with StatsBomb Open Data

A quick reference for understanding and using the StatsBomb open dataset.

## Where to Find It

The open data is hosted on GitHub: [https://github.com/statsbomb/open-data](https://github.com/statsbomb/open-data)

No API key or authentication is needed. The JSON files are accessible directly via GitHub raw content URLs.

## File Structure

The data follows a hierarchy:

```
competitions.json
  → matches/{competition_id}/{season_id}.json
    → events/{match_id}.json
    → lineups/{match_id}.json
```

1. **`competitions.json`** — List of all available competitions and seasons.
2. **`matches/{comp_id}/{season_id}.json`** — All matches for a given competition and season. Each match has a `match_id`.
3. **`events/{match_id}.json`** — All on-ball events for a single match. This is the core data.
4. **`lineups/{match_id}.json`** — Player lineups for a single match (who played, their position, jersey number).

For this project, we use competition_id=43 (FIFA World Cup) and season_id=3 (2018).

## Event Types

Each event has a `type.name` field. The ones that matter most for this project:

| Event Type     | What It Is |
|---------------|------------|
| **Pass**       | A pass attempt, with length, angle, recipient, and outcome |
| **Shot**       | A shot attempt, with xG, outcome, technique, and body part |
| **Pressure**   | A pressing action against the player on the ball |
| **Ball Recovery** | Winning the ball back after it was with the opponent |
| **Carry**      | Moving with the ball (dribbling in space, not past a defender) |
| **Dribble**    | Attempting to dribble past a defender |

Other types include Clearance, Block, Interception, Foul Committed, Foul Won, Goalkeeper, and many more. The full list is in the StatsBomb data spec.

## The Location Array

Each event can have a `location` field, which is an array of `[x, y]`:

- **x** is along the length of the pitch: 0 to 120 yards
- **y** is along the width: 0 to 80 yards
- **Origin** is the top-left corner

Some useful reference points:
- Center spot: `[60, 40]`
- Penalty spot (attacking): `[108, 40]` approximately
- Top of the box (attacking): `[102, 18]` to `[102, 62]`

Not all events have locations. For example, substitutions and tactical shifts don't.

## Type-Specific Subdicts

Events have type-specific data nested under a key matching the event type (lowercased). Examples:

**Shot event** — has a `"shot"` key:
```json
{
  "type": {"name": "Shot"},
  "shot": {
    "statsbomb_xg": 0.12,
    "outcome": {"name": "Saved"},
    "technique": {"name": "Normal"},
    "body_part": {"name": "Right Foot"}
  }
}
```

**Pass event** — has a `"pass"` key:
```json
{
  "type": {"name": "Pass"},
  "pass": {
    "length": 23.5,
    "angle": -0.45,
    "recipient": {"name": "Antoine Griezmann"},
    "outcome": {"name": "Incomplete"},
    "technique": {"name": "Through Ball"}
  }
}
```

A completed pass has no `outcome` field in the `pass` dict (or it's absent). An incomplete pass has an outcome like "Incomplete", "Out", or "Offside".

## Full Documentation

For the complete data specification — all event types, all fields, all possible values — see the StatsBomb data spec PDF:

[https://github.com/statsbomb/open-data/tree/master/doc](https://github.com/statsbomb/open-data/tree/master/doc)

The spec is detailed and worth reading if you want to extend this project beyond the basics covered here.
