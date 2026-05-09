# Security Assessment Report Template

Use this structure for a durable report. Keep sensitive values redacted.

## Summary

- Target:
- Dates:
- Assessment mode: black-box / authenticated / code-assisted / remediation
- Authorization and scope:
- Overall result:
- Highest severity:

## Findings

### Finding 1: <Short Title>

- Severity: Critical / High / Medium / Low / Informational
- Status: Confirmed / Fixed / Accepted / Blocked
- Affected asset:
- Actors tested:
- Impact:
- Evidence:
  - Request:
  - Response:
  - Screenshot/log:
  - Code reference:
- Root cause:
- Remediation:
- Regression tests:
- Validation:
- Residual risk:

Repeat for each confirmed finding. Do not include speculative items here.

## Clean Passes

List meaningful checks that were actually exercised and produced no issue.

| Area | Evidence | Notes |
| --- | --- | --- |
|  |  |  |

## Hypotheses and Blocked Checks

List suspicious signals, blocked checks, missing credentials, or areas left untested.

| Area | Reason | Next step |
| --- | --- | --- |
|  |  |  |

## Remediation Summary

Use this section only when fixes were made.

- Code changes:
- Tests added:
- Commands run:
- Docs updated:
- Commit/PR:

## Appendix

- Scope details:
- Test accounts and roles, redacted:
- Tool versions:
- Scanner outputs or artifact paths:
