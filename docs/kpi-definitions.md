# KPI Definitions

Plain-language definitions for every KPI used in the SQL views and Power BI dashboard.

---

## xG (Expected Goals)

**What it measures**: The probability that a shot results in a goal, based on historical data. A shot from the penalty spot might have an xG of 0.76. A long-range effort might be 0.03.

**How it's calculated**: StatsBomb provides xG as a pre-computed value (`statsbomb_xg`) on each shot event. We sum it per player or per team. We don't build our own xG model — we use StatsBomb's.

**SQL**: `SUM(s.xg)` from the `shots` table, grouped by player or team.

**Caveats**: xG models vary between providers. StatsBomb's model accounts for shot location, body part, assist type, and game situation, but the exact formula is proprietary. Don't compare StatsBomb xG directly to xG from other providers.

---

## xG Overperformance (Goals minus xG)

**What it measures**: Whether a player scored more or fewer goals than expected. A positive value means the player is finishing better than the average player would from the same positions.

**How it's calculated**: `goals - total_xg`. A player with 5 goals and 3.2 xG has an overperformance of +1.8.

**SQL**: `COUNT(*) FILTER (WHERE shot_outcome = 'Goal') - SUM(xg)`

**Caveats**: Small sample sizes make this noisy. In a 7-game World Cup, a player might take 10-15 shots. That's not enough to draw conclusions about finishing skill — it's more useful for identifying which results were lucky or unlucky.

---

## Shots on Target %

**What it measures**: The percentage of shots that forced the goalkeeper into a save or went in.

**How it's calculated**: Shots with outcome "Saved" or "Goal" divided by total shots.

**SQL**: `COUNT(*) FILTER (WHERE shot_outcome IN ('Saved', 'Goal')) / COUNT(*)`

**Caveats**: A blocked shot (hit a defender before reaching the keeper) is not counted as on target. This is standard across football analytics.

---

## Pass Completion Rate

**What it measures**: The percentage of passes that reached a teammate.

**How it's calculated**: In StatsBomb data, a completed pass has a NULL `pass_outcome`. An incomplete pass has an outcome like "Incomplete", "Out", or "Offside". So completed passes = passes where `pass_outcome IS NULL`.

**SQL**: `COUNT(*) FILTER (WHERE pass_outcome IS NULL) / COUNT(*) * 100`

**Caveats**: Pass completion rate is heavily influenced by playing style. A team that plays short passes in their own half will have a higher completion rate than a team that plays long diagonal balls. A center-back will typically have a higher rate than an attacking midfielder. Compare within similar roles.

---

## Progressive Passes

**What it measures**: Passes that move the ball significantly up the pitch. We use `pass_length > 25 yards` as a rough proxy.

**How it's calculated**: Count of passes where `pass_length > 25`.

**SQL**: `COUNT(*) FILTER (WHERE pass_length > 25)`

**Caveats**: This is a rough approximation. A proper progressive pass metric would check that the pass moves the ball closer to the opponent's goal, not just that it's long. A 30-yard sideways pass would count here but shouldn't. We note this in the dashboard.

---

## Pressing Intensity

**What it measures**: How aggressively a team presses the opponent. Measured as the count of "Pressure" events per match.

**How it's calculated**: Count all events where `event_type = 'Pressure'`, grouped by team and match, then averaged across matches.

**SQL**: `AVG(pressure_count_per_match)` from the `team_pressing_stats` view.

**Caveats**: Pressing data depends on how StatsBomb defines and tags pressure events. Different providers may tag these differently. The raw counts are comparable within this dataset but not across datasets from different providers.

---

## Pressing Success Rate

**What it measures**: What percentage of pressures led to winning the ball back.

**How it's calculated**: A pressure is counted as successful if a "Ball Recovery" event by the same team follows within 5 events in the match sequence. This is an approximation — the 5-event window is a proxy for "within a few seconds."

**SQL**: Uses a subquery that checks for a Ball Recovery within 5 index positions of each Pressure event.

**Caveats**: This is the roughest metric in the project. The 5-event window is arbitrary. A real pressing success metric would use timestamp-based windows and track whether the pressing team gained possession, not just whether a Ball Recovery followed. We flag this in the dashboard.

---

## Key Passes (Top Chance Creators)

**What it measures**: Passes that directly led to a shot. We use through balls (`pass_through_ball = TRUE`) as a proxy.

**How it's calculated**: Count of passes where the `pass_through_ball` flag is true.

**SQL**: `COUNT(*) FILTER (WHERE pass_through_ball = TRUE)`

**Caveats**: Through balls are not the same as key passes. A key pass in the traditional sense is any pass that leads directly to a shot, regardless of type. StatsBomb does tag shot assists, but the through ball proxy is simpler and still identifies creative passers. A more complete version would look at the pass immediately preceding each shot event.
