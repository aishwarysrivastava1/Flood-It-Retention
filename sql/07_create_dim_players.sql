-- 07_create_dim_players.sql
-- Purpose: one row per player with their cohort (first engagement day) and first-seen attributes.
CREATE OR REPLACE VIEW flood_it.dim_players AS
WITH data_window AS (
  SELECT MIN(event_date) AS first_data_day,                -- first day in the dataset
         MAX(event_date) AS last_data_day                  -- last day in the dataset
  FROM flood_it.stg_events
),
first_engagement AS (
  SELECT
    player_id,
    event_ts   AS first_engagement_ts,                     -- exact time of the first real engagement
    event_date AS cohort_date,                             -- the day the player "joined", taken from the SAME row as the timestamp
    platform, operating_system, country, device_language, app_version   -- attributes as they were at that first engagement
  FROM (
    SELECT
      player_id, event_ts, event_date, platform, operating_system, country, device_language, app_version,
      ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY event_ts, event_date) AS row_num  -- 1 = the player's earliest engagement row
    FROM flood_it.stg_events
    WHERE event_name = 'user_engagement'                   -- engagement = the player actually used the app
  )
  WHERE row_num = 1                                        -- keep only that earliest row per player
)
SELECT
  f.player_id,
  f.cohort_date,
  f.first_engagement_ts,
  f.platform,
  f.operating_system,
  f.country,
  f.device_language,
  f.app_version,
  DATE_DIFF(w.last_data_day, f.cohort_date, DAY)                 AS days_observable,  -- days of follow-up available after joining
  f.cohort_date >= DATE_ADD(w.first_data_day, INTERVAL 7 DAY)    AS is_new_player     -- skip week 1: those may be older players (left-censoring)
FROM first_engagement AS f
CROSS JOIN data_window AS w;                                     -- attach the single date-window row to every player
