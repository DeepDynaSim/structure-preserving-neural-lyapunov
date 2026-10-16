# Reproducing the computations

## Environment

The supplied training logs identify MATLAB R2024b, Deep Learning Toolbox, and Control System Toolbox on an Intel i7-11800H CPU. Network learning uses single precision. An independent Python audit uses Python 3.10+ and NumPy, with double precision. Optional stress-test retraining needs PyTorch; it is not needed to inspect either supplied checkpoint.

## Python audit

From the repository root:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/audit_exports.py --output generated/python_audit.json
```

The commands verify supplied-artifact SHA-256 hashes, model gradients against finite differences, the quadratic orbital identity, the logarithmic square-completion identity, the binomial endpoint, and the archived partition's exact binary geometry. The model audit evaluates:

| Experiment | Grid | Independent random states | Domain | Event |
|---|---:|---:|---|---|
| Main export | 181 × 181 | 200,000 | `[-2,2]^2` | `q>1e-8` and `m>1e-10` |
| Non-polynomial export | 401 × 401 | 200,000 | `[-1.9,1.9]^2` | `q>1e-12` and `m>0` |

Here `q=||x||²` and `m=dot(V)+c*q`. Each random experiment has its own 200,000 trials; grid points are not included in either probability denominator. Each uses a fresh NumPy generator with seed 271828. This reproduces the experimental protocol, **not** MATLAB's random stream or the absent original stress-test random stream. The main field is evaluated using its actual exported `A,P,J`; the analytical identity test separately uses the exact rational `P` from the paper.

`artifacts/python_audit.json` records the checked repository preparation run. Expected non-polynomial grid worst ratio is approximately `-0.0198263290`, matching the manuscript's `-0.01983`. Independent Monte Carlo extrema need not equal the manuscript's extrema. The main NumPy grid worst ratio is approximately `-0.7067465`, whereas the archived MATLAB study reports a different worst ratio on its combined test set. Floating-point precision, gradient evaluation, and random streams differ; these reports are kept separately instead of being presented as identical reruns.

## Guarded interval calculation from the supplied main checkpoint

```matlab
addpath('matlab');
run_reproduction('verify');
```

Input: `results/revision/revision_experiments.mat`. Output: `generated/guarded_verification/`. This loads the original selected `dlnetwork`, uses the historical fixed `1e-12*(1+M)` inflation, scans local radii, and reproduces the branch-and-bound calculation. An explicit warning describes its arithmetic status. The following values were reproduced during repository preparation:

| Quantity | Value |
|---|---:|
| Selected seed | 20260834 |
| Explored tree nodes | 6,541 |
| Accepted leaf boxes | 3,271 |
| Central leaves / direct leaves | 20 / 3,251 |
| Unresolved leaves | 0 |
| Central radius | 0.2 |
| Local eigenvalue upper target | -0.0902273035 |
| Gradient coefficient target `g` | 4.6406655294 |
| Value coefficient target `b` | 3.7699727838 |
| Perturbation threshold target | 0.1104129170 |
| Absolute coupling threshold target | 0.0161614750 |

The node count includes internal split nodes; it is not the number of terminal boxes. The geometry audit checks coverage and absence of overlaps for the stored binary partition, but it does not independently validate the margin bounds. See [verification status](VERIFICATION_STATUS.md).

## Full original learning study

```matlab
addpath('matlab');
run_reproduction('full');
```

This calls, in order:

1. `simulate_neural_lyapunov`: calibration baseline, derivative-aware feature learning, grid and random testing, trajectories, robustness and scaling examples.
2. `revision_training_study`: ten principal seeds, held-out selection, cumulative ablations, derivative-trained unconstrained comparator, 17 sensitivity configurations, pendulum and four-state benchmarks.
3. `revision_formal_verifier`: guarded interval calculation for the newly selected model.

This can take many minutes on CPU. New timings and training results depend on the MATLAB release, hardware, numerical kernels, and execution environment. Repository preparation reran the supplied-checkpoint verifier and short reconstructed training smoke test; it did **not** rerun the complete ten-seed/ablation/sensitivity training campaign. The original complete campaign outputs are supplied unchanged.

Principal settings: seeds 20260826–20260835; 2,200 iterations; 2–24–8 features with tanh hidden activation and linear output; `epsilon=0.02`, `c=0.15`, `eta=0.05`; hinge weight 8; value anchor weight 0. Uniform batch 704, near-origin batch 128, hard-state batch 192; refresh 12,000 candidates every 200 iterations. Validation: 50,000 states, seed 314159. Final testing: 181 × 181 grid plus an independent 200,000-state uniform sample, seed 271828. Original combined-set statistics remain in the archived CSVs.

The active public copy now computes the Monte Carlo event count for the selected model on `XtestRandom` directly. Its zero-event confidence formula runs only when that count is zero. The historical source hard-coded zero in the exported confidence table; the original file is preserved for provenance.

## Non-polynomial training reconstruction

The exact supplied supplementary model is evaluated by the Python audit without retraining. The supplied archive contains weights and the seed but not its historical training program, iteration count, optimizer settings, or RNG state. To provide executable derivative-only candidate-generation examples, this repository adds two explicitly reconstructed trainers:

```matlab
addpath('matlab');
train_nonpolynomial(5000);
```

```sh
python -m pip install torch
python scripts/train_nonpolynomial.py --iterations 5000 --seed 20261016
```

Both use bias-free 2–8–4 features with two tanh activations, the published domain, floor, and decay coefficient. Their newly chosen settings are recorded with their output. No exact reference values enter their loss. These examples generate new candidates; neither is represented as the missing historical source or guaranteed to produce a successful certificate. Test any trained candidate independently before interpreting it.

## Source and figure handling

`provenance/original_sources/` preserves all `.m`, `.py`, and `.ps1` source files supplied in `article_build/` and `article_revision/`. Earlier manuscript builders retain their original assumptions and filesystem paths; they are historical source, not a builder for the final SAGE manuscript. No final SAGE-generation script was supplied. The final DOCX and six embedded images are preserved unchanged. Numerical figure-generation code remains in the original MATLAB sources. The stress-test figure is available as the embedded manuscript asset; the original script that generated that figure was absent.
