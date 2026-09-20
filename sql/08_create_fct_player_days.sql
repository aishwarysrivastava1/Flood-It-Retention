-- 08_create_fct_player_days.sql
-- Purpose: one row per player per ACTIVE day (a day with at least one user_engagement event).
CREATE OR REPLACE VIEW flood_it.fct_player_days AS
SELECT
  player_id,
  event_date                                                AS activity_date,
  COUNTIF(event_name = 'user_engagement')                   AS engagement_events,
  ROUND(SUM(IFNULL(engagement_time_msec, 0)) / 60000, 2)    AS engaged_minutes,     -- milliseconds -> minutes
  COUNTIF(event_name = 'level_start_quickplay')             AS levels_started,
  COUNTIF(event_name = 'level_complete_quickplay')          AS levels_completed,
  COUNTIF(event_name = 'ad_reward')                         AS ad_rewards,          -- rewarded ads watched (monetization proxy)
  COUNTIF(event_name = 'spend_virtual_currency')            AS currency_spends      -- in-game currency spends (economy proxy)
FROM flood_it.stg_events
GROUP BY player_id, event_date
HAVING COUNTIF(event_name = 'user_engagement') > 0;         -- passive events alone (e.g. os_update) do not make a day active
