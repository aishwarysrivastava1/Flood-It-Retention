# Data Dictionary

Every view in the `flood_it` dataset, its grain, and what each column means.
Generated from the actual view definitions, so it cannot drift from the SQL.

**Reading order:** `stg_events` feeds everything. `player_features` is the modeling table.

## `stg_events`

**Grain:** one row per event  
**Built by:** `sql/06`

| Column | Type | Meaning |
|---|---|---|
| `player_id` | VARCHAR | Anonymous device-level player id (`user_pseudo_id` in the raw data) |
| `event_date` | DATE | Calendar date of the event in the app's reporting time zone |
| `event_ts` | TIMESTAMP | Exact event time in UTC (converted from microseconds) |
| `event_name` | VARCHAR | What happened, e.g. `user_engagement`, `level_complete_quickplay` |
| `platform` | VARCHAR | ANDROID or IOS |
| `operating_system` | VARCHAR | Device operating system |
| `device_language` | VARCHAR | Device language setting |
| `country` | VARCHAR | Country, with empty and missing values replaced by `(unknown)` |
| `app_version` | VARCHAR | Game version the event came from |
| `engagement_time_msec` | BIGINT | Milliseconds of engagement attached to this event; NULL on events that carry no engagement time |

## `dim_players`

**Grain:** one row per player  
**Built by:** `sql/07`

| Column | Type | Meaning |
|---|---|---|
| `player_id` | VARCHAR | One row per player |
| `cohort_date` | DATE | Day of the player's first `user_engagement` event; the day they 'joined' |
| `first_engagement_ts` | TIMESTAMP | Exact UTC time of that first engagement (same event row as `cohort_date`) |
| `platform` | VARCHAR | Platform recorded at first engagement |
| `operating_system` | VARCHAR | OS recorded at first engagement |
| `country` | VARCHAR | Country recorded at first engagement |
| `device_language` | VARCHAR | Language recorded at first engagement |
| `app_version` | VARCHAR | Game version at first engagement |
| `days_observable` | BIGINT | Days of follow-up available between joining and the last day of data. Guards against right-censoring |
| `is_new_player` | BOOLEAN | TRUE when the player joined at least 7 days after the export starts. Guards against left-censoring |

## `fct_player_days`

**Grain:** one row per player per active day  
**Built by:** `sql/08`

| Column | Type | Meaning |
|---|---|---|
| `player_id` | VARCHAR | Player |
| `activity_date` | DATE | An **active** day (at least one `user_engagement` event) |
| `engagement_events` | HUGEINT | Count of `user_engagement` events that day |
| `engaged_minutes` | DOUBLE | Sum of `engagement_time_msec` that day, converted to minutes |
| `levels_started` | HUGEINT | Count of `level_start_quickplay` events |
| `levels_completed` | HUGEINT | Count of `level_complete_quickplay` events |
| `ad_rewards` | HUGEINT | Count of `ad_reward` events (rewarded-ad monetization proxy) |
| `currency_spends` | HUGEINT | Count of `spend_virtual_currency` events (in-game economy proxy) |

## `fct_sessions`

**Grain:** one row per session  
**Built by:** `sql/09`

| Column | Type | Meaning |
|---|---|---|
| `player_id` | VARCHAR | Player |
| `session_number` | HUGEINT | Running session number for that player, 1 upwards |
| `session_date` | DATE | Reporting-time-zone date on which the session started |
| `session_start_ts` | TIMESTAMP | First event time in the session (UTC) |
| `session_end_ts` | TIMESTAMP | Last event time in the session (UTC) |
| `session_seconds` | BIGINT | Seconds between the first and last event. A single-event session is 0 |
| `events_in_session` | BIGINT | Number of events in the session |

## `kpi_daily`

**Grain:** one row per calendar day  
**Built by:** `sql/10`

| Column | Type | Meaning |
|---|---|---|
| `day` | DATE | Calendar day |
| `dau` | BIGINT | Distinct players active that day |
| `wau` | BIGINT | Distinct players active in the trailing 7 days |
| `mau_28d` | BIGINT | Distinct players active in the trailing 28 days |
| `stickiness_dau_mau` | DOUBLE | DAU divided by 28-day MAU. Only meaningful where `has_full_28d_window` is TRUE |
| `first_seen_players` | BIGINT | Players whose cohort date is this day (includes possibly pre-existing players from week 1) |
| `sessions` | BIGINT | Sessions started that day, counted only on genuinely active player-days |
| `sessions_per_dau` | DOUBLE | Sessions divided by DAU |
| `minutes_per_dau` | DOUBLE | Engaged minutes divided by DAU |
| `levels_per_dau` | DOUBLE | Levels started divided by DAU |
| `ad_rewards_per_dau` | DOUBLE | Rewarded ads divided by DAU |
| `currency_spends_per_dau` | DOUBLE | Currency spends divided by DAU |
| `has_full_28d_window` | BOOLEAN | FALSE for the first 27 days, where MAU has an incomplete window and stickiness is inflated |

## `player_retention`

**Grain:** one row per new player  
**Built by:** `sql/11`

| Column | Type | Meaning |
|---|---|---|
| `player_id` | VARCHAR | New player |
| `cohort_date` | DATE | Joining day |
| `days_observable` | BIGINT | Days of follow-up available |
| `retained_d1` | INTEGER | 1 if active exactly 1 day after joining |
| `retained_d3` | INTEGER | 1 if active exactly 3 days after joining |
| `retained_d7` | INTEGER | 1 if active exactly 7 days after joining |
| `retained_d14` | INTEGER | 1 if active exactly 14 days after joining |
| `retained_d30` | INTEGER | 1 if active exactly 30 days after joining |
| `returned_within_7d` | INTEGER | 1 if active on any day from 1 to 7. This is the source of the churn label |
| `active_days_total` | BIGINT | Total distinct active days observed |
| `last_active_day_number` | BIGINT | Days between joining and the last active day. Used for survival analysis |

## `retention_summary`

**Grain:** one row per retention day  
**Built by:** `sql/12`

| Column | Type | Meaning |
|---|---|---|
| `retention_day` | VARCHAR | Label: D1, D3, D7, D14 or D30 |
| `day_number` | INTEGER | 1, 3, 7, 14 or 30 |
| `eligible_players` | HUGEINT | Players with enough follow-up to have this outcome (the honest denominator) |
| `retained_players` | HUGEINT | Eligible players who were active on that day |
| `retention_pct` | DOUBLE | retained / eligible, as a percentage |

## `retention_cohorts_weekly`

**Grain:** one row per cohort week per day number  
**Built by:** `sql/13`

| Column | Type | Meaning |
|---|---|---|
| `cohort_week` | TIMESTAMP | Monday of the week the players joined |
| `day_number` | BIGINT | Days since joining, 0 to 30 |
| `eligible_players` | BIGINT | Players in that cohort week with enough follow-up for this day number |
| `active_players` | BIGINT | Of those, how many were active |
| `retention_pct` | DOUBLE | active / eligible, as a percentage. Day 0 must always be 100% |

## `player_features`

**Grain:** one row per new player with 7+ days of follow-up  
**Built by:** `sql/14`

