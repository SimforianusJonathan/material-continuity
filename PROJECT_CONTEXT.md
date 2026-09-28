# Material Continuity — Project Context, Architecture, and Progress Tracker

> **Purpose of this file**
>
> This document is the primary handoff/context file for any local AI coding agent (Codex, Claude Code, Copilot, etc.) working on the **Material Continuity** project.
>
> Read this file **before making architectural changes, generating code, adding dependencies, or changing business logic**.
>
> The project originated from the final-stage proposal for an Agentic AI hackathon under the **Intelligence Manufacturing** track.
>
> This file contains:
> - the project problem and scope;
> - proposal-derived requirements;
> - implementation decisions and recommendations;
> - architecture and component responsibilities;
> - deterministic vs agentic boundaries;
> - data model and tool contracts;
> - UI and demo flow;
> - security / approval boundaries;
> - repo structure;
> - milestone checklist;
> - progress tracker;
> - architecture decision log;
> - test / acceptance criteria;
> - open questions and risks;
> - instructions for future AI agents.
>
> **Important:** Sections marked `[PROPOSAL]` are grounded in the submitted proposal.
> Sections marked `[IMPLEMENTATION]` are implementation recommendations derived from the proposal and may be changed deliberately if there is a better reason.
> Sections marked `[CURRENT DECISION]` represent decisions already made in this project conversation and should not be changed casually.

---

# 0. Project Identity

## Project name

**Material Continuity**

## Repository strategy

`[CURRENT DECISION]`

Use **one GitHub organization + one monorepo** for the hackathon MVP.

Suggested organization name:

```text
material-continuity
```

Suggested repository name:

```text
material-continuity
```

Reason:
- team size is 3;
- MVP scope is tightly coupled;
- frontend, agent orchestration, deterministic tools, mock enterprise data, and AWS infrastructure need frequent integration;
- multi-repo would add unnecessary coordination and CI/CD overhead for the hackathon stage.

---

# 1. Executive Summary

`[PROPOSAL]`

Material Continuity handles a manufacturing recovery problem that appears when a **critical purchased component becomes unavailable, delayed, or quarantined** and no immediately usable approved option can meet the required production date.

The key business insight is:

> **Availability does not imply usability.**

A replacement component can be physically available but still unusable because:
- engineering requirements are not fully satisfied;
- application-specific evidence is missing;
- the available evidence belongs to the wrong revision;
- a required qualification test is incomplete;
- a deviation has expired;
- Quality has not released the component;
- qualification may complete only after the production shortage occurs.

The system therefore does not merely answer:

> “Can we obtain another component?”

It must answer:

> **“Can an alternative become qualified and usable before the remaining recovery window closes, and what evidence and approvals are still required?”**

The project focuses on a pilot scenario involving **purchased bearings used directly in assembly BOMs**, not maintenance spares.

---

# 2. Precise Problem Statement

`[PROPOSAL]`

When a critical component is delayed or quarantined:

1. Planning must determine which production orders are exposed.
2. Procurement checks available supply, supplier ETA, and quotes.
3. Engineering checks application requirements, drawings, limits, and revisions.
4. Quality checks qualification status, tests, supplier approval, and deviations.
5. Production evaluates whether resequencing can protect output.

A purchase decision made before those answers agree can convert a **material shortage** into a **quality incident**.

The pilot therefore aims to:

> **Compress the time required to establish an approvable, time-feasible recovery plan when immediately usable approved options are exhausted, while preserving Engineering and Quality release authority.**

---

# 3. Core Product Thesis

`[PROPOSAL]`

Material Continuity is **not**:
- a generic RAG chatbot;
- a procurement agent;
- a supplier search engine;
- a predictive maintenance product;
- a generic manufacturing assistant;
- a free-form LLM recommendation system;
- an autonomous release system.

It is a:

> **Versioned, evidence-bound recovery decision workflow for material disruption.**

The central output is a **recovery case** linking:

```text
production exposure
→ recovery options
→ technical requirements
→ evidence per requirement
→ unresolved gaps
→ qualification dependencies
→ recovery timing
→ human approvals
→ authorized action
```

---

# 4. Non-Negotiable Design Principles

These principles should remain stable unless the team explicitly changes the proposal strategy.

## 4.1 Arrival is not readiness

`[PROPOSAL]`

A candidate arriving before depletion is not necessarily usable before depletion.

Example:

```text
Usable stock:            300 bearings
Demand:                  100/day
Stock depletion:         after Day 3
Candidate ETA:           Day 2
Qualification complete:  Day 5
```

Therefore:

```text
arrives before shortage = YES
usable before shortage  = NO
```

---

## 4.2 Missing evidence must remain visible

`[PROPOSAL]`

If an application-specific requirement is not supported by evidence:

```text
Status = UNKNOWN
```

Do **not** silently infer compatibility.

Allowed requirement states:

```text
MATCH
MISMATCH
UNKNOWN
BLOCKED
```

Suggested semantics:

- `MATCH`: sufficient applicable evidence supports the requirement.
- `MISMATCH`: evidence explicitly violates the requirement.
- `UNKNOWN`: required evidence is missing, insufficient, conflicting, or not applicable enough.
- `BLOCKED`: release/qualification state prevents use even if technical attributes appear compatible.

---

## 4.3 Hard mismatches reject

`[PROPOSAL]`

If a hard requirement is violated, the candidate must not progress as a valid replacement.

Example:

```text
Required bore = 25 mm
Candidate bore = 30 mm
Result = MISMATCH
Decision = REJECT
```

---

## 4.4 Unknown is not match

`[PROPOSAL]`

A missing document, missing test, expired deviation, or unresolved conflicting evidence must not be converted into a confident positive conclusion.

---

## 4.5 LLM interprets and orchestrates; code calculates and enforces; humans authorize

`[CURRENT DECISION]`

This sentence is the implementation boundary for the entire MVP:

> **LLM interprets and orchestrates. Code calculates and enforces. Human authorizes.**

### LLM / agent responsibilities

- tool selection;
- understanding the recovery objective;
- interpreting heterogeneous documents;
- extracting structured evidence;
- evidence synthesis;
- identifying missing evidence;
- determining which investigation/tool to perform next;
- explaining recovery scenarios.

### Deterministic code responsibilities

- stock arithmetic;
- time-phased shortage calculation;
- dimensional/unit comparisons;
- hard constraints;
- qualification timing;
- dependency graph calculations;
- scenario cost/timing calculations;
- action authorization checks;
- case-version validation;
- idempotency enforcement.

### Human responsibilities

- Engineering review;
- Quality review;
- approving qualification tasks;
- approving controlled actions where required;
- final material release authority.

---

# 5. MVP Scope

`[PROPOSAL]`

The submitted MVP scope is intentionally narrow.

## Data scope

- one bearing family;
- three candidate records;
- two assembly BOMs;
- ten production orders;
- twelve text-based technical/quality documents;
- stock fixtures;
- supplier fixtures;
- test-calendar fixtures;
- one plant;
- transfer lookup;
- synthetic enterprise data;
- mock test results.

## Technical scope

