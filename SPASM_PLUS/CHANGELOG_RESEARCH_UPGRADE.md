# SPASM++ Research Upgrade Changelog

## 2026-09-30

### Novelty upgrade
- Added sequential/anytime-valid test-martingale monitoring over conformal p-values.
- Added per-dimension conformal nonconformity and Benjamini-Hochberg FDR attribution.
- Added end-to-end detector/repair risk composition and empirical Clopper-Pearson risk ledger.
- Added long-session turn targets through 100 turns.

### Publication-readiness upgrade
- Removed the silent hashed-vector fallback from the primary conformal path.
- Enabled `sentence-transformers` and `scipy` in research requirements.
- Added BGE-M3 Nautilus-style clean-room baseline adapter.
- Added ContextEcho-style snapshot/probe and single-shot-anchor protocol adapter.
- Added calibration-data generation workflow with human screening requirement.
- Added human annotation protocol and agreement reporting guidance.
- Added cross-model configuration for four hosted model targets; availability must be verified before runs.
- Added numerical validation for the sequential conformal martingale.
- Fixed a tie-handling bug in the repository's pure-Python AUROC implementation.

### Honesty / reproducibility changes
- Added explicit validity assumptions for sequential conformal monitoring.
- Added explicit disclosure that the Nautilus/ContextEcho adapters are clean-room
  public-method implementations, not exact reproductions.
- Added `FINAL_RESEARCH_READINESS.md` with ratings and the remaining live-evaluation work.
- Removed local `.env` files, virtual environments, databases, and embedded API credentials from the distributable archive.
