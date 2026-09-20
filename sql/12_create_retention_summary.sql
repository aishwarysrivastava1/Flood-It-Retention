-- 12_create_retention_summary.sql
-- Purpose: overall D1/D3/D7/D14/D30 retention, counting ONLY players who could have been observed that long.
CREATE OR REPLACE VIEW flood_it.retention_summary AS
WITH per_day AS (
  SELECT 'D1' AS retention_day, 1 AS day_number,
         COUNTIF(days_observable >= 1) AS eligible_players, SUM(IF(days_observable >= 1, retained_d1, 0)) AS retained_players
  FROM flood_it.player_retention
  UNION ALL
  SELECT 'D3', 3, COUNTIF(days_observable >= 3), SUM(IF(days_observable >= 3, retained_d3, 0)) FROM flood_it.player_retention
  UNION ALL
  SELECT 'D7', 7, COUNTIF(days_observable >= 7), SUM(IF(days_observable >= 7, retained_d7, 0)) FROM flood_it.player_retention
  UNION ALL
  SELECT 'D14', 14, COUNTIF(days_observable >= 14), SUM(IF(days_observable >= 14, retained_d14, 0)) FROM flood_it.player_retention
  UNION ALL
  SELECT 'D30', 30, COUNTIF(days_observable >= 30), SUM(IF(days_observable >= 30, retained_d30, 0)) FROM flood_it.player_retention
)
SELECT
  retention_day,
  day_number,
  eligible_players,
  retained_players,
  ROUND(100 * SAFE_DIVIDE(retained_players, eligible_players), 2) AS retention_pct
FROM per_day;
