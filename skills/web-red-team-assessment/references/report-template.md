# Security Assessment Report Template

Use this structure for a durable report. Keep sensitive values redacted.

## Summary

- Target:
- Dates:
- Assessment mode: local-only black-box destructive assessment
- Authorization and scope:
- Local credential source summary, redacted:
- Disposable services/data and reset path:
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
  - Screenshot/HTTP transcript:
  - External evidence reference:
- Likely root cause from observed behavior:
- Remediation recommendation:
- Regression test recommendation:
- Validation:
- Cleanup/reset performed:
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

## Recommendations

- Priority order:
- Suggested owner:
- Suggested verification after remediation:
- Notes:

## Appendix

- Scope details:
- Test accounts and roles, redacted:
- Credential inventory path:
- Tool versions:
- Scanner outputs or artifact paths:
- Cleanup/reset commands:
