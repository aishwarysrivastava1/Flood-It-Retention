-- 10_create_kpi_daily.sql
-- Purpose: daily KPI table: DAU, WAU, 28-day MAU, stickiness, sessions, engagement and economy proxies.
CREATE OR REPLACE VIEW flood_it.kpi_daily AS
WITH days AS (
  SELECT DISTINCT activity_date AS day FROM flood_it.fct_player_days
),
rolling AS (
  SELECT
    d.day,
    COUNT(DISTINCT IF(p.activity_date = d.day, p.player_id, NULL))                          AS dau,     -- active today
    COUNT(DISTINCT IF(p.activity_date > DATE_SUB(d.day, INTERVAL 7 DAY), p.player_id, NULL)) AS wau,     -- active in last 7 days
    COUNT(DISTINCT p.player_id)                                                             AS mau_28d  -- active in last 28 days
  FROM days AS d
  JOIN flood_it.fct_player_days AS p
    ON p.activity_date BETWEEN DATE_SUB(d.day, INTERVAL 27 DAY) AND d.day                 -- range join: each day sees its trailing 28 days
  GROUP BY d.day
),
daily_totals AS (
  SELECT activity_date AS day,
         SUM(engaged_minutes) AS engaged_minutes, SUM(levels_started) AS levels_started,
         SUM(ad_rewards) AS ad_rewards, SUM(currency_spends) AS currency_spends
  FROM flood_it.fct_player_days
  GROUP BY activity_date
),
first_seen AS (
  SELECT cohort_date AS day, COUNT(*) AS first_seen_players FROM flood_it.dim_players GROUP BY cohort_date
),
sessions AS (
  SELECT s.session_date AS day, COUNT(*) AS sessions
  FROM flood_it.fct_sessions AS s
  JOIN flood_it.fct_player_days AS p                                        -- keep only sessions on days the player was genuinely active
    ON p.player_id = s.player_id AND p.activity_date = s.session_date       -- so sessions_per_dau uses the same population as DAU
  GROUP BY s.session_date
)
SELECT
  r.day,
  r.dau,
  r.wau,
  r.mau_28d,
  ROUND(SAFE_DIVIDE(r.dau, r.mau_28d), 4)                          AS stickiness_dau_mau,
  IFNULL(f.first_seen_players, 0)                                  AS first_seen_players,
  IFNULL(s.sessions, 0)                                            AS sessions,
  ROUND(SAFE_DIVIDE(IFNULL(s.sessions, 0), r.dau), 3)              AS sessions_per_dau,
  ROUND(SAFE_DIVIDE(t.engaged_minutes, r.dau), 3)                  AS minutes_per_dau,
  ROUND(SAFE_DIVIDE(t.levels_started, r.dau), 3)                   AS levels_per_dau,
  ROUND(SAFE_DIVIDE(t.ad_rewards, r.dau), 4)                       AS ad_rewards_per_dau,
  ROUND(SAFE_DIVIDE(t.currency_spends, r.dau), 4)                  AS currency_spends_per_dau,
  r.day >= DATE_ADD((SELECT MIN(day) FROM days), INTERVAL 27 DAY)  AS has_full_28d_window   -- MAU is incomplete in the first 27 days
FROM rolling AS r
JOIN daily_totals AS t ON t.day = r.day
LEFT JOIN first_seen AS f ON f.day = r.day
LEFT JOIN sessions AS s ON s.day = r.day;
