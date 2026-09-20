# Metric Definitions

Every metric in this project, with its exact definition, where it is computed, and what can go wrong with it.
If someone disagrees with a number, this file is where the conversation starts.

## Activity

| Metric | Definition | Computed in | Watch out for |
|---|---|---|---|
| **Active day** | A calendar day on which a player fired at least one `user_engagement` event | `sql/08` (`HAVING` clause) | Automatic events such as `os_update` do **not** make a day active. Changing this definition changes DAU, retention and sessions at once |
| **DAU** | Distinct players active on a day | `sql/10` | Device-level ids, so one person on two devices counts twice |
| **WAU** | Distinct players active in the trailing 7 days (day − 6 through day) | `sql/10` | The first 6 days of the export have an incomplete window |
| **MAU (28-day)** | Distinct players active in the trailing 28 days | `sql/10` | Incomplete for the first 27 days; use `has_full_28d_window` |
| **Stickiness** | DAU ÷ 28-day MAU | `sql/10` | Meaningless while MAU is incomplete. Report the average only over full windows |
| **Session** | A run of interactive events with no gap longer than 30 minutes | `sql/09` | The 30-minute rule is a convention. Passive events are excluded before the gaps are measured |
| **Sessions per DAU** | Sessions started ÷ DAU, counted only on active player-days | `sql/10` | Without the active-day restriction this would mix two different populations |
| **Engaged minutes** | Sum of `engagement_time_msec` ÷ 60,000 | `sql/08` | GA4 attaches engagement time to several event types; summing all of them is the standard approach |

## New players and cohorts

| Metric | Definition | Computed in | Watch out for |
|---|---|---|---|
| **Cohort date** | The day of a player's first `user_engagement` event | `sql/07` | Taken from the same event row as `first_engagement_ts`, so the date and time never disagree |
| **New player** | A player whose cohort date is at least 7 days after the export begins | `sql/07` (`is_new_player`) | Week-1 players are excluded because they may have installed before the export started (left-censoring) |
| **Days observable** | Days between the cohort date and the last day of data | `sql/07` | The basis of every honest retention denominator |
| **First-seen players** | Players whose cohort date falls on a given day | `sql/10` | Includes week-1 players, so it is *not* the same as "new players" in the cohort analysis |

## Retention and churn

| Metric | Definition | Computed in | Watch out for |
|---|---|---|---|
| **DN retention** | Of players with at least N days of follow-up, the share active **exactly** N days after joining | `sql/11`, `sql/12` | "Exactly day N" is the classic definition. A rolling definition ("active on day N or later") gives higher numbers; say which you used |
| **Returned within 7 days** | Active on any day from 1 to 7 after joining | `sql/11` | This is the label source, not a retention metric. Do not compare it to D7 |
| **Churn (model label)** | `1 − returned_within_7d` | `notebooks/05` | Defined on new players with at least 7 days of follow-up only |
| **Churn (survival event)** | Silent for 7 or more days before the data ends | `notebooks/04` | Players still active near the end are **censored**, not churned |
| **Duration (survival)** | Days from joining to last active day, plus 1 | `notebooks/04` | The +1 makes the joining day count as day 1, so nobody has a duration of zero |
| **Cohort retention %** | Active players ÷ eligible players within a cohort week and day number | `sql/13` | Day 0 must always be 100%. If it is not, your activity and cohort definitions disagree |

## First-day progression

| Metric | Definition | Computed in | Watch out for |
|---|---|---|---|
| **Furthest milestone** | The deepest of: engaged, started a level, completed a level, completed 5 levels, on the joining day | `sql/15` | Descriptive only. Motivated players both progress further and return more |
| **Funnel steps 1-4** | Nested progression counts on the joining day | `sql/16` | Step 3 requires a recorded start *and* completion, so lost start events push players down a step |
| **Funnel steps 5-6** | Return outcomes measured on all new players | `sql/16` | Not a continuation of the funnel; they can exceed step 4 |
| **Completion rate** | Levels completed ÷ levels started on the joining day | `notebooks/03` | Undefined for players who never started a level; those are excluded, not zero-filled |

## Monetization proxies

This dataset contains **no revenue**. These are the closest available signals and must always be labelled as proxies.

| Metric | Definition | Computed in | Watch out for |
|---|---|---|---|
| **Ad rewards per DAU** | `ad_reward` events ÷ DAU | `sql/10` | A rewarded ad watched is not revenue; eCPM is unknown |
| **Currency spends per DAU** | `spend_virtual_currency` events ÷ DAU | `sql/10` | Spending earned currency costs the player nothing |

## Model metrics

| Metric | Definition | Baseline to beat | Watch out for |
|---|---|---|---|
| **ROC-AUC** | Probability the model scores a random churner above a random returner | 0.500 | Flattering under class imbalance |
| **PR-AUC (average precision)** | Area under the precision-recall curve | The churn rate itself | The right headline metric when positives are rare |
| **Log loss** | Penalty for confident wrong probabilities | — | Judges probabilities, not ranking |
| **Brier score** | Mean squared error of the predicted probabilities | — | Lower is better; pairs with the calibration curve |
| **Lift (decile 1)** | Churn rate in the riskiest 10% ÷ overall churn rate | 1.0 | The most business-legible number in the project |
| **Overfit gap** | Train ROC-AUC − test ROC-AUC | Near 0 | Report it; never hide it |
| **Concordance index** | Survival equivalent of ROC-AUC | 0.500 | From the Cox model |
| **ARI (segments)** | Agreement between clusterings from different random starts | Near 1.0 | Low values mean your segments are an artifact of the seed |
| **MAPE / MAE (forecast)** | Average percentage / absolute forecast error | Seasonal naive | If you cannot beat "same weekday last week", recommend the baseline |
