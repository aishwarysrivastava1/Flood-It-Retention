# Player Retention and Churn: Findings and Recommendations
## Flood-It! mobile game, 2018-06-12 to 2018-10-03

> Template. Write this in your own words once the analysis is done. Interviewers ask
> about the wording here, so do not let an AI tool write it for you.

To: Game and product team
From: [your name]
Date: [date]

## Summary
[3-4 sentences. Lead with the single most actionable finding, not the method.]

## Key findings

### 1. Engagement level and trend
[Average DAU, stickiness, and whether the trend is rising, flat or falling.]

### 2. Retention: where players are lost
[D1/D7/D30 with confidence intervals. Where the curve is steepest.
Median days until churn from the Kaplan-Meier curve.]

### 3. The first day decides a lot
[Funnel: what share start a level, complete one, complete five.
The biggest drop-off step, in percentage points.]

### 4. What predicts coming back
[Top features by effect size (Phase 6) and by permutation importance (Phase 8).
Report effect sizes, not only p-values.]

### 5. At-risk players can be identified on day 1
[Test ROC-AUC and PR-AUC against the baseline. Lift in the riskiest decile.
What share of churners the riskiest 30% captures.]

### 6. Player types
[Your segments, their sizes and their return rates. Say that clustering used
behaviour only, and report the ARI stability score.]

### 7. Unusual days
[Each anomaly, and your diagnosis: tracking issue or real behaviour change,
with the per-player ratio evidence that supports it.]

### 8. Two-week outlook
[ETS forecast with the 95% interval, and whether it beat the seasonal naive
baseline in the backtest. If it did not, say so and recommend the baseline.]

## Recommendations
1. [Onboarding change aimed at the biggest funnel drop. Frame as a hypothesis to test.]
2. [Who to target with a retention intervention, based on the lift table, and the
   break-even save rate from the business simulation.]
3. [Which data-quality or tracking issue to fix first, with the evidence.]
4. [What to instrument or A/B test next to turn descriptive findings into causal ones.]

## Assumptions
- Active day = at least one `user_engagement` event.
- Session = events separated by less than 30 minutes.
- Churn label = no activity on days 1-7 after joining.
- Survival churn event = 7+ days of silence before the data ends.
- Players first seen in the first 7 days of the export are excluded (left-censoring).
- Retention denominators include only players observed long enough (right-censoring).
- The business simulation uses invented values for player value and offer cost.

## Limitations
- The dataset is obfuscated; some fields contain placeholder values, and Google notes
  the dataset's internal consistency has limits.
- Device-level ids only, so cross-device players are counted more than once.
- No revenue data; ad rewards and currency spends are proxies.
- 114 days of one game in 2018; findings do not automatically generalise.
- Milestone and segment comparisons are descriptive, not causal.
- [Any anomaly you diagnosed as a tracking issue, and which metrics it affects.]

## What I would do next
[2-3 sentences: the experiment or instrumentation that would answer the open questions.]
