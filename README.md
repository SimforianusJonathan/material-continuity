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

## Run tests

```powershell
python -m unittest discover -s tests -v
```

For architecture, business logic, current progress, and AI-agent handoff
context, see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md).
