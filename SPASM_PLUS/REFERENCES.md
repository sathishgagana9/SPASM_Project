# Research references for the SPASM++ paper

## Persona drift / long-session evaluation

1. Wang, C. (2026). *Nautilus Compass: Black-box Persona Drift Detection for
   Production LLM Agents*. arXiv:2605.09863.
   https://arxiv.org/abs/2605.09863

2. Ding, X., Yu, Y., Liu, C., Zhao, B. (2026). *ContextEcho: A Benchmark for
   Persona Drift in Long Agentic-Coding Sessions*. arXiv:2605.24279.
   https://arxiv.org/abs/2605.24279

## Conformal / risk control in LLMs

3. Wang, Z. et al. (2025). *SConU: Selective Conformal Uncertainty in Large
   Language Models*. ACL 2025.
   https://aclanthology.org/2025.acl-long.934/

4. Bai, T., Jin, Y. (2026). *Conformal Selective Prediction with General Risk
   Control*. arXiv:2603.24704.
   https://arxiv.org/abs/2603.24704

5. Salem, M., Böhm, L., Pontes, D., Ferrugem, A. (2026). *Hierarchical
   Group-Conditional Conformal Risk Control for Selective Prediction in
   Language Models*. arXiv:2607.24562.
   https://arxiv.org/abs/2607.24562

6. Chen, C., Shen, J., Deng, Z., Lei, L. (2025). *Conformal Tail Risk Control
   for Large Language Model Alignment*. ICML 2025 / PMLR 267.
   https://proceedings.mlr.press/v267/chen25bd.html

## Conservative contextual bandits

7. Kazerouni, A., Ghavamzadeh, M., Yousefi, M. R., Van Roy, B. (2017).
   *Conservative Contextual Linear Bandits*. NeurIPS 2017.
   https://arxiv.org/abs/1611.06426

## General conformal background

8. Vovk, V., Gammerman, A., Shafer, G. (2005). *Algorithmic Learning in a
   Random World*. Springer.

9. Angelopoulos, A. N., Bates, S. (2023). *A Gentle Introduction to
   Conformal Prediction and Distribution-Free Uncertainty Quantification*.
   arXiv:2107.07511.
   https://arxiv.org/abs/2107.07511

## Reporting note

The 2026 persona-drift papers are directly relevant baselines. The conformal
literature is included to avoid overstating novelty: conformal significance,
selective risk control, and group-conditional risk control are established and
active areas. SPASM++ should claim novelty only for the specific application,
composition, or experimentally validated method introduced here.
