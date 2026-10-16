# Manuscript and implementation correspondence

The unchanged DOCX in `manuscript/` is the reference author manuscript. This map records the actual supplied sources and scientific differences found while preparing the public repository; no manuscript text has been silently revised.

| Manuscript content | Source or artifact |
|---|---|
| Candidate, derivative-aware objective, sampling and main model selection | `matlab/revision_training_study.m` |
| Lemma 1, Theorems 2 and 3, Corollary 1, Propositions 1 and 2 | `docs/THEORY.md`, Sections 2–7 |
| Appendices A.1–A.3 | `docs/THEORY.md`, Sections 3–5 |
| Calibration dynamics and exact reference | `scripts/models.py`, `tests/test_models.py`, original MATLAB sources |
| Grid and IID event definition | `scripts/audit_exports.py`, active MATLAB Monte Carlo count |
| Guarded branch-and-bound and coefficient estimates | `matlab/revision_formal_verifier.m` |
| Non-polynomial checkpoint | `results/nonpolynomial/Supplementary_Nonpolynomial_Network_Model.json` and CSV |
| Non-polynomial logarithmic certificate | `docs/THEORY.md`, Section 8, and square-completion test |
| Hard/soft CLF formulations | `docs/THEORY.md`, Section 10; conceptual, no supplied CLF-QP experiment |
| Table 2 | `results/revision/multiseed_metrics.csv`, `multiseed_summary.csv`, `monte_carlo_confidence.csv` |
| Table 3 | `results/revision/formal_verification_metrics.csv`, `formal_verified_partition.csv` |
| Table 4 | `results/revision/ablation_metrics.csv`, `sensitivity_metrics.csv` |
| Table 5 | `results/revision/derivative_unconstrained_metrics.csv` and analytical/selected-model results |
| Figure 2 | `results/base/fig02_source_example_audit.*` |
| Figure 3 | `results/revision/fig08_multiseed_statistics.*` |
| Figure 4 | `results/revision/fig11_interval_verification.*` |
| Figure 5 | `results/revision/fig12_certified_candidate_fields.*` |
| Figure 6 | `results/revision/fig09_ablation_sensitivity.*` |
| Figure 7 | Sixth embedded figure in the supplied manuscript; original generating script absent |

## Correspondence notes

1. **Feature activation.** The main MATLAB `make_feature_net` applies tanh after the first affine layer and leaves the second affine output linear. Thus its Jacobian is `W2*D1*W1`; use `D2=I` when specializing manuscript equations (14), (38), and (39). The non-polynomial export uses tanh after both affine layers. The two-tanh interpretation reproduces its reported grid worst ratio `-0.01983`; the linear-output interpretation does not. Both remain covered by the general `C1` architecture proof.

2. **Field factor.** The matrix printed as `F(x)=A+0.6*x1*J*P` in Appendix A is a valid direct factor satisfying `f(x)=F(x)x`. It is distinct from both the true Jacobian and its radial integral. THEORY.md supplies the product-rule term and explains why the benchmark-specific factor is still usable.

3. **Perturbation sign.** The manuscript's `delta` is interpreted as a nonnegative magnitude. The repository proof uses `abs(delta)` explicitly for signed perturbations. The coupling condition always uses `abs(kappa)`.

4. **Confidence computation.** The original study evaluates a combined grid/random set for many tables and hard-codes zero in its confidence CSV construction. The active public copy counts the selected model's event on the IID states alone and applies the zero-event formula conditionally. Archived CSVs are unchanged.

5. **Residual column name.** The manuscript describes the reported `PDERMSE` value as normalized, but the original `evaluate_positive` function computes `sqrt(mean((dotV+q).^2))` without dividing by `q+eta`. The optimization objective is normalized; the exported evaluation column is a raw transport residual. This historical labeling difference is documented, and the original numbers are retained.

6. **Input precision.** The main exported `P` was stored after conversion to single precision, so its decimals differ from the exact rational `P` in the analytical proof. The independent learned-model audit uses the exported dynamics; the analytical identity check uses the exact rational matrix. Neither representation is silently substituted for the other.

7. **Figure and equation labels.** The supplied SAGE file contains six figures captioned 2–7. Its equation sequence runs to (45), with an additional Clopper–Pearson expression that is not numbered in the same way. These are properties of the supplied source, despite the earlier preparation summary describing a fully consecutive presentation. This repository includes the file unchanged and gives its own theory equations distinct `T` labels.

8. **Unavailable historical sources.** The supplementary ZIP supplies the stress-test weights, metadata, and README only. Its original training script, exact optimization schedule, final random sample, and figure-generation script were not supplied. New trainers are explicitly marked reconstructions. Earlier DOCX builders are included as historical source, but the final SAGE builder is also absent.

9. **Soundness.** Guarded numerical values are reproducibility targets. The archive contains no independent validated interval proof, formal prover development, or general high-dimensional verification certificate. Complete mathematical derivations are provided in source form, with their machine-verification hypotheses explicit.