- Recovery Supervisor;
- Evidence Specialist;
- Amazon Bedrock inference;
- AgentCore Runtime;
- AgentCore Gateway;
- Amazon S3;
- Bedrock Managed Knowledge Base;
- EventBridge;
- Lambda;
- controlled tools;
- review UI;
- versioned recovery case;
- approval gate;
- mock enterprise action receipt.

## Explicitly post-MVP / not required

`[PROPOSAL]`

- live SAP write-back;
- unrestricted procurement;
- real supplier onboarding;
- complex technical drawing interpretation;
- physical qualification execution;
- deployed factory benefit;
- automatic BOM release.

---

# 6. Canonical Demo Scenario

`[PROPOSAL]`

The final demo should be built around **one coherent end-to-end failure-and-recovery story**, not a collection of unrelated features.

## Demo sequence

1. Inject a delayed delivery.
2. Identify the affected/exposed production orders.
3. Confirm no timely approved source can meet the need date.
4. Discover unqualified candidate alternatives.
5. Reject one candidate due to a hard mismatch.
6. Flag another candidate because application-specific temperature/lubricant evidence is missing.
7. Compare three recovery paths.
8. A human reviewer approves a qualification task.
9. The action adapter creates a mock QMS task/identifier.
10. Production release remains blocked.
11. Update the source document revision.
12. Re-open the case.
13. Invalidate the previous authorization because it belongs to an older case/evidence version.

## This scenario is the primary definition of done.

If a feature does not materially improve this story, it is lower priority during the hackathon.

---

# 7. Recovery Workflow

`[PROPOSAL]`

The recovery process has five major stages.

## 7.1 Sense / Assess

Input:

```text
ERP/QMS disruption event
```

Examples:
- delivery delay;
- quality hold;
- stock exception;
- component quarantine.

Actions:
- deduplicate event;
- retrieve current stock;
- retrieve holds;
- retrieve confirmed receipts;
- retrieve dated demand / production orders;
- compute time-phased shortage.

Important:

> The shortage date must be calculated by deterministic code, not estimated by the LLM.

---

## 7.2 Discover

Search in the following order:

```text
1. network stock
2. approved source
3. approved equivalent
4. alternate BOM
5. still-valid deviation
6. unqualified candidates
7. original-part expedite
8. production resequencing
```

Do not jump directly to unqualified substitutes if an already-approved recovery path is sufficient.

---

## 7.3 Verify

For each candidate:

- retrieve revision-specific evidence;
- retrieve application requirements;
- normalize units;
- compare evidence to explicit limits;
- record source / revision / page / applicability;
- classify each requirement;
- identify missing/conflicting evidence;
- identify required qualification tests.

Rules:

```text
hard MISMATCH → reject candidate
critical UNKNOWN → block release / require evidence or test
missing evidence → never auto-MATCH
```

---

## 7.4 Simulate

Build a qualification dependency graph.

Example:

```text
supplier confirmation
        ↓
candidate delivery
        ↓
temperature test
        ↓
engineering review
        ↓
quality review
        ↓
qualification release
```

Use:
- test durations;
- resource calendars;
- delivery dates;
- approval dependencies;
- current production shortage date.

Compare at least:

```text
A. substitute + qualification
B. original-part expedite
C. production resequencing
```

Rank or present feasible recovery scenarios using deterministic outputs such as:
- exposed orders;
- recovery date;
- incremental cost;
- qualification completion date;
- feasibility;
- unresolved conditions.

Unknown completion times must remain unresolved.

---

## 7.5 Approve / Act / Learn

Agent-generated recommendations are not authorization.

Before executing an action:

- verify approver identity;
- verify approver role;
- verify allowed action;
- verify case version;
- verify case hash;
- verify approval expiry;
- re-read changing stock/evidence where relevant;
- enforce idempotency;
- log an action receipt.

A qualification task approval does **not** release the material for production.

---

# 8. High-Level Architecture

`[PROPOSAL + IMPLEMENTATION]`

```text
                    ┌───────────────────────┐
                    │  Disruption Event     │
                    │ ERP / QMS / Fixture   │
                    └───────────┬───────────┘
                                │
                           EventBridge
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Recovery Supervisor   │
                    │ Agent / Orchestrator  │
                    └───────────┬───────────┘
                                │
       ┌────────────────────────┼─────────────────────────┐
       │                        │                         │
       ▼                        ▼                         ▼
┌───────────────┐       ┌────────────────┐       ┌─────────────────┐
│ Exposure Tool │       │ Recovery       │       │ Evidence        │
│ Deterministic │       │ Options Tool   │       │ Specialist      │
└───────────────┘       └────────────────┘       └────────┬────────┘
                                                        │
                                                        ▼
                                            S3 + Bedrock Knowledge Base
                                                        │
       ┌────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Versioned Recovery Case │
│ Evidence + gaps + state │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Qualification Graph     │
│ Deterministic timing    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Recovery Simulation     │
│ Deterministic scenarios │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Human Approval Gate     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Action Adapter          │
│ role/version/idempotency│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Mock ERP / QMS Action   │
│ + Action Receipt        │
└─────────────────────────┘
```

---

# 9. Agent Architecture

## 9.1 Recovery Supervisor

`[PROPOSAL]`

Primary role:
- orchestrate the recovery case;
- choose the next tool;
- branch based on results;
- maintain case context;
- coordinate evidence investigation;
- request simulations;
- present recovery scenarios.

The supervisor should **not** perform deterministic business calculations itself.

Expected tools:

```text
getExposure()
findRecoveryOptions()
compareRequirements()
simulateRecovery()
createQualificationTask()
```

Possible additional implementation tools:

```text
getCase()
updateCase()
getCandidateEvidence()
getQualificationDependencies()
validateApproval()
executeAuthorizedAction()
```

---

## 9.2 Evidence Specialist

`[PROPOSAL]`

Responsibilities:
- retrieve technical/quality evidence;
- identify correct document revision;
- extract candidate specifications;
- map evidence to specific application requirements;
- normalize units;
- identify evidence gaps;
- identify qualification dependencies;
- preserve provenance.

Expected output should be structured.

Example:

```json
{
  "candidate_id": "CAND-A",
  "requirement_id": "REQ-LOAD-001",
  "requirement": "Dynamic load",
  "required_operator": ">=",
  "required_value": 14,
  "required_unit": "kN",
  "observed_value": 16,
  "observed_unit": "kN",
  "status": "MATCH",
  "evidence": {
    "document": "Candidate_A_Datasheet_Rev2.pdf",
    "revision": "2",
    "page": 3,
    "location": "Dynamic load rating table"
  }
}
```

---

# 10. Deterministic Core

`[IMPLEMENTATION]`

Build this before depending heavily on agents.

The MVP should function with mocked/structured inputs before document retrieval and agent orchestration are added.

## 10.1 `getExposure()`

Purpose:
- determine when usable stock is depleted;
- identify exposed production orders.

Inputs:

```json
{
  "material_id": "BRG-001",
  "as_of": "ISO-8601 timestamp"
}
```

Expected calculations:

```text
available stock
+ confirmed receipts by date
- allocations
- time-phased BOM consumption
= projected availability
```

Outputs:

