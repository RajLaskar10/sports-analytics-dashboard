-- Useful ad-hoc queries for exploring the 2018 World Cup data.
-- Run these against the database after loading data and creating views.

-- Top 10 players by total xG in the tournament
SELECT player_name, team, total_xg, goals, goals_minus_xg
FROM player_shooting_stats
ORDER BY total_xg DESC
LIMIT 10;

-- Top 10 players by pass completion rate (minimum 50 passes)
SELECT player_name, team, total_passes, completed_passes, completion_rate_pct
FROM player_passing_stats
WHERE total_passes >= 50
ORDER BY completion_rate_pct DESC
LIMIT 10;

-- Teams ranked by pressing intensity (average pressures per match)
SELECT team, matches, total_pressures, avg_pressures_per_match, press_success_rate_pct
FROM team_pressing_stats
ORDER BY avg_pressures_per_match DESC;

-- Matches with biggest xG vs result discrepancy
SELECT match_date, home_team, away_team,
       home_xg, away_xg, home_goals, away_goals, total_xg_diff
FROM match_xg_summary
ORDER BY ABS(total_xg_diff) DESC
LIMIT 10;

-- Shot map for a specific player (replace the player name as needed)
SELECT s.player_name, s.minute, s.location_x, s.location_y,
       s.xg, s.shot_outcome, s.shot_technique, s.shot_body_part,
       m.home_team || ' vs ' || m.away_team AS match
FROM shots s
JOIN matches m ON s.match_id = m.match_id
WHERE s.player_name = 'Harry Kane'
ORDER BY m.match_date, s.minute;
