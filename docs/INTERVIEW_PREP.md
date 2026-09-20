# Interview Preparation

Questions an interviewer can ask from this repository, grouped by what they are really testing.
Practise answering out loud, without notes. Fill the brackets with your own numbers.

## A. Tell me about the project (60-120 seconds)
Raw GA4 events for a live mobile game, 114 days, ~15K players, ~5.7M events. I modeled them in BigQuery
into staging, player, player-day and session layers, then built KPI, retention, cohort and funnel views.
On top of that: statistical testing of first-day behaviour, survival analysis, a churn model validated on
later cohorts, behavioural segmentation, and anomaly detection with a forecast. It ships as a live
dashboard and a decision memo. The headline finding is [your finding].

## B. Data modeling and SQL
1. **Why build a staging layer at all?** Renaming, typing and flattening once means no later query touches
   nested fields, and a definition lives in exactly one place.
2. **How do you pull a value out of `event_params`?** A scalar subquery over `UNNEST(event_params)` filtered
   to the key you want. For row-level expansion, cross join to the unnested array instead.
3. **How did you rebuild sessions?** `LAG` for the previous event time per player, flag gaps over 30 minutes,
   then a running `SUM` of those flags is the session id. I measure the gap in seconds because
   `TIMESTAMP_DIFF(..., MINUTE)` truncates, so a 30.9-minute gap would otherwise count as 30.
4. **Where did you use window functions?** Session numbering, "first row per player" for cohort attributes,
   share-of-total in the event dictionary, country ranking, and a funnel monotonicity check.
5. **How do you count DAU, WAU and MAU in one pass?** Join each day to its trailing 28 days of player-days,
   then `COUNT(DISTINCT IF(condition, player_id, NULL))` three times with different conditions.
6. **What does "active" mean here, and why does it matter?** At least one `user_engagement` event. Automatic
   events fire without a person playing, so including them would inflate DAU and retention.

## C. Censoring and correctness
7. **What is left-censoring here and what did you do?** Players present on day 1 of the export may have
   installed long before. I exclude anyone whose first engagement is in the first 7 days.
8. **What is right-censoring and what did you do?** Someone who joined 3 days before the data ends cannot
   have a D7 outcome. Retention denominators count only players with enough follow-up, and the modeling
   table requires 7+ days.
9. **What happens if you ignore that?** Recent cohorts look like they never return, so retention falls
   artificially over time and you "discover" a decline that is an artifact of the window.
10. **How do you know your data layer is right?** `sql/18_verification_checks.sql` runs 14 invariants,
    including day-0 cohort retention being exactly 100% and the funnel's first step equalling the modeling
    table size. Every row must say PASS.

## D. Statistics
11. **Why Mann-Whitney instead of a t-test?** The behaviour counts are heavily right-skewed with long tails;
    rank-based tests are robust to that.
12. **You have tiny p-values everywhere. So what?** With thousands of players almost anything is significant,
    so I report rank-biserial effect sizes and Cramér's V. Some features are significant and negligible.
13. **Why Holm correction?** I tested 15 features at once; without correction I would collect false positives.
14. **Why Wilson intervals?** They behave properly for rates near 0 or 100% and small cohorts, unlike the
    textbook normal-approximation interval.
15. **Explain the survival setup.** Duration is days from joining to last seen; the event is 7+ days of
    silence before the data ends. Players active near the end are censored: known to have lasted at least
    that long, unknown after.
16. **What does a hazard ratio of 0.5 mean?** Roughly half the instantaneous churn risk per unit of that
    variable, holding the others constant.
17. **Your Cox model violated proportional hazards. What now?** Report it as an average effect over the
    window, and either bin or stratify the offending variable. Hiding it would be worse than having it.

## E. Machine learning
18. **What exactly is your label and why that one?** No activity on days 1-7 after joining, for new players
    with a full week of follow-up. It is actionable: a team can intervene during that week.
19. **How did you prevent leakage?** Features come only from the joining day (`event_date = cohort_date`),
    the label from days 1-7, and preprocessing sits inside a Pipeline so scalers fit on training folds only.
20. **Why out-of-time validation?** Deployment means predicting the future from the past. A random split
    lets the model learn from cohorts that arrive after the ones it is scored on.
21. **Your boosted model overfit. How did you know and what did you do?** Train ROC-AUC far above test
    ROC-AUC. I tuned depth, learning rate and minimum leaf size by cross-validation, which shrank the gap.
22. **Which metrics did you report and why?** ROC-AUC for ranking, PR-AUC because positives matter,
    log loss and Brier for probability quality, plus calibration and lift for decision-making.
23. **What is the PR-AUC baseline?** The churn rate itself. Any model below that is worse than guessing.
24. **How did you choose the threshold?** Maximised F1 on out-of-fold training predictions, then applied it
    once to the test set. Choosing it on test data is tuning on the test set.
25. **Is the model good enough to ship?** Depends on the intervention. The riskiest decile carries [X]x the
    average churn rate, and the simulation says targeting pays off only above roughly a [X]% save rate.
26. **Why permutation importance rather than built-in importances?** It is model-agnostic and measures what
    the model actually relies on. Correlated features share credit, which I flagged from the correlation step.

## F. Segmentation and time series
27. **How did you pick the number of segments?** Elbow and silhouette together, restricted to 3-6 because a
    team cannot act on more, then a stability check: refits with five seeds gave ARI [X].
28. **Why not cluster on retention?** Clustering on the outcome and then reporting that the clusters differ
    on the outcome is circular. Behaviour only.
29. **How do you tell a tracking bug from a real drop?** Compare DAU to the STL trend plus weekly pattern,
    then check per-player ratios. DAU collapsing while sessions and minutes per player stay normal points to
    missing events, not missing engagement.
30. **Why replace anomalies before forecasting?** A model fitted through an outage keeps predicting dips
    that never happened.
31. **Did you beat the naive baseline?** Backtested the last 14 days against "same weekday last week":
    [your MAPE numbers]. If the model had lost, the honest recommendation is the baseline.

## G. Judgement and communication
32. **Players who completed 5 levels retained far better. Should we push level completions?** Not from this
    evidence; motivated players do both. It is a hypothesis for an A/B test.
33. **What are the biggest limitations?** Obfuscated data with placeholders, device-level ids, no revenue,
    one game over 114 days in 2018, and everything outside an experiment is associational.
34. **What would you do with a studio's real data?** Real account ids, revenue and acquisition source,
    retention past 30 days, per-level difficulty instrumentation, and experiments on the onboarding step
    the funnel points to.
35. **How did you use AI tools?** [Your README sentence, plus the verification habits you actually used.]
