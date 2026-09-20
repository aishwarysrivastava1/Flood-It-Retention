-- 03_event_param_keys.sql
-- Purpose: discover which parameters (extra details) each event carries, and their data types.
SELECT
  e.event_name,                                                                  -- event type
  p.key                                                     AS param_key,        -- parameter name, e.g. engagement_time_msec
  COUNT(*)                                                  AS occurrences,      -- how often this key appears on this event
  COUNTIF(p.value.string_value IS NOT NULL)                 AS text_values,      -- stored as text
  COUNTIF(p.value.int_value IS NOT NULL)                    AS integer_values,   -- stored as whole number
  COUNTIF(p.value.double_value IS NOT NULL OR p.value.float_value IS NOT NULL) AS decimal_values  -- stored as decimal
FROM `firebase-public-project.analytics_153293282.events_*` AS e,
  UNNEST(e.event_params) AS p                                                    -- UNNEST turns the nested list into one row per parameter
GROUP BY e.event_name, p.key
ORDER BY e.event_name, occurrences DESC;
