-- 14_create_player_features.sql
-- Purpose: the modeling table. Features come ONLY from the joining day (day 0); the label comes from days 1-7.
CREATE OR REPLACE VIEW flood_it.player_features AS
WITH day0_events AS (
  SELECT
    e.player_id,
    COUNTIF(e.event_name = 'user_engagement')              AS d0_engagement_events,
    ROUND(SUM(IFNULL(e.engagement_time_msec, 0)) / 60000, 2) AS d0_engaged_minutes,
    COUNTIF(e.event_name = 'level_start_quickplay')        AS d0_levels_started,
    COUNTIF(e.event_name = 'level_end_quickplay')          AS d0_levels_ended,
    COUNTIF(e.event_name = 'level_complete_quickplay')     AS d0_levels_completed,
    COUNTIF(e.event_name = 'level_reset_quickplay')        AS d0_levels_reset,
    COUNTIF(e.event_name = 'post_score')                   AS d0_scores_posted,
    COUNTIF(e.event_name = 'spend_virtual_currency')       AS d0_currency_spends,
    COUNTIF(e.event_name = 'ad_reward')                    AS d0_ad_rewards,
    COUNTIF(e.event_name = 'challenge_a_friend')           AS d0_friend_challenges,
    COUNTIF(e.event_name = 'completed_5_levels')           AS d0_completed_5_levels,
    COUNTIF(e.event_name = 'use_extra_steps')              AS d0_extra_steps_used,
    COUNT(DISTINCT IF(e.event_name NOT IN ('os_update', 'app_update', 'app_remove', 'app_clear_data'), e.event_name, NULL)) AS d0_distinct_event_types   -- breadth of the game the player touched, ignoring automatic events
  FROM flood_it.stg_events AS e
  JOIN flood_it.dim_players AS p ON p.player_id = e.player_id
  WHERE p.is_new_player
    AND e.event_date = p.cohort_date                         -- joining day only: no information from the future
  GROUP BY e.player_id
),
day0_sessions AS (
  SELECT s.player_id,
         COUNT(*)                                            AS d0_sessions,
         ROUND(AVG(s.session_seconds) / 60, 2)               AS d0_avg_session_minutes
  FROM flood_it.fct_sessions AS s
  JOIN flood_it.dim_players AS p ON p.player_id = s.player_id
  WHERE p.is_new_player AND s.session_date = p.cohort_date
  GROUP BY s.player_id
)
SELECT
  p.player_id,
  p.cohort_date,
  EXTRACT(DAYOFWEEK FROM p.cohort_date)          AS cohort_day_of_week,   -- 1 = Sunday ... 7 = Saturday in BigQuery
  EXTRACT(HOUR FROM p.first_engagement_ts)       AS join_hour_utc,        -- late joiners have less of day 0 left
  p.platform,
  p.operating_system,
  p.country,
  p.device_language,
  IFNULL(d.d0_engagement_events, 0)    AS d0_engagement_events,
  IFNULL(d.d0_engaged_minutes, 0)      AS d0_engaged_minutes,
  IFNULL(d.d0_levels_started, 0)       AS d0_levels_started,
  IFNULL(d.d0_levels_ended, 0)         AS d0_levels_ended,
  IFNULL(d.d0_levels_completed, 0)     AS d0_levels_completed,
  IFNULL(d.d0_levels_reset, 0)         AS d0_levels_reset,
  IFNULL(d.d0_scores_posted, 0)        AS d0_scores_posted,
  IFNULL(d.d0_currency_spends, 0)      AS d0_currency_spends,
  IFNULL(d.d0_ad_rewards, 0)           AS d0_ad_rewards,
  IFNULL(d.d0_friend_challenges, 0)    AS d0_friend_challenges,
  IFNULL(d.d0_completed_5_levels, 0)   AS d0_completed_5_levels,
  IFNULL(d.d0_extra_steps_used, 0)     AS d0_extra_steps_used,
  IFNULL(d.d0_distinct_event_types, 0) AS d0_distinct_event_types,
  IFNULL(s.d0_sessions, 0)             AS d0_sessions,
  IFNULL(s.d0_avg_session_minutes, 0)  AS d0_avg_session_minutes,
  r.retained_d1,
  r.returned_within_7d,
  r.active_days_total,
  r.last_active_day_number,
  r.days_observable
FROM flood_it.dim_players AS p
JOIN flood_it.player_retention AS r ON r.player_id = p.player_id
LEFT JOIN day0_events AS d ON d.player_id = p.player_id
LEFT JOIN day0_sessions AS s ON s.player_id = p.player_id
WHERE p.is_new_player
  AND r.days_observable >= 7;                                -- everyone in the table had a full week to return
