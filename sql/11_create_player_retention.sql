-- 11_create_player_retention.sql
-- Purpose: per NEW player, flags for returning on day 1/3/7/14/30 and within days 1-7.
CREATE OR REPLACE VIEW flood_it.player_retention AS
SELECT
  p.player_id,
  p.cohort_date,
  p.days_observable,
  MAX(IF(DATE_DIFF(a.activity_date, p.cohort_date, DAY) = 1, 1, 0))              AS retained_d1,   -- active exactly 1 day after joining
  MAX(IF(DATE_DIFF(a.activity_date, p.cohort_date, DAY) = 3, 1, 0))              AS retained_d3,
  MAX(IF(DATE_DIFF(a.activity_date, p.cohort_date, DAY) = 7, 1, 0))              AS retained_d7,
  MAX(IF(DATE_DIFF(a.activity_date, p.cohort_date, DAY) = 14, 1, 0))             AS retained_d14,
  MAX(IF(DATE_DIFF(a.activity_date, p.cohort_date, DAY) = 30, 1, 0))             AS retained_d30,
  MAX(IF(DATE_DIFF(a.activity_date, p.cohort_date, DAY) BETWEEN 1 AND 7, 1, 0))  AS returned_within_7d,  -- the churn label source
  COUNT(DISTINCT a.activity_date)                                                AS active_days_total,
  MAX(DATE_DIFF(a.activity_date, p.cohort_date, DAY))                            AS last_active_day_number
FROM flood_it.dim_players AS p
JOIN flood_it.fct_player_days AS a
  ON a.player_id = p.player_id
WHERE p.is_new_player                                                            -- only players who truly joined inside the window
GROUP BY p.player_id, p.cohort_date, p.days_observable;
