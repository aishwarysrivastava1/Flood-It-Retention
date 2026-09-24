# Player Retention and Churn: Findings and Recommendations
## Flood-It! mobile game, 2018-06-12 to 2018-10-03

**To:** Game and product team
**From:** Aishwary Srivastava
**Date:** 2026-09-24
**Source:** `firebase-public-project.analytics_153293282` — 5,700,000 raw GA4 events, 15,175 device-level players, 114 days
**Reproduce:** every number below comes from `notebooks/02`–`07`, run on the BigQuery views in `sql/`

---

## Summary

**Flood-It! is running on a treadmill.** Daily active players are flat across the whole window
(503.9 average in the first four weeks, 497.3 in the last four, −1.3%), while the game takes on about
119 new players a day. Acquisition is replacing churn rather than adding to the base.

The churn happens almost immediately: **71.4% of new players never return within 7 days**, and the
Kaplan-Meier median time to churn is **1 day** — half of all new players are gone after their first
day. D1 retention is **13.3%** (95% CI 12.7–14.0); D30 is **2.6%** (2.3–3.0).

The clearest lever is the first day. **66.9% of new players start a level, but only 42.6% of those
complete one.** Players who complete a level on day 0 return within 7 days at 35.4%, against 23.9% for
players who never start one. That gap is an association, not a proven cause, so it belongs in an A/B
test rather than in a roadmap commitment.

A churn model trained on day-0 behaviour and validated on later cohorts reaches **test ROC-AUC 0.677**
(baseline 0.500) and **PR-AUC 0.854** (base rate 0.758). It ranks players usefully but not sharply: the
riskiest decile churns at 88.8% against an average of 75.8%, a lift of **1.17×**. With churn this common,
a broad onboarding fix is worth more than targeted rescue offers.

---

## Key findings

### 1. Engagement is flat, and the base churns as fast as it grows

| Metric | Value |
|---|---|
| Average DAU | 471.4 |
| Average 28-day MAU (full windows only) | 4,629.4 |
| Stickiness (DAU ÷ MAU) | 10.1% (range 6.7%–13.8%) |
| Sessions per active player | 1.55 |
| Engaged minutes per active player | 12.2 |
| Rewarded ads per active player | 0.035 |
| New players first seen | 13,588 over 114 days (≈119/day) |
| DAU trend, first 4 weeks → last 4 weeks | 503.9 → 497.3 (−1.3%) |

10% stickiness means a typical monthly player opens the game about three days a month. Flat DAU
alongside 119 new players a day is the treadmill: the game is buying back the players it loses.

### 2. Retention: almost all of the loss happens on day 1

| Day | Eligible players | Retained | Retention | 95% CI (Wilson) |
|---|---|---|---|---|
| D1 | 11,645 | 1,552 | **13.33%** | 12.72 – 13.96 |
| D3 | 11,479 | 880 | 7.67% | 7.19 – 8.17 |
| D7 | 11,066 | 558 | **5.04%** | 4.65 – 5.47 |
| D14 | 10,360 | 433 | 4.18% | 3.81 – 4.58 |
| D30 | 8,281 | 216 | **2.61%** | 2.29 – 2.97 |

Denominators shrink because each day counts only players with that much follow-up left in the window.

Survival analysis on the same players (90.4% observed churn, 9.6% censored) gives a **median survival of
1 day**. The probability a new player is still active is 45.7% after day 1, 34.0% after day 7 and 21.2%
after day 30. D7 retention ranges from 2.5% to 11.1% across the 16 weekly cohorts with no monotonic
trend, so nothing in this window looks like a release that moved retention.

### 3. The first day decides most of it

| Funnel step (11,066 new players with a full week of follow-up) | Players | % of joiners |
|---|---|---|
| Joined (first `user_engagement`) | 11,066 | 100.0% |
| Started a level on day 0 | 7,398 | 66.9% |
| Completed a level on day 0 | 3,151 | 28.5% |
| Completed 5+ levels on day 0 | 542 | 4.9% |
| *Outcome:* returned on day 1 | 1,493 | 13.5% |
| *Outcome:* returned within 7 days | 3,170 | 28.6% |

