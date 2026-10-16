# Verification status and limits

The mathematical results in [THEORY.md](THEORY.md) are conditional on the stated domain, regularity, and sound enclosure hypotheses. The archived numerical verifier uses ordinary MATLAB floating-point arithmetic and a fixed heuristic inflation. **No validated outward-rounded machine certificate is included.**

## What is established by which mechanism

| Claim | Support | Scope |
|---|---|---|
| `V(0)=0`, quadratic floor, radial unboundedness | Exact algebraic architecture | Every weight choice in real arithmetic |
| Calibration reference derivative `-||x||²` | Exact matrix and skew-symmetry identities | Global analytical statement |
| Logarithmic reference derivative is negative | Completed-square identity | Global analytical statement |
| No detected sample failures | Export evaluation and archived experiment records | Only the stated points and numerical event |
| IID failure-probability endpoint | Zero-event binomial inversion | Declared event, uniform IID distribution, fixed model |
| Partition covers the square | Binary geometry audit | Coverage alone, without sound margin bounds |
| Stored interval bounds and robustness numbers | Reproduced guarded MATLAB computation | Numerical targets; soundness remains unestablished |
| Continuum decrease, invariant sublevel, robust/coupled decay | Theorems plus sound bounds | Conditional until validated verification is supplied |

## Why fixed inflation is insufficient

The functions named `outward` in the original MATLAB sources subtract and add `1e-12*(1+M)`. Their names describe an intention; they do not establish directed rounding of each addition, product, reduction, or transcendental evaluation. A rigorous verifier must bound all such errors and its input encoding. See the primary [INTLAB interval-computation documentation](https://www.tuhh.de/ti3/rump/intlab/demos/html/dintval.html) for directed rounding and verified inclusions. INTLAB is not bundled, installed, or silently substituted in these experiments.

To upgrade these numerical targets, a verifier artifact would need to specify the exact interpreted weights and dynamics, sound elementary functions, the complete partition or reproducible search, rigorously discharged leaf conditions, and sound global upper bounds for `b` and `g`. Any unprocessed or unresolved leaf prevents the full-domain conclusion. Replacing a heuristic tolerance with a smaller tolerance does not establish this.

## Jacobian and factorization distinction

The main code uses `F_alg(x)=A+0.6*x1*J*P`, for which `F_alg(x)*x=f(x)` exactly in real arithmetic. It does **not** claim this matrix is the actual Jacobian. The general radial-Jacobian theorem can instead use the product-rule Jacobian and its integral, as shown in THEORY.md. Both factorizations give the same field when multiplied by `x`, and either soundly enclosed factor can support the quadratic-form argument.

The main feature output is linear; the stress-test output is tanh. Ignoring this difference changes the Jacobian and therefore the derivative test. The independent evaluator includes both architectures explicitly.

## Historical naming

Files named `formal_*`, fields such as `CertifiedPerturbationDelta`, and earlier document-generation scripts are preserved verbatim under `results/` and `provenance/`. These historical names are not a claim of validated arithmetic. Active verifier entry points issue a warning and call their outputs guarded numerical calculations. Legacy prototype `formal_verify_neural.m` is retained only for provenance and is not the public reproduction entry point.

The robustness threshold is sufficient for the stated linear perturbation class on a verified invariant sublevel. The coupling threshold is sufficient for two identical diffusive subsystems on a joint invariant sublevel. Neither is a global network guarantee. Positive slack in a soft CLF-QP does not itself establish Lyapunov decrease.
