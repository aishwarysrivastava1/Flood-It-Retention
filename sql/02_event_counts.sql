-- 02_event_counts.sql
-- Purpose: list every event type, how often it happens and how many players trigger it.
SELECT
  event_name,                                                                   -- type of event
  COUNT(*)                                                    AS events,        -- how many times it happened
  COUNT(DISTINCT user_pseudo_id)                              AS players,       -- how many different players triggered it
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)            AS share_of_events_pct  -- window function: share of all events
FROM `firebase-public-project.analytics_153293282.events_*`
GROUP BY event_name
ORDER BY events DESC;
