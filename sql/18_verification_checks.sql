-- 18_verification_checks.sql
-- Purpose: one query that proves the data layer is internally consistent.
-- Every row must say PASS. Run it after building the views, and again any time you change one.

WITH checks AS (
  SELECT 'one row per player in dim_players' AS check_name,                                        -- each player must appear exactly once
         (SELECT COUNT(*) FROM flood_it.dim_players) = (SELECT COUNT(DISTINCT player_id) FROM flood_it.dim_players) AS passed
  UNION ALL
  SELECT 'no player has more active days than the dataset has days',                               -- impossible values catch join mistakes
         (SELECT MAX(days) FROM (SELECT COUNT(*) AS days FROM flood_it.fct_player_days GROUP BY player_id))
         <= (SELECT COUNT(DISTINCT activity_date) FROM flood_it.fct_player_days)
  UNION ALL
  SELECT 'sessions are at least as many as active player-days',                                    -- a day holds one or more sessions
         (SELECT COUNT(*) FROM flood_it.fct_sessions) >= (SELECT COUNT(*) FROM flood_it.fct_player_days)
  UNION ALL
  SELECT 'no activity happens before a player joined',                                             -- cohort_date must be the earliest active day
         (SELECT COUNT(*) FROM flood_it.fct_player_days AS a
            JOIN flood_it.dim_players AS p ON p.player_id = a.player_id
          WHERE a.activity_date < p.cohort_date) = 0
  UNION ALL
  SELECT 'day-0 retention is 100% in every weekly cohort',                                         -- players are active on their joining day by definition
         (SELECT MIN(retention_pct) FROM flood_it.retention_cohorts_weekly WHERE day_number = 0) = 100
  UNION ALL
  SELECT 'retention falls as the day number rises',                                                -- D1 >= D7 >= D30
         (SELECT MIN(retention_pct) FROM flood_it.retention_summary WHERE day_number = 1)
         >= (SELECT MIN(retention_pct) FROM flood_it.retention_summary WHERE day_number = 7)
  UNION ALL
  SELECT 'eligible players fall as the day number rises',                                          -- censoring is being applied
         (SELECT eligible_players FROM flood_it.retention_summary WHERE day_number = 1)
         >= (SELECT eligible_players FROM flood_it.retention_summary WHERE day_number = 30)
  UNION ALL
  SELECT 'funnel step 1 equals the modeling table size',                                           -- the funnel and the model use the same population
         (SELECT players FROM flood_it.first_day_funnel WHERE step_order = 1)
         = (SELECT COUNT(*) FROM flood_it.player_features)
  UNION ALL
  SELECT 'funnel progression steps never increase',                                                -- steps 1-4 are nested
         (SELECT COUNTIF(players > previous_players) FROM (
            SELECT players, LAG(players) OVER (ORDER BY step_order) AS previous_players
            FROM flood_it.first_day_funnel WHERE step_order <= 4)) = 0
  UNION ALL
  SELECT 'every player in player_features had a full week of follow-up',                           -- the label is knowable for everyone
         (SELECT COUNTIF(days_observable < 7) FROM flood_it.player_features) = 0
  UNION ALL
  SELECT 'no negative feature values',                                                             -- counts cannot be negative
         (SELECT COUNTIF(d0_engaged_minutes < 0 OR d0_levels_started < 0 OR d0_sessions < 0) FROM flood_it.player_features) = 0
  UNION ALL
  SELECT 'both churn classes exist',                                                               -- a single-class label would break the model
         (SELECT AVG(returned_within_7d) FROM flood_it.player_features) BETWEEN 0.01 AND 0.99
  UNION ALL
  SELECT 'D7 rate in retention_summary matches a direct calculation',                              -- checks the UNION ALL logic in view 12
         ABS((SELECT retention_pct FROM flood_it.retention_summary WHERE day_number = 7)
             - (SELECT ROUND(100 * SAFE_DIVIDE(SUM(retained_d7), COUNTIF(days_observable >= 7)), 2)
                  FROM flood_it.player_retention)) < 0.01
  UNION ALL
  SELECT 'return rate matches between player_features and player_retention',                       -- checks the modeling table filters
         ABS((SELECT ROUND(100 * AVG(returned_within_7d), 2) FROM flood_it.player_features)
             - (SELECT ROUND(100 * AVG(returned_within_7d), 2) FROM flood_it.player_retention
                 WHERE days_observable >= 7)) < 0.01
)
SELECT
  check_name,                                                    -- what was tested
  IF(passed, 'PASS', 'FAIL') AS result                           -- every row must say PASS
FROM checks
ORDER BY result, check_name;
