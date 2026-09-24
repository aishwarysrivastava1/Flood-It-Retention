-- 15_create_retention_by_milestone.sql
-- Purpose: how far players got on day 0 vs how often they came back (descriptive, not causal).
CREATE OR REPLACE VIEW flood_it.retention_by_milestone AS
SELECT
  CASE
    WHEN d0_levels_completed  >= 5 THEN '4) Completed 5+ levels'   -- measured completions, not the completed_5_levels event: that event also fires in the non-quickplay level mode
    WHEN d0_levels_completed   > 0 THEN '3) Completed a level'
    WHEN d0_levels_started     > 0 THEN '2) Started a level only'
    ELSE                                '1) Engaged, no level started'
  END                                                  AS furthest_milestone_day0,
  COUNT(*)                                             AS players,
  SUM(retained_d1)                                     AS retained_d1_players,     -- raw counts so charts never rebuild them from rounded percentages
  SUM(returned_within_7d)                              AS returned_players,
  ROUND(100 * AVG(retained_d1), 2)                     AS d1_retention_pct,
  ROUND(100 * AVG(returned_within_7d), 2)              AS returned_within_7d_pct
FROM flood_it.player_features
GROUP BY furthest_milestone_day0;
