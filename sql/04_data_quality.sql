-- 04_data_quality.sql
-- Purpose: measure missing ids, exact duplicate events and placeholder values before trusting any metric.
WITH base AS (
  SELECT
    user_pseudo_id,                                        -- player id
    event_timestamp,                                       -- microseconds since 1970
    event_name,                                            -- event type
    geo.country             AS country,                    -- country (may hold placeholders)
    device.operating_system AS operating_system            -- OS (may hold placeholders)
  FROM `firebase-public-project.analytics_153293282.events_*`
),
duplicates AS (
  SELECT user_pseudo_id, event_timestamp, event_name, COUNT(*) AS copies   -- identical player + time + event
  FROM base
  GROUP BY user_pseudo_id, event_timestamp, event_name
  HAVING COUNT(*) > 1                                                      -- keep only repeated combinations
)
SELECT
  (SELECT COUNT(*) FROM base)                                                        AS total_events,
  (SELECT COUNTIF(user_pseudo_id IS NULL) FROM base)                                 AS events_missing_player_id,
  (SELECT IFNULL(SUM(copies - 1), 0) FROM duplicates)                                AS extra_duplicate_rows,
  (SELECT COUNTIF(country IS NULL OR country IN ('', '(not set)', '<Other>')) FROM base) AS events_placeholder_country,
  (SELECT COUNTIF(operating_system IS NULL OR operating_system IN ('', '(not set)', '<Other>')) FROM base) AS events_placeholder_os;
