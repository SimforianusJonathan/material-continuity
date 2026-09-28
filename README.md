# Material Continuity

Material Continuity is a versioned, evidence-bound workflow for recovering from
critical manufacturing material disruptions. The agent coordinates the
investigation, deterministic services perform calculations and enforce
constraints, and humans retain release authority.

The current implementation contains the first two local deterministic slices: a
synthetic bearing scenario, an exposure engine that calculates the first
shortage date and affected production orders, and ordered recovery-option
discovery that exhausts approved paths before surfacing unqualified candidates.
Structured candidate evidence can also be compared deterministically against
application requirements with revision, applicability, unit, and provenance
checks.
Candidate qualification dependencies can be scheduled against explicit resource
calendars to distinguish supplier arrival from actual production readiness.
Recovery simulation then compares substitute qualification, original expedite,
and production resequencing without treating feasibility as authorization.
These deterministic outputs can be assembled into immutable, hash-bound
recovery-case versions with approvals and actions referencing the exact version
reviewed.

## Requirements

- Python 3.11 or newer
- No third-party packages are required for the current slice

## Run the canonical exposure scenario

```powershell
python -m core.exposure --material MAT-BRG-001 --as-of 2026-09-29T00:00:00+00:00
```

## Run recovery-option discovery

```powershell
python -m core.recovery_options --material MAT-BRG-001 --required-quantity 700 --need-by 2026-10-04 --as-of 2026-09-29
```

## Compare candidate evidence

```powershell
python -m core.requirements --candidate CAND-A
python -m core.requirements --candidate CAND-B
```

## Build the qualification graph

```powershell
python -m core.qualification --candidate CAND-A
```

## Compare recovery scenarios

```powershell
python -m core.simulation --material MAT-BRG-001 --as-of 2026-09-29T00:00:00+00:00 --shortage-at 2026-10-04T00:00:00+00:00
```

## Build the canonical recovery case

```powershell
python -m core.case_state --case-id CASE-001
```

## Run tests

```powershell
python -m unittest discover -s tests -v
```

For architecture, business logic, current progress, and AI-agent handoff
context, see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md).
