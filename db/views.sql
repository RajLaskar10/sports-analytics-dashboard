-- KPI Views for the Sports Analytics Dashboard
-- These views are the analytical layer. Power BI connects to these views, not the raw tables.
-- Run this after loading data with pipeline/load.py.

-- Player shooting stats: xG, goals, shots on target, overperformance
CREATE OR REPLACE VIEW player_shooting_stats AS
SELECT
    s.player_id,
    s.player_name,
    s.team,
    COUNT(DISTINCT s.match_id)                                      AS matches_played,
    COUNT(*)                                                         AS total_shots,
    COUNT(*) FILTER (WHERE s.shot_outcome IN ('Saved', 'Goal'))     AS shots_on_target,
    COUNT(*) FILTER (WHERE s.shot_outcome = 'Goal')                 AS goals,
    ROUND(SUM(s.xg)::NUMERIC, 2)                                   AS total_xg,
    ROUND((SUM(s.xg) / NULLIF(COUNT(*), 0))::NUMERIC, 3)           AS xg_per_shot,
    COUNT(*) FILTER (WHERE s.shot_outcome = 'Goal') - ROUND(SUM(s.xg)::NUMERIC, 2) AS goals_minus_xg,
    -- Approximate shots per 90: shots / (matches * 90) * 90 = shots / matches
    ROUND((COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT s.match_id), 0)), 2) AS shots_per_match
FROM shots s
GROUP BY s.player_id, s.player_name, s.team;

-- Player passing stats: completion rate, through balls, switches, progressive passes
CREATE OR REPLACE VIEW player_passing_stats AS
SELECT
    p.player_id,
    p.player_name,
    p.team,
    COUNT(*)                                                          AS total_passes,
    COUNT(*) FILTER (WHERE p.pass_outcome IS NULL)                    AS completed_passes,
    ROUND(
        (COUNT(*) FILTER (WHERE p.pass_outcome IS NULL))::NUMERIC
        / NULLIF(COUNT(*), 0) * 100, 1
    )                                                                 AS completion_rate_pct,
    ROUND(AVG(p.pass_length)::NUMERIC, 1)                            AS avg_pass_length,
    COUNT(*) FILTER (WHERE p.pass_through_ball = TRUE)                AS through_balls,
    COUNT(*) FILTER (WHERE p.pass_switch = TRUE)                      AS switches,
    -- Progressive passes: rough proxy using pass_length > 25 yards
    COUNT(*) FILTER (WHERE p.pass_length > 25)                        AS progressive_passes
FROM passes p
GROUP BY p.player_id, p.player_name, p.team;

-- Team pressing stats: pressure count per match, average, and approximate success rate
CREATE OR REPLACE VIEW team_pressing_stats AS
WITH press_events AS (
    SELECT
        e.match_id,
        e.team,
        e.index AS press_index,
        e.event_type
    FROM events e
    WHERE e.event_type = 'Pressure'
),
-- Approximate pressing success: a pressure followed by a Ball Recovery
-- by the same team within 5 events (proxy for ~5 seconds)
press_success AS (
    SELECT
        pe.match_id,
        pe.team,
        pe.press_index,
        CASE WHEN EXISTS (
            SELECT 1 FROM events e2
            WHERE e2.match_id = pe.match_id
              AND e2.team = pe.team
              AND e2.event_type = 'Ball Recovery'
              AND e2.index > pe.press_index
              AND e2.index <= pe.press_index + 5
        ) THEN 1 ELSE 0 END AS success
    FROM press_events pe
),
team_match AS (
    SELECT
        ps.match_id,
        ps.team,
        COUNT(*)          AS pressures,
        SUM(ps.success)   AS successful_pressures
    FROM press_success ps
    GROUP BY ps.match_id, ps.team
)
SELECT
    tm.team,
    COUNT(DISTINCT tm.match_id)                                       AS matches,
    SUM(tm.pressures)                                                 AS total_pressures,
    ROUND(AVG(tm.pressures)::NUMERIC, 1)                             AS avg_pressures_per_match,
    ROUND(
        SUM(tm.successful_pressures)::NUMERIC
        / NULLIF(SUM(tm.pressures), 0) * 100, 1
    )                                                                 AS press_success_rate_pct
FROM team_match tm
GROUP BY tm.team;

-- Match xG summary: compare expected and actual goals per match
CREATE OR REPLACE VIEW match_xg_summary AS
SELECT
    m.match_id,
    m.match_date,
    m.home_team,
    m.away_team,
    COALESCE(home_xg.xg, 0)  AS home_xg,
    COALESCE(away_xg.xg, 0)  AS away_xg,
    m.home_score              AS home_goals,
    m.away_score              AS away_goals,
    ROUND((m.home_score - COALESCE(home_xg.xg, 0) + m.away_score - COALESCE(away_xg.xg, 0))::NUMERIC, 2) AS total_xg_diff
FROM matches m
LEFT JOIN (
    SELECT match_id, team, ROUND(SUM(xg)::NUMERIC, 2) AS xg
    FROM shots
    GROUP BY match_id, team
) home_xg ON home_xg.match_id = m.match_id AND home_xg.team = m.home_team
LEFT JOIN (
    SELECT match_id, team, ROUND(SUM(xg)::NUMERIC, 2) AS xg
    FROM shots
    GROUP BY match_id, team
) away_xg ON away_xg.match_id = m.match_id AND away_xg.team = m.away_team;

-- Top chance creators: players ranked by key passes (through balls as proxy)
CREATE OR REPLACE VIEW top_chance_creators AS
SELECT
    p.player_id,
    p.player_name,
    p.team,
    COUNT(*) FILTER (WHERE p.pass_through_ball = TRUE) AS key_passes,
    COUNT(*)                                            AS total_passes,
    ROUND(
        COUNT(*) FILTER (WHERE p.pass_through_ball = TRUE)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100, 2
    )                                                   AS key_pass_rate_pct
FROM passes p
GROUP BY p.player_id, p.player_name, p.team
HAVING COUNT(*) FILTER (WHERE p.pass_through_ball = TRUE) > 0
ORDER BY key_passes DESC;
