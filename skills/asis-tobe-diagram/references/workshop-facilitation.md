# Workshop Facilitation Guide

## Purpose

Use the diagram as a structured decision instrument, not as a presentation made
after decisions have already been assumed.

## Before the session

- Inventory the source material and mark conflicts.
- Prepare a provisional model with assumptions visibly labeled.
- Send no more than eight consolidated questions, prioritizing blockers.
- Identify required decision-makers: process owner, operational SME, control or
  compliance owner, system owner, and delivery owner.
- State the decision boundary for the session: understand As-is, agree design
  principles, approve To-be, or approve implementation scope.

## Suggested 60-minute agenda

| Time | Activity | Output |
|---:|---|---|
| 0–5 | Confirm purpose, scope, and decision rights | Agreed boundary |
| 5–20 | Walk As-is using real cases and exceptions | Corrected process and pain points |
| 20–30 | Confirm evidence, frequency, and materiality | Prioritized pain points and baseline gaps |
| 30–45 | Test To-be changes against constraints and failure modes | Agreed changes, rejected options, risks |
| 45–55 | Confirm KPI, owners, and transition dependencies | Measurement and phased plan |
| 55–60 | Read back decisions and assign open questions | Decision log and owners |

## Facilitation prompts

- “What actually happens for the last difficult case, not only the standard
  procedure?”
- “Who owns the case while it waits here?”
- “Which system is authoritative when two values disagree?”
- “What must a human still judge, and why?”
- “How do we know the automated step has completed the business outcome rather
  than only returned a technical success?”
- “What is the safe manual fallback?”
- “Which control could be weakened by this change?”
- “What evidence would falsify this pain point or benefit assumption?”

## Decision discipline

Record each important statement as one of:

- **Fact:** supported by a named source.
- **Decision:** accepted by an accountable owner.
- **Assumption:** temporarily adopted and assigned for validation.
- **Option:** not yet selected.
- **Conflict:** sources disagree.
- **Question:** information is missing.

Do not let “sounds reasonable” become an approved To-be requirement.

## After the session

Within the same revision:

1. Update the JSON model and preserve stable IDs.
2. Update `decision-log.md` and `open-questions.md`.
3. Run the validator and regenerate HTML.
4. Produce an ID-based diff from the prior version.
5. Ask stakeholders to approve decisions, not pixel-level layout.
