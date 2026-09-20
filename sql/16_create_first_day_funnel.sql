-- 16_create_first_day_funnel.sql
-- Purpose: long-format funnel for charts. Steps 1-4 are nested; steps 5-6 are retention outcomes for ALL new players.
CREATE OR REPLACE VIEW flood_it.first_day_funnel AS
SELECT 1 AS step_order, 'Joined (first engagement)' AS step, COUNT(*) AS players FROM flood_it.player_features
UNION ALL
SELECT 2, 'Started a level on day 0',    COUNTIF(d0_levels_started > 0)                                   FROM flood_it.player_features
UNION ALL
SELECT 3, 'Completed a level on day 0',  COUNTIF(d0_levels_started > 0 AND d0_levels_completed > 0)       FROM flood_it.player_features
UNION ALL
SELECT 4, 'Completed 5 levels on day 0', COUNTIF(d0_levels_completed > 0 AND d0_completed_5_levels > 0)   FROM flood_it.player_features
UNION ALL
SELECT 5, 'Returned on day 1',           COUNTIF(retained_d1 = 1)                                          FROM flood_it.player_features
UNION ALL
SELECT 6, 'Returned within 7 days',      COUNTIF(returned_within_7d = 1)                                   FROM flood_it.player_features;
