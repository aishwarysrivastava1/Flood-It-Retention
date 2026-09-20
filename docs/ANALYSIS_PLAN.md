# Analysis Plan

Written **before** running the analysis, and committed first, so the definitions could not be chosen to suit the results.
(The same discipline as a pre-analysis plan for an experiment. This project is observational, so the plan fixes
definitions and methods rather than hypotheses to test.)

Date written: [date]
Author: [your name]

## 1. Objective
Understand how well a live mobile game retains new players, what first-day behaviour predicts returning,
and whether at-risk players can be identified early enough to act on.

## 2. Data
Public BigQuery dataset `firebase-public-project.analytics_153293282` (Flood-It!), 114 days of raw
Google Analytics 4 event data, roughly 15,000 players and 5.7 million events. No revenue data.

## 3. Definitions fixed in advance
- **Active day:** at least one `user_engagement` event.
- **Cohort date:** the day of the player's first `user_engagement` event.
- **New player:** cohort date at least 7 days after the export begins (left-censoring guard).
- **Session:** interactive events with no gap over 30 minutes.
- **Retention DN:** active exactly N days after joining, among players with at least N days of follow-up.
- **Churn label:** no activity on days 1-7 after joining.
- **Survival churn event:** 7 or more days of silence before the data ends; otherwise censored.

## 4. Analyses planned
1. Data quality: duplicates, missing ids, placeholder values, unusual days.
2. KPIs: DAU, WAU, 28-day MAU, stickiness, sessions and engagement per active player.
3. Retention: D1/D3/D7/D14/D30 with Wilson confidence intervals; weekly cohort grid; retention curve.
4. First-day funnel and retention by furthest milestone.
5. Player-level tests: Mann-Whitney U with rank-biserial effect sizes, Holm-corrected; chi-square with
   Cramér's V for categorical features; Spearman correlations.
6. Survival analysis: Kaplan-Meier overall and by platform and milestone; log-rank tests; Cox regression.
7. Churn model: logistic regression, random forest and gradient boosting, compared against a dummy baseline.
8. Segmentation: K-means on behavioural features only, with a stability check.
9. Time series: STL decomposition, robust anomaly detection, ETS forecast against a seasonal naive baseline.

## 5. Modeling rules fixed in advance
- **Features:** joining-day behaviour only, plus join hour, day of week, platform and country.
- **Label:** days 1-7 after joining. No feature may describe any day after day 0.
- **Split:** out-of-time. Train on the earlier 75% of cohort dates, test on the later 25%.
- **Model selection:** by mean cross-validated ROC-AUC on the training set only.
- **Threshold:** chosen to maximise F1 on out-of-fold training predictions, then applied once to the test set.
- **Reporting:** ROC-AUC, PR-AUC, log loss, Brier score, the train-test gap, calibration and lift.

## 6. Decision rules
- A model is worth recommending only if it beats the dummy baseline on both ROC-AUC and PR-AUC on the
  later cohorts, **and** the lift table shows targeting is meaningfully better than random.
- Any association between first-day behaviour and returning will be reported as descriptive, not causal,
  and framed as a hypothesis for an experiment.

## 7. Known limitations accepted up front
- Obfuscated data with placeholder values; device-level ids only; no revenue.
- 114 days of one game in 2018.
- Both ends of the window are censored.
- Nothing here can establish causation.
