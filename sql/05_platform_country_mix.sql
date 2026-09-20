-- 05_platform_country_mix.sql
-- Purpose: see which platforms and countries players come from.
SELECT
  platform,                                                               -- ANDROID or IOS
  IFNULL(NULLIF(geo.country, ''), '(unknown)')           AS country,      -- turn empty text into a readable label
  COUNT(DISTINCT user_pseudo_id)                         AS players       -- distinct players
FROM `firebase-public-project.analytics_153293282.events_*`
GROUP BY platform, country
ORDER BY players DESC
LIMIT 25;
