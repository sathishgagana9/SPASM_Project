# Calibration data

The primary conformal detector requires a held-out calibration set of real,
persona-consistent assistant responses. Do **not** reuse the test set.

Generate calibration responses with `research/experiments/build_calibration.py`
using the same model family/configuration used for the target evaluation, then
review them for persona consistency before accepting them into calibration.

For alpha=0.05, the current split-conformal implementation requires at least
19 calibration examples for a nontrivial minimum p-value. In practice, use a
substantially larger and diverse set (the recommended target is >=50 per
persona when budget permits).
