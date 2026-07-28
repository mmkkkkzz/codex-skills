# Diagram Selection Guide

Do not force every problem into one As-is / To-be swimlane. Select the primary
artifact by the decision that stakeholders need to make, then link secondary
artifacts when necessary.

| Decision need | Primary artifact | Use As-is / To-be as… |
|---|---|---|
| Compare current and future work, ownership, systems, and handoffs | As-is / To-be swimlane | Primary artifact |
| Define formal event, gateway, message, and compensation semantics | BPMN 2.0 | Executive or change summary above the BPMN detail |
| Identify waiting, queueing, touch time, and waste across an end-to-end flow | Value-stream map | Summary of current/future operating changes |
| Understand customer experience across frontstage and backstage work | Service blueprint / customer journey | Internal operating-model companion |
| Explain software containers, components, and boundaries | C4 / architecture diagram | Business-context companion |
| Trace data creation, transformation, system of record, and downstream use | Data lineage / DFD | Business-process overlay or linked detail |
| Define complex business rules or eligibility logic | Decision table / DMN / decision tree | Process entry point and outcomes only |
| Clarify accountability without sequence detail | RACI / responsibility matrix | Supplement to lane ownership |
| Plan rollout, dependency, and organizational change | Roadmap / transition-state diagram | Current and target anchors |

## Escalate to BPMN or another formal notation when

- The diagram will be used to configure or execute a workflow engine.
- Event timing, message correlation, parallel gateways, compensation, or
  transactional behavior must be unambiguous.
- Multiple pools and contractual inter-organization messages are material.
- The client mandates BPMN, Signavio, ARIS, Visio, or another governed notation.

In those cases, generate a maintainable As-is / To-be overview and state that a
formal model is a separate deliverable. Do not represent informal HTML notation
as standards-compliant BPMN.

## Split rather than overload

Use linked diagrams when a single view would exceed the complexity guidance:

1. **L0 — Executive comparison:** outcomes, major actors, major changes, KPIs.
2. **L1 — Business process:** normal flow, responsibilities, systems, controls.
3. **L2 — Detail:** exceptions, integration, decision rules, data lineage, and
   operating procedures.

Keep stable IDs across levels so a change, risk, or question can be traced from
L0 to L2.