**The biggest single drop is level start → level completion: −38.4 points of all joiners.** 57.4% of
players who start a level on their first day never finish one. The event dictionary supports a
difficulty reading: the export holds 137,035 `level_fail_quickplay` events across 6,343 players.

Return rate rises with first-day progress (χ² = 221.7, df = 3, p = 8.8 × 10⁻⁴⁸):

| Furthest progress on day 0 | Players | Returned on day 1 | Returned within 7 days |
|---|---|---|---|
| Engaged, no level started | 3,664 | 11.60% | 23.94% |
| Started a level only | 4,247 | 11.63% | 25.97% |
| Completed a level | 2,613 | 16.34% | 35.40% |
| Completed 5+ levels | 542 | 27.12% | 48.89% |

This is **descriptive, not causal**. Motivated players both progress further and return more often.

### 4. What predicts coming back: time and depth, not rewards

Mann-Whitney U with rank-biserial effect sizes, Holm-corrected, over 15 day-0 features:

| Feature | Median (returned) | Median (churned) | Effect size | Holm p |
|---|---|---|---|---|
| Engaged minutes | 4.66 | 2.13 | **0.287** | < 0.0001 |
| Average session minutes | 5.92 | 3.42 | **0.270** | < 0.0001 |
| Engagement events | 13 | 8 | 0.259 | < 0.0001 |
| Scores posted | 1 | 0 | 0.237 | < 0.0001 |
| Distinct event types | 9 | 8 | 0.209 | < 0.0001 |
| Rewarded ads watched | 0 | 0 | 0.006 | 0.015 |
| Friend challenges | 0 | 0 | 0.004 | 0.025 |

Rewarded ads and friend challenges are statistically significant and **practically irrelevant** — which
is exactly what a 0.006 effect size on 11,066 players means. Platform is the same story: χ² p = 0.15,
Cramér's V = 0.014.

The Cox model agrees on direction: each unit of log engaged minutes multiplies churn hazard by 0.916
(0.896–0.937), log levels completed by 0.849 (0.817–0.881), day-0 sessions by 0.928 (0.897–0.961).
Concordance 0.594. Proportional hazards fails for all three, so these are average effects over the
window rather than constant ones.

### 5. At-risk players can be ranked on day 1, but only roughly

Out-of-time split: trained on cohorts up to 2018-09-04 (8,470 players, 70.0% churn), tested on later
cohorts (2,596 players, 75.8% churn). Later cohorts churn more, which is itself worth watching.

| Model | CV ROC-AUC | Train AUC | Test AUC | Test PR-AUC | Overfit gap |
|---|---|---|---|---|---|
| Baseline (majority) | 0.500 | 0.500 | 0.500 | 0.758 | 0.000 |
| Logistic regression | 0.665 ± 0.011 | 0.670 | 0.671 | 0.849 | −0.001 |
| Random forest | 0.674 ± 0.008 | 0.770 | 0.680 | 0.854 | 0.091 |
| Gradient boosting (untuned) | 0.649 ± 0.010 | **0.905** | 0.646 | 0.832 | **0.259** |
| Gradient boosting (tuned) | 0.673 | — | **0.677** | **0.854** | small |

The untuned booster is the textbook overfit: near-perfect on training players, worst of the four on new
cohorts. Tuning traded raw fit for generalisation and won back 0.03 AUC on the test set.

Targeting value, from the decile lift table:

| Decile by predicted risk | Churn rate | Lift | Cumulative share of churners |
|---|---|---|---|
| 1 (riskiest 10%) | 88.8% | 1.17× | 11.7% |
| 1–3 (riskiest 30%) | 87.0% | 1.15× | 34.5% |
| 10 (safest 10%) | 48.8% | 0.64× | 100% |

