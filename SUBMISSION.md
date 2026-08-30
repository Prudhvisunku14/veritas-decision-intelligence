# Submission Guide

## What to submit

1. This repository / ZIP file.
2. A short demo video or live walkthrough using `DEMO_SCRIPT.md`.
3. Architecture slide based on `ARCHITECTURE.md`.
4. Screenshots of:
   - material KPI alert,
   - Level-1 bridge decomposition,
   - Level-2 diagnosis with evidence confidence,
   - abstention case,
   - RBAC denial,
   - feedback and telemetry.
5. Optional evaluation table comparing hidden synthetic ground truth with estimated findings.

## MVP completion criteria

- [ ] Synthetic data generated from three sources at native grains.
- [ ] DuckDB initialized.
- [ ] Five KPI contracts load successfully.
- [ ] Revenue anomaly appears in the North incident window.
- [ ] Bridge contributions reconcile to the observed revenue delta.
- [ ] Business-driver diagnoses are shown separately from bridge contributions.
- [ ] Low-confidence marketing diagnosis abstains.
- [ ] North manager cannot query South.
- [ ] CEO and North manager receive different narratives.
- [ ] Actions come only from the controlled playbook.
- [ ] Feedback is stored, not applied instantly.
- [ ] Telemetry records latency and model metadata.
- [ ] Tests pass.

## Recommended pitch line

Veritas KPI is a governed evidence-to-action engine: deterministic analytics establishes the KPI truth, a structured Evidence Object captures provenance and uncertainty, the system abstains when evidence is weak, and only then does an LLM explain the result and translate it into an authorized business action.
