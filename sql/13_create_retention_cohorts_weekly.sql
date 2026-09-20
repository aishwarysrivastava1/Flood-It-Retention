-- 13_create_retention_cohorts_weekly.sql
-- Purpose: long-format cohort table (cohort week x day number) for retention curves and heatmaps.
CREATE OR REPLACE VIEW flood_it.retention_cohorts_weekly AS
WITH players AS (
  SELECT player_id, cohort_date, days_observable,
         DATE_TRUNC(cohort_date, WEEK(MONDAY)) AS cohort_week          -- group joining days into Monday-starting weeks
  FROM flood_it.player_retention
),
activity AS (
  SELECT p.cohort_week, p.player_id,
         DATE_DIFF(a.activity_date, p.cohort_date, DAY) AS day_number  -- 0 = joining day, 1 = next day, ...
  FROM players AS p
  JOIN flood_it.fct_player_days AS a ON a.player_id = p.player_id
),
day_numbers AS (
  SELECT DISTINCT day_number FROM activity WHERE day_number BETWEEN 0 AND 30   -- the day numbers we report
),
eligible AS (
  SELECT p.cohort_week, d.day_number, COUNT(*) AS eligible_players
  FROM players AS p
  CROSS JOIN day_numbers AS d
  WHERE p.days_observable >= d.day_number                                   -- only players followed at least that long
  GROUP BY p.cohort_week, d.day_number
),
returned AS (
  SELECT cohort_week, day_number, COUNT(DISTINCT player_id) AS active_players
  FROM activity
  WHERE day_number BETWEEN 0 AND 30
  GROUP BY cohort_week, day_number
)
SELECT
  e.cohort_week,
  e.day_number,
  e.eligible_players,
  IFNULL(r.active_players, 0)                                                 AS active_players,
  ROUND(100 * SAFE_DIVIDE(IFNULL(r.active_players, 0), e.eligible_players), 2) AS retention_pct
FROM eligible AS e
LEFT JOIN returned AS r
  ON r.cohort_week = e.cohort_week AND r.day_number = e.day_number;