Permutation importance ranks `d0_sessions` (0.045 AUC drop), `d0_avg_session_minutes` (0.038) and
`d0_levels_completed` (0.032) first, well clear of everything else. `join_hour_utc` (0.007) still helps,
because a player who first opens the game at 23:50 has ten minutes of "day 0" left. Ad rewards, currency
spends and country contribute nothing measurable, and shuffling them slightly *improves* the score. Logistic odds ratios agree: one standard deviation more day-0 sessions multiplies churn odds
by 0.68.

Calibration is good (Brier 0.174 against 0.187 for the baseline), so the probabilities can carry a
threshold. Under **invented** economics (10 value units per saved player, 0.5 per offer), targeting the
riskiest 10% breaks even at a **5.6% save rate** and returns about +100 units at a 10% save rate.

### 6. Player types: one huge low-intent segment

K-means on day-0 behaviour only (K = 5, silhouette 0.419, chosen inside the 3–6 range a team can act on).
Retention was **not** an input. Stability across five seeds: **ARI 0.994**, so the segments are structure,
not seed noise. Return rates differ strongly (χ² = 614.7, df = 4, p ≈ 1 × 10⁻¹³¹):

| Segment | Players | Share | Median day-0 minutes | Median levels started | Returned within 7 days |
|---|---|---|---|---|---|
| Quick bouncers | 6,612 | 59.8% | 1.25 | 0 | **21.6%** |
| Light samplers | 2,458 | 22.2% | 4.70 | 3 | 31.9% |
| Steady players | 692 | 6.3% | 8.78 | 4 | 38.0% |
| Keen progressors — the only ad-watching group (2.6 rewarded ads on day 0) | 140 | 1.3% | 10.90 | 4 | 39.3% |
| Power players | 1,164 | 10.5% | 12.77 | 5 | **55.2%** |

Three in five new players are "quick bouncers" who spend about 75 seconds in the game and never start a
level. That one segment is the retention problem.

### 7. Unusual days: 8 of 100, and the shape points at tracking

STL decomposition (7-day season, robust) plus a MAD-based robust z-score (|z| > 3.5) over the 100-day
window that remains after excluding the first 14 days as ramp-up:

| Day | DAU vs expected | Sessions/player | Minutes/player | Levels/player | Reading |
|---|---|---|---|---|---|
| 2018-06-27 | 0.66× | 1.05 | 1.50 | 1.13 | fewer players, each heavier |
| 2018-07-01 | **1.72×** | 1.06 | 1.13 | 1.04 | acquisition spike |
| 2018-07-03 | 0.73× | 1.07 | 1.33 | 1.03 | fewer players, each heavier |
| 2018-07-05 | 0.70× | 1.00 | 1.28 | 1.21 | fewer players, each heavier |
| 2018-07-07 | 0.68× | 1.02 | 1.26 | 1.13 | fewer players, each heavier |
| 2018-07-14 | 0.70× | 1.02 | 1.21 | 1.26 | fewer players, each heavier |
| 2018-08-10 | 0.74× | 0.97 | 1.23 | 1.18 | fewer players, each heavier |
| 2018-09-20 | 0.77× | 1.02 | 1.07 | 1.30 | fewer players, each heavier |

On the seven low days DAU falls 23–34% while sessions per player stay normal and minutes per player
*rise* 7–50%. The players who were recorded behaved normally or more heavily, so the missing mass is
light players. That is consistent with **partial event loss** rather than an engagement collapse: a real
behaviour change moves the per-player ratios, not just the headcount. It cannot be confirmed from the
export alone, so it is a question for the data-engineering team, not a conclusion.

2018-07-01 is the opposite shape: 72% more players, all behaving normally — an acquisition spike.

### 8. Two-week outlook: use the naive baseline

Backtest on the final 14 days, with anomalies replaced by expected values before fitting:

| Method | MAPE | MAE |
|---|---|---|
| **Seasonal naive** (same weekday last week) | **7.70%** | **40.9** |
| ETS (additive, damped trend, 7-day season) | 11.59% | 62.8 |

**The naive baseline wins, so that is the recommendation for planning.** The ETS forecast for
2018-10-04 → 2018-10-17 sits between 450 and 609 DAU with 95% prediction intervals from roughly 310 to
745 — consistent with a flat series and wide uncertainty rather than a useful signal.

