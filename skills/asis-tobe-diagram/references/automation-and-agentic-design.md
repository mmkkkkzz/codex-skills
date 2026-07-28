# Automation and Agentic Design Checklist

Use this checklist whenever To-be includes API integration, RPA, workflow
automation, generative AI, or an autonomous/agentic step.

## Business boundary

- What business outcome does the automated step own?
- What remains a human judgment, approval, or legal accountability?
- What cases are ineligible for automation?
- Is the step deterministic, probabilistic, or mixed?

## Inputs and system of record

- Are required fields, identifiers, and source systems explicit?
- Which value wins when sources conflict?
- Are input quality checks performed before execution?
- Are schema, master-data, and permission changes detected?

## Execution safety

- Is the operation idempotent or protected against duplicate execution?
- Are timeout, retry, backoff, and circuit-breaker behavior defined?
- Is there a dry-run or approval mode for high-impact actions?
- Are credentials stored outside the model and HTML artifact?
- Are least privilege and segregation of duties preserved?

## Human-in-the-loop and exception operations

- What confidence, rule, amount, or risk condition routes to a human?
- Who owns the exception queue and what is the SLA?
- Can an operator inspect inputs, rationale, and prior attempts?
- Is correction followed by safe resume or full replay?
- Is a manual fallback documented and exercised?

## Observability and audit

- Is a correlation ID retained end-to-end?
- Are technical success and business completion distinguished?
- Are decision inputs, outputs, model/version, approvals, and changes logged?
- Can operators detect silent partial failure?
- Are dashboards and alerts tied to business-impact thresholds?

## AI-specific controls

- Are source grounding and permitted knowledge boundaries defined?
- Are prompt injection, data leakage, and untrusted content handled?
- Is structured output validated before downstream action?
- Are confidence or policy checks calibrated on representative cases?
- Is there a human override, kill switch, and rollback path?
- Are model updates evaluated against a fixed regression set?

## RPA-specific controls

- Is API or file integration genuinely unavailable or uneconomic?
- Are UI selectors resilient and monitored for breakage?
- Are unattended account sessions, MFA, and credential rotation supported?
- Is screen-state validation performed before write actions?
- Can the robot stop without leaving a partially completed transaction?

## Representation in the model

At minimum, represent:

- trigger;
- automated action;
- validation;
- exception route;
- retry or fallback;
- completion confirmation;
- operating owner;
- linked risks and KPIs.

Do not compress all of these into one box labeled “AI化” or “RPA化.”