```json
{
  "material_id": "BRG-001",
  "current_usable_stock": 300,
  "shortage_date": "2026-10-04",
  "affected_orders": [
    {
      "order_id": "PO-006",
      "due_date": "2026-10-04",
      "unserved_qty": 100
    }
  ]
}
```

---

## 10.2 `findRecoveryOptions()`

Purpose:
search for recovery paths in the required order.

Possible output:

```json
{
  "approved_options": [],
  "unqualified_candidates": [
    "CAND-A",
    "CAND-B"
  ],
  "fallbacks": [
    "EXPEDITE_ORIGINAL",
    "RESEQUENCE_PRODUCTION"
  ]
}
```

---

## 10.3 `compareRequirements()`

Purpose:
perform deterministic comparison after evidence extraction.

Input:

```json
{
  "requirement": {
    "name": "Bore",
    "operator": "=",
    "value": 25,
    "unit": "mm",
    "critical": true
  },
  "candidate_evidence": {
    "value": 25,
    "unit": "mm",
    "source": "Candidate_A_Datasheet_Rev2.pdf",
    "revision": "2",
    "page": 2
  }
}
```

Output:

```json
{
  "status": "MATCH",
  "normalized_required_value": 25,
  "normalized_observed_value": 25,
  "unit": "mm"
}
```

Hard rule:
- comparison result must be reproducible;
- LLM text must not determine numerical compatibility.

---

## 10.4 `simulateRecovery()`

Purpose:
compute when a recovery option becomes usable and compare it with the shortage window.

Input example:

```json
{
  "candidate_id": "CAND-A",
  "arrival_date": "2026-10-03",
  "shortage_date": "2026-10-04",
  "dependencies": [
    {
      "task": "temperature_test",
      "duration_hours": 16
    },
    {
      "task": "engineering_review",
      "duration_hours": 4
    },
    {
      "task": "quality_release",
      "duration_hours": 4
    }
  ]
}
```

Output:

```json
{
  "arrival_date": "2026-10-03",
  "qualification_complete": "2026-10-05",
  "shortage_date": "2026-10-04",
  "feasible_before_shortage": false,
  "delay_after_shortage_hours": 24
}
```

---

# 11. Recovery Case Model

`[PROPOSAL + IMPLEMENTATION]`

The recovery case is a first-class object.

Suggested structure:

```json
{
  "case_id": "CASE-001",
  "case_version": 3,
  "status": "UNDER_REVIEW",
  "trigger": {
    "type": "DELIVERY_DELAY",
    "material_id": "BRG-001"
  },
  "exposure": {},
  "recovery_options": [],
  "candidates": [],
  "evidence_matrix": [],
  "qualification_dependencies": [],
  "scenarios": [],
  "approvals": [],
  "actions": [],
  "source_versions": [],
  "created_at": "",
  "updated_at": ""
}
```

## Case-version rules

A case version should change when information that can materially change the decision changes, for example:

- source document revision changes;
- supplier ETA changes;
- stock quantity changes significantly;
- test result changes;
- qualification requirement changes;
- production order timing changes;
- candidate evidence changes.

An approval is valid only for the case/evidence version it reviewed.

---

# 12. Evidence Model

`[PROPOSAL]`

Every supported requirement row should retain:

```text
requirement
candidate value
normalized value
source document
document revision
page/location
applicability
status
```

Example matrix:

| Requirement | Candidate | Evidence | Status |
|---|---:|---|---|
| Bore = 25 mm | 25 mm | Datasheet Rev2 p.2 | MATCH |
| Dynamic load ≥ 14 kN | 16 kN | Datasheet Rev2 p.3 | MATCH |
| Lubricant suitability at operating temperature | Not evidenced | No application-specific evidence | UNKNOWN |
| Plant qualification release | Not released | QMS fixture | BLOCKED |

---

# 13. Synthetic Data Model

`[IMPLEMENTATION]`

The following tables/entities are recommended for the MVP.

## 13.1 Materials

```text
material_id
description
material_family
approved_status
current_stock
unit
```

## 13.2 BOM

```text
product_id
material_id
quantity_required
bom_revision
valid_from
valid_to
```

## 13.3 Production Orders

```text
order_id
product_id
quantity
scheduled_date
due_date
priority
status
```

## 13.4 Purchase Orders / Receipts

```text
po_id
material_id
supplier_id
quantity
expected_delivery
status
```

## 13.5 Suppliers / Candidate Availability

```text
supplier_id
candidate_id
available_qty
eta
quoted_price
quote_timestamp
```

## 13.6 Engineering Requirements

```text
requirement_id
product_id
application_id
property
operator
required_value
unit
criticality
source_document
source_revision
```

## 13.7 Candidate Specifications

```text
candidate_id
property
value
unit
source_document
source_revision
source_page
```

## 13.8 Qualification Tests

```text
test_id
candidate_id
requirement_id
procedure_id
duration_hours
required_resource
status
result
```

## 13.9 Deviations

```text
deviation_id
candidate_id
scope
valid_from
valid_until
approval_status
```

## 13.10 Approvals

```text
approval_id
case_id
case_version
case_hash
approver_id
approver_role
permitted_action
approved_at
expires_at
```

## 13.11 Action Receipts

```text
action_id
case_id
case_version
action_type
external_reference
idempotency_key
status
executed_at
```

---

# 14. Document / Retrieval Layer

`[PROPOSAL + IMPLEMENTATION]`

Target architecture:

```text
Engineering / Quality Documents
            ↓
           S3
            ↓
Bedrock Managed Knowledge Base
            ↓
Evidence Specialist
            ↓
Structured evidence
            ↓
Deterministic requirement comparison
```

Recommended synthetic document set:

```text
Candidate_A_Datasheet_Rev2.pdf
Candidate_A_Certificate.pdf
Candidate_B_Datasheet.pdf
Candidate_C_Datasheet.pdf

Engineering_Drawing_Assembly_A.pdf
Engineering_Drawing_Assembly_B.pdf
Bearing_Application_Requirements.pdf

Qualification_SOP_Temperature.pdf
Qualification_SOP_Load.pdf

Approved_Supplier_List.pdf
Existing_Deviation.pdf
Quality_Release_Procedure.pdf
```

The exact filenames may change.

The retrieval layer must preserve:
- document identity;
- revision;
- page/location;
- applicability;
- extraction confidence if implemented;
- source version.

---

# 15. Qualification Dependency Graph

`[PROPOSAL + IMPLEMENTATION]`

Candidate readiness must follow the critical path of remaining work.

Example:

```text
Candidate selected
      │
      ▼
Supplier delivery
      │
      ▼
Temperature test
      │
      ▼
Engineering review
      │
      ▼
Quality review
      │
      ▼
Qualification release
      │
      ▼
Usable for production
```

Do not equate:
- supplier ETA;
- test completion;
- approval;
- production release.

These are distinct lifecycle states.

---

# 16. Recovery Scenarios

`[PROPOSAL]`

At minimum compare:

## Scenario A — Substitute + Qualification

Variables:
- candidate ETA;
- missing evidence;
- qualification test duration;
- Engineering review;
- Quality review;
- incremental cost;
- qualification completion date.

## Scenario B — Original-Part Expedite

Variables:
- expedited ETA;
- expedite cost;
- quantity;
- production coverage.

