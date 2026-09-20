-- 06_create_stg_events.sql
-- Purpose: one flat, clean view of the raw events with only the columns this project needs.
CREATE OR REPLACE VIEW flood_it.stg_events AS
SELECT
  user_pseudo_id                                     AS player_id,        -- rename to something readable
  PARSE_DATE('%Y%m%d', event_date)                   AS event_date,       -- text -> DATE (the app's reporting time zone)
  TIMESTAMP_MICROS(event_timestamp)                  AS event_ts,         -- microseconds -> TIMESTAMP (UTC)
  event_name,                                                             -- event type
  platform,                                                               -- ANDROID or IOS
  device.operating_system                            AS operating_system, -- nested field: device -> operating_system
  device.language                                    AS device_language,  -- device language setting
  IFNULL(NULLIF(geo.country, ''), '(unknown)')       AS country,          -- empty country -> '(unknown)'
  app_info.version                                   AS app_version,      -- game version
  (SELECT value.int_value
     FROM UNNEST(event_params)
    WHERE key = 'engagement_time_msec')              AS engagement_time_msec  -- pull ONE parameter out of the nested list
FROM `firebase-public-project.analytics_153293282.events_*`
WHERE user_pseudo_id IS NOT NULL;                                         -- events without a player cannot be analyzed
