# Power BI Dashboard Setup

How to connect Power BI Desktop to the Supabase database and build the four-page dashboard.

## Connecting to Supabase

Power BI connects to Supabase the same way it connects to any PostgreSQL database — just use your Supabase host and credentials.

1. Open Power BI Desktop
2. Click **Get Data** → **Database** → **PostgreSQL database**
3. Enter your server details:
   - Server: `db.<your-project-ref>.supabase.co`
   - Database: `postgres`
4. Enter your credentials (same as in `.env`)
5. In the Navigator, select the **views** — not the raw tables:
   - `player_shooting_stats`
   - `player_passing_stats`
   - `team_pressing_stats`
   - `match_xg_summary`
   - `top_chance_creators`
6. Click **Load**

Import the views, not the raw tables. The views contain pre-computed KPIs so you don't need to write DAX for the core metrics.

## Dashboard Pages

### Page 1 — Tournament Overview

**Card visuals** at the top:
- Total matches (count of rows in `match_xg_summary`)
- Total goals (sum of `home_goals + away_goals`)
- Average xG per match (average of `home_xg + away_xg`)

**Bar chart**: Team xG vs Actual Goals
- Use `match_xg_summary`, group by team
- Side-by-side bars: total xG (expected) vs total goals (actual)
- Teams that scored more than their xG overperformed; less means underperformed

**Table**: Match xG Summary
- Columns: match_date, home_team, away_team, home_xg, away_xg, home_goals, away_goals, total_xg_diff
- Sort by `ABS(total_xg_diff)` descending to show the biggest performance gaps first

### Page 2 — Player Shooting

**Scatter plot**: xG vs Goals
- X-axis: `total_xg`
- Y-axis: `goals`
- Each dot is a player
- Add a reference line where x = y (the diagonal)
- Players above the line overperformed their xG; below means underperformed

**Bar chart**: Top 10 Players by xG
- Filter to top 10 by `total_xg`
- Show `total_xg` and `goals` as side-by-side bars

**Slicer**: Team
- Add a team slicer so you can filter to a specific team

### Page 3 — Player Passing

**Bar chart**: Top Passers by Completion Rate
- Use `player_passing_stats`
- Filter: `total_passes >= 50` (to avoid low-volume outliers)
- Sort by `completion_rate_pct` descending
- Show top 15-20 players

**Bar chart**: Through Balls and Switches Leaderboard
- Separate bar charts or a grouped bar for `through_balls` and `switches`
- Sort by count descending

**Slicer**: Team

### Page 4 — Pressing

**Bar chart**: Team Pressing Intensity
- Use `team_pressing_stats`
- Y-axis: `avg_pressures_per_match`
- Sort descending

**Bar chart**: Pressing Success Rate by Team
- Y-axis: `press_success_rate_pct`
- Sort descending

Note: pressing success rate is approximate. It counts a pressure as successful if a Ball Recovery by the same team follows within 5 events. Real pressing metrics would need tracking data.

## DAX Measures

Add these calculated measures for flexibility in the dashboard:

```dax
Goals per Match = 
DIVIDE(SUM(player_shooting_stats[goals]), SUM(player_shooting_stats[matches_played]))

xG per Match = 
DIVIDE(SUM(player_shooting_stats[total_xg]), SUM(player_shooting_stats[matches_played]))

xG Overperformance = 
SUM(player_shooting_stats[goals]) - SUM(player_shooting_stats[total_xg])

Pass Completion % = 
DIVIDE(SUM(player_passing_stats[completed_passes]), SUM(player_passing_stats[total_passes])) * 100
```

## Notes

- **Northeastern email**: If you have a Northeastern email address, you can get a free Power BI Service license through your university. This lets you publish dashboards to the web for sharing.

- **Exporting for interviews**: If you're presenting at an interview where you can't share a live Power BI link, export the dashboard as a PDF. In Power BI Desktop: File → Export to PDF. Each page becomes a separate page in the PDF.
