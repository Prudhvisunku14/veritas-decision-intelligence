# Judge Q&A

## Why do you need an LLM?

The LLM is used only for language: intent understanding, persona adaptation, and evidence-grounded narrative synthesis. All quantitative truth is computed before the LLM call.

## How do you know the numbers are not hallucinated?

The LLM receives a structured Evidence Object. Numeric claims are expected to match fields in that object. The prototype also has a deterministic fallback narrative that requires no model.

## Why not use only Power BI/Tableau?

The differentiation is the governed end-to-end workflow: cross-source reconciliation, versioned KPI contracts, exact KPI bridge attribution, evidence-quality/abstention, pre-query security, decision-right-aware actions, and feedback/outcome tracking.

## Is Evidence Confidence Score a probability?

No. It is a deterministic composite evidence-quality score. It is never presented as a probability that an explanation is correct.

## What did you train?

Nothing is fine-tuned in the MVP. The analytical engine uses deterministic rules, statistical baselines, and decomposition. Feedback is stored for periodic recalibration.

## How do you handle causality?

Most outputs use "associated with" language. An optional Difference-in-Differences demonstration can estimate causal impact in a controlled treatment/control scenario.

## How do you prevent data leakage to the LLM?

Authorization is resolved before the SQL query is built. The LLM receives only the scoped Evidence Object, never unauthorized rows.
