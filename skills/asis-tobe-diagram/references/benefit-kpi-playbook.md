# Benefit and KPI Playbook

## Principle

A To-be diagram is not complete when it only shows that work becomes “more
automated.” It must state what outcome should improve, how that outcome will be
measured, and which guardrails must not deteriorate.

## KPI design fields

Every material KPI should have:

- **Definition:** what is counted and excluded.
- **Baseline:** observed value and measurement period, or `未計測`.
- **Target:** value, date, and whether it is provisional.
- **Formula / measurement:** reproducible calculation and data source.
- **Owner:** accountable role, not only the reporting analyst.
- **Cadence:** daily, weekly, monthly, release-based, or event-based.
- **Linked changes:** which To-be changes are expected to move it.
- **Guardrail relationship:** what could improve superficially while quality or
  control degrades.

## KPI families

| Family | Examples | Typical source |
|---|---|---|
| Outcome | lead time, response time, completion rate, customer wait | workflow timestamps, CRM |
| Efficiency | touch time, person-minutes per case, throughput, unit cost | work logs, time study |
| Quality | error, rework, rejection, duplicate, missing-field rates | exception logs, QA samples |
| Control | approval deviation, access violation, evidence completeness | audit logs, IAM, GRC |
| Reliability | straight-through success, retry, failure, MTTR | automation / integration telemetry |
| Adoption | target-channel usage, manual bypass, active users | application analytics |
| Experience | satisfaction, effort score, complaint rate | survey, support system |

## Benefits calculation

Do not convert every time saving directly into headcount reduction. Separate:

1. **Capacity released:** cases × touch-time reduction.
2. **Avoided growth:** work absorbed without additional staffing.
3. **Hard saving:** contract, license, or labor cost actually removed.
4. **Risk reduction:** expected loss reduction; state assumptions explicitly.
5. **Revenue / service effect:** increased conversion, faster launch, SLA gain.

Example structure:

```text
Annual capacity released
= annual eligible cases
× adoption rate
× automation success rate
× touch-time reduction per successful case
```

Mark each input as observed, agreed assumption, or sensitivity range. Use a
range when evidence is weak.

## Guardrails

Pair efficiency KPIs with at least one quality, control, or reliability metric.
Examples:

- Lead time ↓ while error rate does not increase.
- Automation rate ↑ while manual bypass and unresolved exceptions remain below
  threshold.
- Approval time ↓ while approval deviations remain zero.
- Human review volume ↓ while false-negative risk stays within an agreed limit.

## Prohibited patterns

- Inventing a baseline or target because the slide looks incomplete.
- Claiming an FTE saving when only capacity release is demonstrated.
- Measuring only automation execution, not end-to-end business completion.
- Using an average that hides severe tail latency or high-risk exceptions.
- Defining a KPI without a data source or accountable owner.
