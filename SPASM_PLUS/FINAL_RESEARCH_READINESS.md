# Final Research Readiness — SPASM++

## What was implemented in this package

- Sequential test-martingale conformal monitor across turns.
- Explicit conditional-super-uniformity validity assumption.
- Multivariate per-dimension conformal p-values.
- Benjamini-Hochberg FDR attribution.
- End-to-end detector/repair risk composition using a conservative union bound.
- Exact one-sided empirical binomial upper bounds via Clopper-Pearson.
- Real-embedding-only primary conformal path; silent hashed fallback removed.
- Sentence-transformers and scipy research dependencies enabled.
- Clean-room Nautilus Compass-style baseline adapter.
- ContextEcho-style snapshot/probe and single-shot anchor protocol adapter.
- Human annotation protocol and calibration-data separation.
- Cross-model configuration expanded to four currently configured Groq targets.
- Long-session turn counts extended to 1/5/10/20/50/100.
- Sequential conformal numerical validation script.
- Unit tests for the new research modules.

## What is NOT completed inside this archive

The following require credentials, network/model access, or human participants
and therefore cannot be truthfully precomputed here:

- Real sentence-transformer model download and live embedding evaluation.
- Live LLM runs across multiple model families.
- Exact reproduction using the official Nautilus Compass/ContextEcho released
  artifacts and datasets.
- Human annotation and Cohen's kappa.
- Final held-out performance tables.
- Final statistical significance tests from real experiment outputs.

## Rating

- Novelty potential: **8.0/10**
- Algorithmic novelty: **6.5/10**
- Experimental readiness: **6.0/10**
- Human-grounded validity: **4.0/10**
- Reproducibility: **8.0/10**
- Overall submission readiness: **6.0/10**

These are project-readiness scores, not acceptance predictions.

## Final execution order

1. Create a clean research environment and install `backend/requirements.txt`
   plus `research/requirements-research.txt`.
2. Set `SPASM_SEMANTIC_BACKEND=embeddings`.
3. Generate >=50 calibration candidates/persona where budget permits and
   human-screen them.
4. Freeze calibration/dev/test splits.
5. Run single-shot conformal vs sequential conformal.
6. Run multivariate/FDR attribution and evaluate attribution precision.
7. Run Nautilus-style and ContextEcho-style conditions on the same benchmark.
8. Run SPASM++ repair and verification across at least three model families.
9. Run long-session experiments at 1/5/10/20/50/100 turns.
10. Obtain two independent human annotations on 300–500 held-out examples.
11. Compute kappa, precision/recall/F1, AUROC/AUPRC, calibration, repair
    persistence, utility/cost, and confidence intervals.
12. Compute the empirical end-to-end risk ledger on held-out data.
13. Run all ablations and cross-model checks.
14. Freeze results and write the paper.