| Column | Type | Meaning |
|---|---|---|
| `player_id` | VARCHAR | New player with at least 7 days of follow-up |
| `cohort_date` | DATE | Joining day |
| `cohort_day_of_week` | BIGINT | Day of week of joining (BigQuery: 1 = Sunday) |
| `join_hour_utc` | BIGINT | UTC hour of first engagement. Late joiners have less of day 0 left |
| `platform` | VARCHAR | ANDROID or IOS |
| `operating_system` | VARCHAR | Device OS |
| `country` | VARCHAR | Country at first engagement |
| `device_language` | VARCHAR | Device language |
| `d0_engagement_events` | HUGEINT | FEATURE. `user_engagement` events on the joining day |
| `d0_engaged_minutes` | DOUBLE | FEATURE. Engaged minutes on the joining day |
| `d0_levels_started` | HUGEINT | FEATURE. Levels started on the joining day |
| `d0_levels_ended` | HUGEINT | FEATURE. Levels ended on the joining day |
| `d0_levels_completed` | HUGEINT | FEATURE. Levels completed on the joining day |
| `d0_levels_reset` | HUGEINT | FEATURE. Level resets on the joining day (a frustration signal) |
| `d0_scores_posted` | HUGEINT | FEATURE. Scores posted on the joining day |
| `d0_currency_spends` | HUGEINT | FEATURE. Virtual currency spends on the joining day |
| `d0_ad_rewards` | HUGEINT | FEATURE. Rewarded ads watched on the joining day |
| `d0_friend_challenges` | HUGEINT | FEATURE. Friend challenges on the joining day (a social signal) |
| `d0_completed_5_levels` | HUGEINT | FEATURE. Whether the 5-level milestone fired on the joining day |
| `d0_extra_steps_used` | HUGEINT | FEATURE. Extra steps used on the joining day |
| `d0_distinct_event_types` | BIGINT | FEATURE. Distinct game event types touched on the joining day, ignoring automatic events. A breadth measure |
| `d0_sessions` | BIGINT | FEATURE. Sessions on the joining day |
| `d0_avg_session_minutes` | DOUBLE | FEATURE. Average session length on the joining day |
| `retained_d1` | INTEGER | OUTCOME. Active exactly 1 day after joining |
| `returned_within_7d` | INTEGER | LABEL SOURCE. Churn target is `1 - returned_within_7d` |
| `active_days_total` | BIGINT | OUTCOME. Total active days. Never use as a feature |
| `last_active_day_number` | BIGINT | OUTCOME. Used for survival analysis. Never use as a feature |
| `days_observable` | BIGINT | Follow-up days. Always 7 or more in this view |

## `retention_by_milestone`

**Grain:** one row per milestone group  
**Built by:** `sql/15`

| Column | Type | Meaning |
|---|---|---|
| `furthest_milestone_day0` | VARCHAR | How far the player got on the joining day |
| `players` | BIGINT | Players in that milestone group |
| `retained_d1_players` | HUGEINT | Of those, how many returned on day 1 |
| `returned_players` | HUGEINT | Of those, how many returned within 7 days |
| `d1_retention_pct` | DOUBLE | Day-1 return rate for the group |
| `returned_within_7d_pct` | DOUBLE | 7-day return rate for the group |

## `first_day_funnel`

**Grain:** one row per funnel step  
**Built by:** `sql/16`

| Column | Type | Meaning |
|---|---|---|
| `step_order` | INTEGER | 1 to 6; steps 1-4 are nested, 5-6 are outcomes for all new players |
| `step` | VARCHAR | Readable step name |
| `players` | HUGEINT | Players reaching that step |

## `retention_by_segment`

**Grain:** one row per platform and country group  
**Built by:** `sql/17`

| Column | Type | Meaning |
|---|---|---|
| `platform` | VARCHAR | ANDROID or IOS |
| `country_group` | VARCHAR | Top-10 country by new players, or `All other countries` |
| `players` | BIGINT | New players in that platform and country group |
| `returned_players` | HUGEINT | Of those, how many returned within 7 days |
| `d1_retention_pct` | DOUBLE | Day-1 return rate for the segment |
| `returned_within_7d_pct` | DOUBLE | 7-day return rate for the segment |

## Columns you must never use as model features

These describe what happened **after** the joining day. Using any of them as a feature is leakage:

- `retained_d1`, `retained_d3`, `retained_d7`, `retained_d14`, `retained_d30`
- `returned_within_7d`
- `active_days_total`
- `last_active_day_number`
- `days_observable`

The model's feature list is every column starting with `d0_`, plus `join_hour_utc`, `cohort_day_of_week`, `platform` and `country`.
