-- 17_create_retention_by_segment.sql
-- Purpose: retention by platform and top-10 country (all others grouped together).
CREATE OR REPLACE VIEW flood_it.retention_by_segment AS
WITH country_rank AS (
  SELECT country, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, country) AS country_rank   -- 1 = country with the most new players; ties broken by name so exactly 10 are kept
  FROM flood_it.player_features
  GROUP BY country
)
SELECT
  f.platform,
  IF(c.country_rank <= 10, f.country, 'All other countries') AS country_group,
  COUNT(*)                                                   AS players,
  SUM(f.returned_within_7d)                                  AS returned_players,
  ROUND(100 * AVG(f.retained_d1), 2)                         AS d1_retention_pct,
  ROUND(100 * AVG(f.returned_within_7d), 2)                  AS returned_within_7d_pct
FROM flood_it.player_features AS f
JOIN country_rank AS c ON c.country = f.country
GROUP BY f.platform, country_group;