## Scenario C — Production Resequencing

Variables:
- alternative order sequence;
- available material;
- protected orders;
- deferred orders;
- changeover / operational impact if modeled.

Output example:

| Recovery Option | Ready Date | Exposed Orders | Incremental Cost | Decision State |
|---|---|---:|---:|---|
| Candidate A + Qualification | Day 5 | 2 | 3,000 | CONDITIONAL |
| Original Expedite | Day 4 | 1 | 7,500 | FEASIBLE |
| Production Resequencing | Day 3 | 0 initially | 2,000 | TEMPORARY BRIDGE |

The numbers above are illustrative only.

---

# 17. Human Approval and Action Gate

`[PROPOSAL]`

The agent must not possess:
- unrestricted purchasing authority;
- BOM release authority;
- automatic production release authority.

Before an action executes, validate:

```text
authenticated user
approver role
permitted action
case ID
case version
case hash
approval expiry
source freshness
idempotency key
```

### Failure behavior

Fail closed if:
- approval is stale;
- source revision changed;
- case version changed;
- role is unauthorized;
- approval expired;
- action is outside permitted scope;
- duplicate action already executed.

---

# 18. Stale Approval Demo

`[CURRENT DECISION]`

This should be intentionally demonstrated because it clearly differentiates the project.

Example:

```text
Case Version 3
Candidate A
Datasheet Revision 2

Quality approves:
CREATE_QUALIFICATION_TASK
```

Then replace:

```text
Candidate_A_Datasheet_Rev2.pdf
```

with:

```text
Candidate_A_Datasheet_Rev3.pdf
```

System behavior:

```text
new evidence version detected
case version: 3 → 4
previous authorization: INVALID
```

If execution is attempted:

```text
ACTION BLOCKED

Authorization belongs to Case Version 3.
Current Case Version is 4.
Re-review required.
```

---

# 19. Action Adapter

`[PROPOSAL + IMPLEMENTATION]`

The MVP does not require a live SAP write-back.

The action adapter may mock an enterprise QMS/ERP write.

Primary MVP action:

```text
createQualificationTask()
```

Example result:

```json
{
  "status": "CREATED",
  "qms_task_id": "QMS-QUAL-00421",
  "case_id": "CASE-001",
  "case_version": 3,
  "timestamp": "2026-10-XXTXX:XX:XXZ",
  "idempotency_key": "..."
}
```

Important:

```text
Qualification task created ≠ material released
```

Production release must remain blocked until the appropriate lifecycle criteria are satisfied.

---

# 20. AWS Service Mapping

`[PROPOSAL]`

Target services:

## Amazon Bedrock

Use for:
- document interpretation;
- adaptive reasoning;
- evidence synthesis;
- tool selection.

## Amazon Bedrock AgentCore Runtime

Use for:
- hosting agent runtime;
- Recovery Supervisor;
- Evidence Specialist.

## AgentCore Gateway

Use for:
- controlled tool exposure;
- API/Lambda targets;
- constrained agent access.

## Amazon S3

Use for:
- technical documents;
- quality documents;
- source versions;
- potentially audit artifacts.

## Bedrock Managed Knowledge Base

Use for:
- document parsing;
- retrieval;
- evidence grounding.

## AWS Lambda

Use for:
- deterministic arithmetic;
- requirement checks;
- exposure calculation;
- recovery simulation;
- approval-policy enforcement;
- action adapter.

## EventBridge

Use for:
- disruption event trigger;
- event-driven invocation.

## CloudWatch / AgentCore Observability

Use for:
- tool-call traces;
- logs;
- errors;
- agent execution visibility;
- audit support.

## IAM

Use least privilege.

Do not rely on retrieved documents as authorization.

---

# 21. AWS Validation Checklist

`[IMPLEMENTATION]`

Perform early before committing architecture details:

- [ ] Confirm AWS account access from hackathon.
- [ ] Confirm target AWS Region.
- [ ] Confirm Bedrock model availability.
- [ ] Confirm AgentCore Runtime availability.
- [ ] Confirm AgentCore Gateway availability.
- [ ] Confirm Knowledge Base availability.
- [ ] Confirm S3 permissions.
- [ ] Confirm Lambda deployment access.
- [ ] Confirm EventBridge access.
- [ ] Confirm CloudWatch access.
- [ ] Identify quota limitations.
- [ ] Identify allowed model(s).
- [ ] Record all required environment variables.

If AgentCore access is unavailable, preserve the logical architecture and use a compatible fallback runtime rather than rewriting the product concept.

---

# 22. UI / UX Scope

`[IMPLEMENTATION]`

Keep the frontend compact.

Recommended five primary views:

## View 1 — Disruption / Exposure

Show:

```text
critical material
current usable stock
daily/projected consumption
original ETA
depletion date
affected orders
```

Example:

```text
CRITICAL MATERIAL EXCEPTION

BRG-001

Available Stock       300
Consumption / Day     100
Original ETA          Day 21

Projected Depletion   Day 3
Orders Exposed        4
```

---

## View 2 — Recovery Discovery

Show the search hierarchy and results:

```text
Network stock        none
Approved source      none
Approved equivalent  none
Alternate BOM        none
Valid deviation      none

Unqualified candidates:
Candidate A
Candidate B
Candidate C
```

This view demonstrates that the system does not jump prematurely to unqualified alternatives.

---

## View 3 — Evidence Matrix

This is likely the most important technical review view.

Example:

| Requirement | Candidate Value | Evidence | Status |
|---|---:|---|---|
| Bore = 25 mm | 25 mm | Datasheet Rev2 p.2 | MATCH |
| Dynamic load ≥ 14 kN | 16 kN | Datasheet Rev2 p.3 | MATCH |
| Lubricant at operating temperature | — | No applicable evidence | UNKNOWN |
| Plant qualification release | Not released | QMS | BLOCKED |

---

## View 4 — Recovery Timeline / Qualification Graph

Show candidate arrival vs actual readiness.

Example concept:

```text
DAY             1    2    3    4    5
Stock           ███████████
                         ↑
                     depletion

Candidate ETA        ●

Qualification             █████

Engineering                    ●
Quality                        ●

Usable                            ●
```

Primary message:

```text
Candidate arrives before shortage,
but qualification completes after depletion.
```

---

## View 5 — Approval / Action

Show:
- selected recovery scenario;
- unresolved conditions;
- required role;
- approval button;
- action receipt;
- production release status.

Example:

```text
Selected Recovery:
Original Expedite + Temporary Resequencing

Candidate A:
Qualification path not ready before depletion

[Approve Qualification Task]
[Request Revision]

Production Release: BLOCKED
```

---

# 23. Suggested Monorepo Structure

`[CURRENT DECISION]`

```text
material-continuity/
│
├─ apps/
│  └─ web/
│     ├─ src/
│     ├─ public/
│     └─ tests/
│
├─ services/
│  ├─ recovery-supervisor/
│  ├─ evidence-specialist/
│  └─ action-adapter/
│
├─ core/
│  ├─ exposure/
│  ├─ recovery-options/
│  ├─ requirements/
│  ├─ qualification/
│  ├─ simulation/
│  ├─ approval/
│  └─ case-state/
│
├─ data/
│  ├─ fixtures/
│  │  ├─ materials/
│  │  ├─ bom/
│  │  ├─ production-orders/
│  │  ├─ purchase-orders/
│  │  ├─ suppliers/
│  │  └─ qualification/
│  │
│  └─ documents/
│
├─ infrastructure/
│  └─ aws/
│
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ acceptance/
│
├─ docs/
│  ├─ architecture/
│  ├─ decisions/
│  └─ demo/
│
├─ scripts/
├─ .env.example
├─ README.md
├─ PROJECT_CONTEXT.md
└─ LICENSE
```

This file should be saved as:

```text
PROJECT_CONTEXT.md
```

at repository root.

---

# 24. Team Workstream Split

`[IMPLEMENTATION]`

For a 3-person team, divide by functional dependency rather than rigid frontend/backend/AI silos.

## Person 1 — Decision Engine

Own:
- synthetic ERP/QMS data;
- `getExposure`;
- `findRecoveryOptions`;
- qualification timing;
- recovery simulation;
- scenario ranking.

## Person 2 — Agent + Evidence

Own:
- S3;
- Knowledge Base;
- Bedrock;
- Evidence Specialist;
- Recovery Supervisor;
- tool-calling integration;
- provenance output.

## Person 3 — Case + Approval + UI

Own:
- recovery-case state;
- case versioning;
- approval model;
- action adapter;
- frontend;
- audit/event timeline.

### Integration rule

Do not wait until all three workstreams are "finished."

Integrate continuously around the canonical demo scenario.

---

# 25. Recommended Build Order

`[CURRENT DECISION]`

Do **not** start by building the agent.

Recommended sequence:

## Phase 0 — Environment / Architecture Validation

- [ ] Create GitHub organization.
- [x] Create monorepo.
- [x] Add `PROJECT_CONTEXT.md`.
- [x] Add `.gitignore`.
- [x] Add `.env.example`.
- [ ] Confirm AWS account.
- [ ] Confirm AWS Region.
- [ ] Verify service availability.
- [ ] Choose backend/frontend stack.
- [x] Define local run command.

## Phase 1 — Canonical Scenario + Synthetic Data

- [x] Lock one delayed-bearing exposure scenario.
- [x] Define original bearing.
- [x] Define current stock.
- [x] Define production demand.
- [x] Define delayed original receipt.
- [x] Define Candidate A.
- [x] Define Candidate B hard mismatch.
- [x] Define Candidate C / optional third path.
- [x] Define 2 BOMs.
- [x] Define 10 production orders.
- [x] Define supplier availability.
- [ ] Define qualification test calendar.
- [ ] Define 12 documents.

## Phase 2 — Deterministic Core

- [x] Implement `getExposure`.
- [x] Unit-test stock depletion.
- [x] Implement `findRecoveryOptions`.
- [x] Implement requirement normalization.
- [x] Implement `compareRequirements`.
- [x] Unit-test MATCH.
- [x] Unit-test MISMATCH.
- [x] Unit-test UNKNOWN.
- [ ] Implement qualification dependency graph.
- [ ] Implement `simulateRecovery`.
- [ ] Compare three recovery scenarios.

## Phase 3 — Recovery Case

- [ ] Define recovery-case schema.
- [ ] Implement case creation.
- [ ] Implement case updates.
- [ ] Implement version increment.
- [ ] Store source versions.
- [ ] Store evidence matrix.
- [ ] Store simulation results.
- [ ] Store approvals.
- [ ] Store action receipts.

## Phase 4 — Evidence Pipeline

- [ ] Upload synthetic docs to S3.
- [ ] Create Knowledge Base.
- [ ] Validate retrieval.
- [ ] Extract structured evidence.
- [ ] Preserve revision/page/source.
- [ ] Connect evidence output to deterministic comparison.
- [ ] Ensure unsupported evidence remains UNKNOWN.

## Phase 5 — Evidence Specialist

- [ ] Define system prompt / role.
- [ ] Define structured output schema.
- [ ] Add retrieval tool.
- [ ] Add requirement-mapping workflow.
- [ ] Add evidence-gap detection.
- [ ] Add qualification-procedure retrieval.
- [ ] Test with Candidate A.
- [ ] Test with Candidate B.

## Phase 6 — Recovery Supervisor

- [ ] Define supervisor role.
- [ ] Expose controlled tools.
- [ ] Implement recovery branching.
- [ ] Maintain case state.
- [ ] Call Evidence Specialist only when needed.
- [ ] Call deterministic tools for all calculations.
- [ ] Produce recovery summary.

## Phase 7 — Approval Gate

- [ ] Define roles.
- [ ] Define allowed actions by role.
- [ ] Implement case hash.
- [ ] Implement approval expiry.
- [ ] Implement stale-case detection.
- [ ] Implement source-freshness check.
- [ ] Implement idempotency.

## Phase 8 — Action Adapter

- [ ] Implement `createQualificationTask`.
- [ ] Generate mock QMS identifier.
- [ ] Record action receipt.
- [ ] Prevent duplicate action.
- [ ] Keep production release blocked.

## Phase 9 — UI

- [ ] Disruption view.
- [ ] Recovery options view.
- [ ] Evidence matrix.
- [ ] Qualification/recovery timeline.
- [ ] Approval/action view.
- [ ] Agent/tool timeline.
- [ ] Stale approval visualization.

## Phase 10 — Event / Observability

- [ ] EventBridge trigger.
- [ ] Event deduplication.
- [ ] CloudWatch logging.
- [ ] Agent/tool traces.
- [ ] Error-state logging.

## Phase 11 — Acceptance Demo

- [ ] Run canonical scenario end-to-end.
- [ ] Hard mismatch candidate rejected.
- [ ] Missing evidence remains UNKNOWN.
- [ ] Qualification timing extends past shortage.
- [ ] Recovery scenarios compared.
- [ ] Human approves qualification task.
- [ ] QMS task receipt generated.
- [ ] Production release remains blocked.
- [ ] Evidence revision changes.
- [ ] Case version increments.
- [ ] Previous approval becomes invalid.
- [ ] Duplicate action is blocked.

---

# 26. Current Progress Tracker

Update this section after every meaningful work session.

## Overall status

```text
Project phase: LOCAL DETERMINISTIC CORE
Proposal: COMPLETE
Hackathon qualification: FINAL STAGE
GitHub strategy: DECIDED — one organization, one monorepo
Implementation: EXPOSURE + RECOVERY DISCOVERY + REQUIREMENT COMPARISON COMPLETE / qualification graph next
```

## Progress table

| Area | Status | Notes |
|---|---|---|
| Proposal | DONE | Submitted and passed to final stage |
| Project naming | DONE | Material Continuity |
| GitHub organization strategy | DONE | One org |
| Repository strategy | DONE | One monorepo |
| Canonical demo flow | DEFINED | Based on proposal acceptance scenario |
| Synthetic dataset | IN PROGRESS | Material, stock, 2 BOMs, 10 production orders, delayed receipt, Candidate A/B/C, approved paths, suppliers, fallbacks, engineering requirements, and candidate evidence defined; qualification calendar and document corpus remain |
| Deterministic exposure engine | DONE | Typed dependency-free Python engine, JSON loader, CLI, and 10 passing tests; canonical shortage is 2026-10-04 |
| Recovery option discovery | DONE | Ordered deterministic search covers network stock through resequencing; approved sufficiency stops candidate escalation; 6 dedicated tests pass |
| Requirement comparison | DONE | Typed evidence/provenance, deterministic unit conversion, revision/applicability checks, MATCH/MISMATCH/UNKNOWN/BLOCKED, and canonical Candidate A/B decisions; 14 dedicated tests pass |
| Qualification graph | TODO | P0 |
| Recovery simulation | TODO | P0 |
| Recovery-case versioning | TODO | P0 |
| Approval gate | TODO | P0 |
| Action adapter | TODO | P0/P1 |
| AWS access validation | TODO | Do early |
| S3 document corpus | TODO | P1 |
| Bedrock Knowledge Base | TODO | P1 |
| Evidence Specialist | TODO | P1 |
| Recovery Supervisor | TODO | P1 |
| UI | TODO | P1 |
| EventBridge | TODO | P2 |
| Observability | TODO | P2 |
| SAP live integration | OUT OF MVP | Mock adapter is sufficient |

---

# 27. Session Progress Log

Append new entries; do not overwrite old ones.

## 2026-09-29 — Deterministic requirement comparison

### Completed

- Added application requirement fixtures for bore diameter, dynamic load, lubricant-temperature suitability, and plant qualification release.
- Added structured Candidate A/B evidence fixtures with document, revision, page, location, and applicability provenance.
- Implemented typed deterministic `compareRequirements()` behavior for `MATCH`, `MISMATCH`, `UNKNOWN`, and `BLOCKED`.
- Added deterministic unit normalization/conversion for MVP length, force, temperature, and speed units without introducing dependencies.
- Enforced fail-closed behavior for:
  - missing evidence;
  - incompatible units;
  - stale source revisions;
  - conflicting evidence;
  - non-applicable evidence;
  - malformed value types;
  - empty requirement sets.
- Added candidate-level decisions that reject hard mismatches while keeping missing evidence and unsatisfied release gates blocked.
- Added twelve unit tests and two canonical fixture integration tests.
- Verified all 30 repository tests pass and compilation succeeds.
- Verified the canonical decisions:
  - Candidate A: bore `MATCH`, load `MATCH`, lubricant evidence `UNKNOWN`, plant release `BLOCKED`;
  - Candidate B: bore `MISMATCH` with hard reject, load/lubricant `MATCH`, plant release `BLOCKED`.

### Next recommended action

1. define qualification task and resource-calendar fixtures;
2. implement the deterministic qualification dependency graph;
3. calculate sequential and parallel critical paths while preserving unresolved durations;
4. connect Candidate A's evidence gap to the required temperature test and review/release chain.

---

## 2026-09-29 — Deterministic recovery-option discovery

### Completed

- Added Candidate A, Candidate B, and Candidate C master fixtures plus supplier availability, ETA, quantity, quote, and source references.
- Added canonical recovery fixtures for:
  - network stock;
  - approved original source;
  - approved equivalent;
  - alternate BOM;
  - expired deviation;
  - original-part expedite;
  - production resequencing.
- Implemented typed, deterministic `findRecoveryOptions()` behavior with the required search order.
- Added quantity coverage across approved paths and early termination when approved options fully cover demand.
- Ensured unqualified candidates and fallbacks are surfaced only after timely approved paths are exhausted.
- Preserved availability versus readiness by reporting candidate ETA separately from approval status and by marking whether each option arrives by the need date.
- Added an auditable per-category search trace and fail-closed validation for duplicate IDs, invalid quantities/costs, and invalid request dates.
- Added five unit tests and one canonical fixture integration test.
- Verified all 16 repository tests pass, compilation succeeds, and the canonical search returns:
  - approved coverage: 0 of 700;
  - Candidate A/B: arrive by need date but remain unqualified;
  - Candidate C: arrives after need date and remains unqualified;
  - original expedite and production resequencing as non-authorized fallbacks.

### Next recommended action

1. add application requirement and candidate specification fixtures with source revision/page provenance;
2. implement deterministic unit normalization;
3. implement `compareRequirements()` for MATCH, MISMATCH, UNKNOWN, and BLOCKED;
4. prove Candidate B is rejected for the hard bore mismatch and Candidate A remains UNKNOWN for missing lubricant-temperature evidence.

---

## 2026-09-29 — Local bootstrap and deterministic exposure engine

### Completed

- Initialized the local Git monorepo.
- Added the recommended root scaffolding: `.gitignore`, `.env.example`, `README.md`, and `pyproject.toml`.
- Chose dependency-free Python 3.11 dataclasses and `unittest` for the first deterministic slice; no backend or frontend framework decision was made.
- Added the canonical local exposure fixtures:
  - one original bearing material with stock, allocation, and quality-hold quantities;
  - two effective BOM rows;
  - ten dated production orders;
  - one delayed receipt and one later confirmed receipt.
- Implemented deterministic `getExposure` behavior with:
  - usable-stock calculation;
  - confirmed time-phased receipts;
  - BOM-derived production consumption;
  - deterministic same-day priority ordering;
  - first-shortage detection;
  - affected-order quantities;
  - fail-closed validation for invalid stock, duplicate IDs, and ambiguous/missing BOM rows.
- Added a JSON-fixture CLI and JSON-safe structured output.
- Added nine unit tests and one fixture integration test covering exact depletion, receipts before/after shortage, zero stock, overlapping orders, unrelated products, repeat-call idempotence, duplicate IDs, and timestamp validation.
- Verified all 10 tests pass and the canonical fixture returns:
  - usable stock: 300;
  - shortage date: `2026-10-04`;
  - first affected order: `MO-004`;
  - affected orders: 7.

### Next recommended action

1. complete Candidate A/B/C and supplier-availability fixtures;
2. add network stock, approved-source/equivalent, alternate-BOM, and deviation fixtures;
3. implement deterministic `findRecoveryOptions()` in the required search order;
4. unit-test that approved recovery paths are exhausted before unqualified candidates are returned.

---

## 2026-09-28 — Project setup planning

### Completed

- Project proposal already completed.
- Team passed proposal screening and reached final stage.
- Project name confirmed as **Material Continuity**.
- GitHub organization naming discussed.
- Recommended organization/repository name: `material-continuity`.
- Decided to use one monorepo.
- Implementation order defined.
- Core architecture boundary defined:
  - LLM interprets/orchestrates;
  - deterministic code calculates/enforces;
  - humans authorize.

### Next recommended action

1. initialize local repository;
2. add this file as `PROJECT_CONTEXT.md`;
3. create repo folders;
4. lock synthetic demo dataset;
5. implement deterministic `getExposure()` before agent work.

---

# 28. Architecture Decision Records

Use this section for small ADRs.

## ADR-001 — Monorepo

**Status:** Accepted

**Decision:** Use one repository for web, agents, deterministic core, data, and infrastructure.

**Reason:** Team is small, system is tightly coupled, hackathon timeline rewards integration speed.

---

## ADR-002 — Deterministic calculations outside LLM

**Status:** Accepted

**Decision:** Stock depletion, numerical comparisons, qualification timing, scenario calculations, authorization checks, and idempotency are deterministic.

**Reason:** Reproducibility, auditability, proposal consistency, safety.

---

## ADR-003 — Two-agent architecture

**Status:** Accepted

**Decision:** Use:
1. Recovery Supervisor;
2. Evidence Specialist.

**Reason:** Matches proposal while avoiding unnecessary multi-agent complexity.

---

## ADR-004 — Human release authority retained

**Status:** Accepted

**Decision:** No autonomous BOM release, production release, or unrestricted purchasing.

**Reason:** Core safety and governance requirement.

---

## ADR-005 — Mock enterprise write for MVP

**Status:** Accepted

**Decision:** `createQualificationTask()` may produce a mock QMS task instead of live SAP write-back.

**Reason:** Proposal explicitly places live SAP write-back after MVP.

---

# 29. Testing Strategy

## 29.1 Unit Tests

Must cover:

### Exposure

- exact depletion date;
- receipts before shortage;
- receipts after shortage;
- zero stock;
- overlapping production orders;
- duplicate event input.

### Requirement Comparison

- exact match;
- min-bound match;
- max-bound match;
- mismatch;
- missing evidence;
- incompatible units;
- convertible units;
- wrong document revision;
- conflicting evidence.

### Qualification Timing

- sequential tasks;
- parallel tasks;
- missing completion time;
- unavailable resource calendar;
- qualification before shortage;
- qualification after shortage.

### Approval

- valid role;
- invalid role;
- expired approval;
- stale case version;
- changed case hash;
- duplicate idempotency key.

---

## 29.2 Integration Tests

- evidence extraction → deterministic comparison;
- supervisor → tool calls → recovery case;
- recovery case → approval gate;
- approval gate → action adapter;
- source update → case version increment;
- version increment → approval invalidation.

---

## 29.3 Acceptance Tests

The final system must successfully demonstrate:

```text
delay event
→ exposure calculation
→ no timely approved option
→ candidate discovery
→ hard mismatch rejection
→ UNKNOWN evidence gap
→ qualification timing
→ scenario comparison
→ human approval
→ mock QMS action
→ production release remains blocked
→ source revision change
→ approval invalidation
```

---

# 30. Pilot Metrics

`[PROPOSAL]`

These are **pilot targets**, not achieved results.

Do not present them as proven outcomes.

## Time to reviewable package

Measure:

```text
event → complete reviewable evidence package
```

Target:

```text
at least 50% lower median than manual baseline
```

## Time to approved decision

Measure:

```text
event → recorded approved decision
```

Target:

```text
lower, without higher reviewer effort
```

## Critical-gap detection

Measure:

```text
seeded missing/contradictory requirements detected
```

Target:

```text
100% of seeded critical gaps flagged
```

## Evidence traceability

Measure:

```text
supported MATCH rows with valid source/revision/location
```

Target:

```text
100%
```

No unsupported MATCH.

## Action integrity

Measure unauthorized/stale/duplicate actions.

Target:

```text
zero prohibited or duplicate writes
```

## Production exposure

Measure simulated:

```text
unserved units / late orders
```

Target:

```text
lower simulated exposure
```

Real production benefit requires a plant pilot and must not be claimed from the MVP.

---

# 31. Important Messaging Rules for Demo / Pitch

## Do say

```text
"The candidate is available, but it is not yet ready for assembly."
```

```text
"We calculate when the candidate becomes usable after evidence, testing, and release dependencies."
```

```text
"Missing evidence remains UNKNOWN rather than being inferred as compatible."
```

```text
"The agent coordinates the investigation, while deterministic services calculate constraints and humans retain release authority."
```

```text
"Our pilot target is at least a 50% reduction in median time to a reviewable package."
```

## Do not say

```text
"Our system automatically approves replacement parts."
```

```text
"Our agent decides whether a bearing is safe."
```

```text
"We reduce decision time by 50%."
```

unless this has actually been measured.

```text
"This is the first system in the market to do this."
```

The proposal intentionally does **not** claim market-first capability.

---

# 32. Innovation Positioning

`[PROPOSAL]`

The proposal explicitly acknowledges overlapping capabilities in:
- SAP Manufacturing Assistant;
- SAP Planning Assistant;
- SAP Product Design Assistant;
- generic procurement agents;
- manufacturing control towers;
- RAG systems;
- change-management / scenario agents.

The contribution is narrower:

> **Connect application-specific evidence and qualification dependencies to a material-shortage deadline, with version-bound execution controls.**

Do not exaggerate the novelty claim.

---

# 33. Scope Guardrails

When an AI coding agent proposes a feature, classify it.

## P0 — Directly required for canonical demo

Examples:
- exposure calculation;
- requirement comparison;
- qualification timing;
- evidence provenance;
- case versioning;
- approval gate.

## P1 — Important for judging / architecture credibility

Examples:
- Bedrock retrieval;
- supervisor orchestration;
- polished UI;
- action receipt;
- agent tool trace.

## P2 — Useful but non-critical

Examples:
- EventBridge;
- richer observability;
- advanced filters;
- extra dashboards.

## P3 — Post-MVP

Examples:
- live SAP write-back;
- supplier onboarding;
- complex CAD/drawing interpretation;
- advanced optimization;
- production-scale permissions model;
- multiple plants;
- real physical validation.

If a P2/P3 feature threatens P0 completeness, defer it.

---

# 34. Security / Safety Checklist

- [ ] Least-privilege IAM.
- [ ] No unrestricted procurement tool.
- [ ] No unrestricted BOM release tool.
- [ ] Retrieved content is data, not authorization.
- [ ] Approval tied to case version.
- [ ] Approval tied to action scope.
- [ ] Approval expiry enforced.
- [ ] Stale approvals fail closed.
- [ ] Duplicate writes blocked.
- [ ] Action receipt logged.
- [ ] Tool errors bounded.
- [ ] Retrieval retries bounded.
- [ ] Missing sources escalate to human review.
- [ ] Agent cannot fabricate missing evidence as MATCH.

---

# 35. Engineering Conventions

`[IMPLEMENTATION]`

Recommended:

## Typed schemas

Use typed request/response schemas for:
- tools;
- evidence rows;
- recovery cases;
- approval records;
- action receipts.

Prefer Pydantic / Zod / equivalent.

## Determinism

All deterministic functions should:
- accept explicit inputs;
- return structured outputs;
- avoid hidden global state;
- be unit-testable.

## Timestamps

Use ISO 8601 UTC internally.

Convert to local display only in UI.

## IDs

Suggested patterns:

```text
CASE-001
MAT-BRG-001
CAND-A
REQ-001
TEST-001
APR-001
ACT-001
```

## Logging

Log:
- case ID;
- case version;
- tool;
- input hash if useful;
- output status;
- duration;
- error code.

Do not log secrets.

---

# 36. Suggested Environment Variables

`[IMPLEMENTATION]`

Do not hardcode secrets.

Example `.env.example`:

```bash
AWS_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=

BEDROCK_MODEL_ID=
BEDROCK_KB_ID=

S3_DOCUMENT_BUCKET=
S3_CASE_BUCKET=

AGENTCORE_RUNTIME_ID=
AGENTCORE_GATEWAY_ID=

APP_ENV=development
LOG_LEVEL=INFO

FRONTEND_API_URL=http://localhost:8000
BACKEND_PORT=8000
```

Adapt based on final stack and AWS credentials model.

---

# 37. Open Questions

Track unresolved architecture decisions here.

- [ ] Which exact frontend framework?
- [ ] Which exact backend framework?
- [ ] Which persistence layer for recovery cases?
- [ ] Is DynamoDB enough for MVP or is relational storage preferable?
- [ ] What AWS Region is available?
- [ ] Which Bedrock model is permitted?
- [ ] Are AgentCore Runtime and Gateway available in the hackathon account?
- [ ] Will Knowledge Base ingest PDFs directly as expected?
- [ ] How will case hash be calculated?
- [ ] Which source changes trigger a new case version?
- [ ] Will scenario ranking be explicit weighted logic or non-ranked presentation?
- [ ] How realistic should supplier cost fixtures be?
- [ ] What user roles are needed in the UI?
- [ ] How will test calendars be represented?

Do not invent answers silently. Record the decision in ADRs when resolved.

---

# 38. Known Risks

## Risk 1 — Building the agent too early

Impact:
agent appears functional but core logic is unreliable.

Mitigation:
implement deterministic tools first.

---

## Risk 2 — Turning the system into a chatbot

Impact:
project loses its evidence-bound workflow differentiation.

Mitigation:
make recovery case, evidence matrix, dependency graph, and action gate first-class UI/state.

---

## Risk 3 — LLM performs arithmetic / safety logic

Impact:
non-reproducible decisions and weak judging credibility.

Mitigation:
keep calculations in deterministic services.

---

## Risk 4 — Overengineering AWS integration

Impact:
time lost on infra instead of end-to-end demo.

Mitigation:
prioritize canonical workflow; mock enterprise adapters where proposal allows.

---

## Risk 5 — UI hides the core innovation

Impact:
judges see “another manufacturing assistant.”

Mitigation:
visually emphasize:
- shortage deadline;
- arrival vs readiness;
- evidence gaps;
- qualification critical path;
- stale approval invalidation.

---

## Risk 6 — Unsupported novelty claims

Impact:
easy challenge from judges.

Mitigation:
use the proposal's focused contribution rather than “market first.”

---

# 39. AI Agent Operating Instructions

Any AI coding agent reading this file should follow these rules.

## Before coding

1. Read this entire file.
2. Inspect the existing repository.
3. Inspect recent commits.
4. Read current TODO/progress section.
5. Identify which phase is currently active.
6. Do not redesign architecture without a concrete reason.

## Before creating a new service/module

Ask internally:
- Does an existing module already own this responsibility?
- Is this deterministic or agentic?
- Does the canonical demo require it?
- Is it P0/P1/P2/P3?
- Does it preserve proposal boundaries?

## When uncertain

Prefer:
- explicit state;
- typed schemas;
- deterministic calculations;
- small tools;
- visible provenance;
- fail-closed behavior.

Avoid:
- magic hidden state;
- free-form JSON when typed schema is possible;
- LLM-generated arithmetic;
- autonomous write authority;
- unsupported assumptions;
- unnecessary agents.

## After meaningful work

Update:

```text
# 26. Current Progress Tracker
# 27. Session Progress Log
# 28. Architecture Decision Records
```

If an architecture decision changes, record:
- old decision;
- new decision;
- reason;
- consequences.

---

# 40. Suggested First Local Coding Session

`[IMPLEMENTATION]`

The first coding session should **not** involve Bedrock.

Goal:

> Make the core recovery scenario work deterministically using local JSON fixtures.

Recommended tasks:

```text
1. initialize repository
2. add project folder structure
3. add synthetic fixture schemas
4. create materials.json
5. create bom.json
6. create production_orders.json
7. create purchase_orders.json
8. implement getExposure()
9. write unit tests
10. print / return shortage date + exposed orders
```

Definition of done:

```text
Given a fixed stock level, known receipts, BOM consumption, and dated production orders,
the program produces a reproducible shortage date and affected-order list.
```

Only after this is correct should the implementation move to:
- recovery options;
- requirement comparison;
- qualification simulation;
- document retrieval;
- agents.

---

# 41. Minimal Local Scenario Fixture

`[IMPLEMENTATION — illustrative starting point]`

This is not official proposal data. It is a recommended fixture shape.

```yaml
material:
  id: BRG-001
  name: Assembly Bearing 25mm
  usable_stock: 300

demand:
  average_per_day: 100

original_supply:
  expected_delivery_day: 21

candidate_a:
  id: CAND-A
  eta_day: 2
  bore_mm: 25
  dynamic_load_kn: 16
  lubricant_temperature_evidence: null
  plant_release: false

candidate_b:
  id: CAND-B
  eta_day: 2
  bore_mm: 30
  dynamic_load_kn: 18
  plant_release: false

recovery:
  shortage_day: 3

qualification_candidate_a:
  temperature_test_days: 2
  engineering_review_days: 0.5
  quality_review_days: 0.5
```

Expected reasoning:

```text
Candidate B:
hard bore mismatch → reject

Candidate A:
delivery before depletion → yes
technical evidence complete → no
qualification complete before depletion → no
status → conditional / blocked pending qualification
```

---

# 42. README Relationship

This file is intentionally more detailed than `README.md`.

Recommended:

## README.md

Keep concise:
- what project does;
- how to run;
- architecture summary;
- links to docs.

## PROJECT_CONTEXT.md

Use as:
- AI-agent handoff;
- architecture memory;
- project decisions;
- progress tracker;
- scope guardrail.

README should link here:

```markdown
For architecture, business logic, current progress, and AI-agent handoff context,
see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md).
```

---

# 43. Source-of-Truth Hierarchy

If information conflicts, use this priority order:

```text
1. Latest explicit team decision
2. Submitted proposal
3. PROJECT_CONTEXT.md current ADRs
4. Implemented + tested behavior
5. AI-agent suggestion
```

An AI agent must not silently override levels 1–4.

If implementation intentionally deviates from proposal:
- document the deviation;
- explain why;
- assess whether demo/pitch language must change.

---

# 44. Final Project Mental Model

The shortest correct mental model is:

```text
A material disruption occurs.

The system first determines whether production is actually exposed.

It exhausts immediately usable approved recovery options.

If only unqualified candidates remain, it assembles application-specific evidence
and explicitly records what is known, mismatched, unknown, or blocked.

It then calculates whether the candidate can complete all required qualification
dependencies before the production recovery window closes.

The agent coordinates this investigation.

Deterministic services perform calculations and constraints.

Humans retain release authority.

Any approved action is tied to the exact case/evidence version reviewed.

If the evidence changes, stale authorization becomes invalid.
```

That is **Material Continuity**.

---

# 45. Immediate Next Action

Current recommended next step:

```text
Define qualification calendar fixtures and implement the deterministic
qualification dependency graph before starting Bedrock or agent orchestration.
```

When that is complete, update the progress tracker and continue to:

```text
simulateRecovery()
→ recovery case/versioning
→ evidence pipeline
→ agents
→ approval/action
→ UI
```