---

## Recommendations

1. **Fix the first-level completion gap, and test it.** 57.4% of players who start a level on day 0 never
   finish one, and completing one is associated with an 11.5-point higher 7-day return rate (35.4% vs 23.9%). The hypothesis
   worth testing is that the first three levels are too hard or too slow: add a hint, a penalty-free retry,
   or an easier opening ladder, then measure D1 return in an A/B test. Do not treat the descriptive gap as
   a proven cause.
2. **Prefer a broad onboarding change over targeted rescue offers.** The model ranks risk usefully
   (PR-AUC 0.854 vs 0.758 base), but churn is so common that the riskiest decile carries only 1.17× the
   average rate. Under the assumed economics, offers pay only above a 5.6% save rate. If an offer is run
   anyway, target decile 1 and instrument the save rate so that assumption becomes a measurement.
3. **Send the seven low-DAU days to data engineering before treating them as behaviour.** Deploy logs and
   pipeline history for 2018-06-27, 07-03, 07-05, 07-07, 07-14, 08-10 and 09-20 should be checked first.
   Separately, the game emits two parallel sets of level events (quickplay and a second mode) and
   `completed_5_levels` spans both, so it cannot be used as a progression milestone; one canonical
   level-progression event would remove that ambiguity.
4. **Instrument for the questions this data cannot answer.** Add level identifiers and difficulty to level
   events, a tutorial-completion event, cross-device user ids, and acquisition source. Then run the
   onboarding A/B test; the companion experimentation project is where the causal claim belongs.

---

## Assumptions

- Active day = at least one `user_engagement` event.
- Session = events separated by less than 30 minutes, measured in seconds so a 30.9-minute gap splits.
- Churn label = no activity on days 1–7 after joining.
- Survival churn event = 7+ days of silence before the data ends; otherwise censored.
- Players first seen in the first 7 days of the export are excluded (left-censoring).
- Retention denominators include only players observed long enough (right-censoring).
- Model features come from the joining day only; the label comes from days 1–7.
- The business simulation uses invented values: 10 units per saved player, 0.5 per offer.

## Limitations

- The dataset is obfuscated: 337,374 events (5.9%) carry a placeholder operating system, 5,240 (0.09%) a
  placeholder country, and 207 rows are exact duplicates. Google notes the export's internal consistency
  has limits.
- Device-level ids only, so cross-device players are counted more than once.
- No revenue data; ad rewards and currency spends are proxies, and both proved irrelevant to retention.
- 114 days of one game in 2018; findings do not automatically generalise.
- Milestone and segment comparisons are descriptive, not causal.
- Seven days are diagnosed as probable event loss. Every DAU-derived metric on those dates — DAU, WAU,
  MAU, stickiness and the cohort cells covering them — is understated, and they were replaced with expected
  values before the forecast was fitted.
- The game has two parallel level modes and the `completed_5_levels` event spans both, so it is not used to
  define progression: the funnel's step 4 and the milestone view's top group both use measured quickplay
  completions (`d0_levels_completed >= 5`, 542 players). Non-quickplay levels are out of scope throughout.
- Proportional hazards fails for all three behavioural covariates in the Cox model, so its hazard ratios
  are average effects across the observation window.
- **Cross-validation folds are not byte-stable across runs.** BigQuery returns view rows unordered, so a
  re-export reshuffles `player_features.csv` and the stratified folds land differently. Test-set metrics
  move by about ±0.002 AUC and cross-validated means by about ±0.005; the ranking of the four models,
  the overfitting gaps and every conclusion are unaffected. Adding `ORDER BY` to the export query would
  pin it exactly.

## What I would do next

Run the onboarding experiment: an easier or better-signposted first three levels, randomised at install,
with D1 return as the primary metric and day-0 level completion as the mechanism check. In parallel, fix
the level-event instrumentation so per-level difficulty can be measured directly, which would turn
"players stall somewhere early" into "players stall at level N".
