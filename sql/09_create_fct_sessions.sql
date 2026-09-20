-- 09_create_fct_sessions.sql
-- Purpose: rebuild sessions from raw events: a new session starts after 30+ minutes of inactivity.
CREATE OR REPLACE VIEW flood_it.fct_sessions AS
WITH interactive AS (
  SELECT player_id, event_ts, event_date
  FROM flood_it.stg_events
  WHERE event_name NOT IN ('app_remove', 'os_update', 'app_update', 'app_clear_data')   -- ignore events the player did not actively trigger
),
gaps AS (
  SELECT
    player_id, event_ts, event_date,
    TIMESTAMP_DIFF(event_ts,
                   LAG(event_ts) OVER (PARTITION BY player_id ORDER BY event_ts),        -- previous event time for the same player
                   SECOND)                                   AS seconds_since_previous    -- seconds, because MINUTE truncates (30.9 min would count as 30)
  FROM interactive
),
flagged AS (
  SELECT
    player_id, event_ts, event_date,
    IF(seconds_since_previous IS NULL OR seconds_since_previous > 30 * 60, 1, 0) AS is_new_session  -- first event or a gap over 30 minutes = new session
  FROM gaps
),
numbered AS (
  SELECT
    player_id, event_ts, event_date,
    SUM(is_new_session) OVER (PARTITION BY player_id ORDER BY event_ts
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_number  -- running total = session id
  FROM flagged
)
SELECT
  player_id,
  session_number,
  MIN(event_date)                                      AS session_date,       -- reporting-time-zone date of the session start
  MIN(event_ts)                                        AS session_start_ts,
  MAX(event_ts)                                        AS session_end_ts,
  TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), SECOND) AS session_seconds,    -- time between first and last event
  COUNT(*)                                             AS events_in_session
FROM numbered
GROUP BY player_id, session_number;
