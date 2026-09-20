# Looker Studio Dashboard

**Public link:** [paste your link here after sharing with "Anyone with the link · Viewer"]

## Data sources (all BigQuery views in the `flood_it` dataset)
- `kpi_daily`
- `retention_summary`
- `retention_cohorts_weekly`
- `first_day_funnel`
- `retention_by_segment`
- `retention_by_milestone`

## Page 1: Engagement overview
| Chart | Type | Source | Setup |
|---|---|---|---|
| Avg DAU | Scorecard | kpi_daily | `dau`, Average |
| Avg stickiness | Scorecard | kpi_daily | `stickiness_dau_mau`, Average, Percent; filter `has_full_28d_window = true` |
| Total new players | Scorecard | kpi_daily | `first_seen_players`, Sum |
| DAU and WAU over time | Time series | kpi_daily | Dimension `day`; metrics `dau`, `wau` |
| Per-player engagement | Time series | kpi_daily | Dimension `day`; metrics `sessions_per_dau`, `minutes_per_dau` |
| Date range control | Control | kpi_daily | — |

Caveat text box: "MAU and stickiness need a full 28-day window; earlier days are
excluded from the stickiness average."

## Page 2: Retention
| Chart | Type | Source | Setup |
|---|---|---|---|
| Retention by day | Bar | retention_summary | `retention_day` x `retention_pct`, sorted by `day_number` |
| Cohort heatmap | Pivot table with heatmap | retention_cohorts_weekly | Row `cohort_week`, column `day_number`, metric `retention_pct` (Average); filter `day_number <= 28` |
| Cohort sizes | Bar | retention_cohorts_weekly | Row `cohort_week`, metric `eligible_players` where `day_number = 0` |

Caveat text box: "Retention counts only players observed long enough for each day.
Players first seen in the first 7 days of the export are excluded."

## Page 3: First day and segments
| Chart | Type | Source | Setup |
|---|---|---|---|
| First-day funnel | Horizontal bar | first_day_funnel | `step` x `players`, sorted by `step_order` |
| Retention by milestone | Column | retention_by_milestone | `furthest_milestone_day0` x `d1_retention_pct`, `returned_within_7d_pct` |
| Platform and country table | Table with bars | retention_by_segment | Dimensions `platform`, `country_group`; metrics `players`, `returned_within_7d_pct` |
| Platform filter | Control | retention_by_segment | Drop-down on `platform` |

Caveat text box: "Milestone comparisons are descriptive, not causal. Motivated players
both progress further and return more often."
