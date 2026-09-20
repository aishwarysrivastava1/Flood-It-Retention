-- 01_overview.sql
-- Purpose: confirm the size and date range of the raw event data.
SELECT
  MIN(PARSE_DATE('%Y%m%d', event_date))  AS first_day,       -- event_date is text like '20180612', so convert it to a DATE
  MAX(PARSE_DATE('%Y%m%d', event_date))  AS last_day,        -- last day of data
  COUNT(DISTINCT event_date)             AS days_of_data,    -- number of distinct days
  COUNT(DISTINCT user_pseudo_id)         AS players,         -- user_pseudo_id = anonymous player id
  COUNT(*)                               AS events           -- one row = one event
FROM `firebase-public-project.analytics_153293282.events_*`; -- the * reads every daily table (events_20180612 ... events_20181003)
