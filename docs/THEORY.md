# Mathematical statements and complete proofs

These derivations restate and expand the supplied SAGE author manuscript. Equations are given in editable LaTeX. They are mathematical proofs under stated hypotheses; the supplied floating-point artifacts do not independently establish the interval hypotheses.

## 1. Domain and regularity

Let $D\subset\mathbb R^n$ be compact with $0\in\operatorname{int}D$, and let the closed-loop vector field $f_\kappa$ be locally Lipschitz on an open neighborhood of $D$, with $f_\kappa(0)=0$. Write $f$ for this fixed closed-loop field below. The subscript on $f_\kappa$ denotes a fixed controller and is independent of the scalar coupling strength used in Section 7.

Let $\phi:\mathbb R^n\to\mathbb R^r$ be $C^1$ and let $\varepsilon>0$. Define

$$V(x)=\varepsilon\|x\|^2+\|\phi(x)-\phi(0)\|^2. \tag{T1}$$

Every norm on a vector is Euclidean; every matrix norm is its induced 2-norm unless another norm is explicitly written. For radial Jacobian arguments, require $f\in C^1$ on a neighborhood of each radial hull under consideration. The benchmark square is star shaped; for a general non-star-shaped $D$, the field must also be defined on the portions of the radial hull outside $D$.

## 2. Positive definiteness and regularity — manuscript Theorem 3

**Statement.** $V\in C^1$, $V(0)=0$, $V(x)\ge\varepsilon\|x\|^2$, and $V$ is radially unbounded.

**Proof.** A squared norm is a finite sum of squares of its components. Composition and finite sums of $C^1$ functions remain $C^1$. At the origin both terms in (T1) vanish. For $x\ne0$, the first term is positive and the second is nonnegative. Finally $V(x)\ge\varepsilon\|x\|^2\to\infty$ as $\|x\|\to\infty$. ∎

Differentiating (T1) gives

$$\nabla V(x)=2\varepsilon x+2J_\phi(x)^\top[\phi(x)-\phi(0)]. \tag{T2}$$

## 3. Radial enclosure — manuscript Lemma 1

For an axis-aligned box $Q=[\ell,u]$, define

$$R(Q)=\operatorname{hull}(\{0\}\cup Q)=[\min(0,\ell),\max(0,u)], \tag{T3}$$

where the minimum and maximum act componentwise. For all $x\in Q$ and $t\in[0,1]$, $tx\in R(Q)$. The fundamental theorem of calculus gives

$$\phi(x)-\phi(0)=B(x)x,\quad B(x)=\int_0^1J_\phi(tx)\,dt, \tag{T4}$$

$$f(x)=F(x)x,\quad F(x)=\int_0^1J_f(tx)\,dt. \tag{T5}$$

**Statement.** If interval matrices $\mathcal J_\phi(R(Q))$ and $\mathcal J_f(R(Q))$ enclose the respective Jacobians everywhere on $R(Q)$, then they enclose $B(x)$ and $F(x)$ for every $x\in Q$. Sound interval operations applied to

$$G(x)=2\varepsilon I+2J_\phi(x)^\top B(x),\qquad
H(x)=\operatorname{sym}(G(x)^\top F(x))+cI \tag{T6}$$

also enclose $G(x)$ and $H(x)$. Here $\operatorname{sym}M=(M+M^\top)/2$ and $c>0$.

**Proof.** Fix an entry $i,j$. Its value in (T4) is the integral average of a continuous scalar function whose entire range is in the interval $[a_{ij},b_{ij}]$. Integration of $a_{ij}\le (J_\phi(tx))_{ij}\le b_{ij}$ over an interval of length one preserves these inequalities. This proves entrywise inclusion of $B$; the same argument proves inclusion of $F$. The endpoint Jacobian $J_\phi(x)$ can be bounded on $Q$ itself. Interval addition and multiplication that enclose their exact real results preserve these inclusions in (T6), even when dependency makes the result wider. ∎

For two tanh layers, $a_1=\tanh(W_1x+b_1)$, $\phi=\tanh(W_2a_1+b_2)$,

$$J_\phi(x)=D_2(x)W_2D_1(x)W_1,\quad D_i=\operatorname{diag}(1-\tanh^2 z_i). \tag{T7}$$

For the **main exported model**, the final activation is the identity, so $D_2=I$. The supplementary stress-test model uses both tanh layers. On a scalar interval $[a,b]$, $\tanh$ is monotone, and the minimum of $\operatorname{sech}^2$ occurs at the endpoint with largest absolute value. Its maximum is one if $0\in[a,b]$, otherwise it occurs at the endpoint closest to zero. All these endpoint evaluations require validated rounding when used in a machine proof.

## 4. Box-wise decrease — manuscript Theorem 2

Define the prescribed margin

$$m(x)=\nabla V(x)^\top f(x)+c\|x\|^2=x^\top H(x)x. \tag{T8}$$

**Statement.** Suppose a sound interval matrix encloses $H(x)$ for every $x\in Q$ and a sound scalar upper bound satisfies $\lambda_{\max}(H(x))\le\bar\lambda_Q<0$ throughout $Q$. Then

$$\dot V(x)\le-c\|x\|^2\quad(x\in Q), \tag{T9}$$

with a strictly negative margin for every nonzero $x$.

**Proof.** From (T2), (T4), and (T6), $\nabla V=Gx$; from (T5), $f=Fx$. The quadratic form of a skew-symmetric matrix is zero, so (T8) follows. The Rayleigh quotient for the symmetric matrix $H$ yields $m(x)\le\bar\lambda_Q\|x\|^2<0$ for $x\ne0$. At zero both sides of (T9) are zero. Subtracting $c\|x\|^2$ proves the result. ∎

For a symmetric interval matrix with diagonal upper endpoints $\bar h_{ii}$ and off-diagonal ranges $[\underline h_{ij},\bar h_{ij}]$, Gershgorin gives

$$\bar\lambda_Q=\max_i\left(\bar h_{ii}+\sum_{j\ne i}\max(|\underline h_{ij}|,|\bar h_{ij}|)\right). \tag{T10}$$

The maximum and the sums must also be bounded outward. A finite partition covering $D$ proves (T9) on $D$ if every leaf is discharged soundly. Away from zero, a direct interval evaluation with $\sup m(Q)\le0$ also suffices. A finite grid or partition geometry alone does not prove the inequality.

### Benchmark-specific factorization and the general Jacobian

For $f(x)=Ax+0.6x_1JPx$, the archived verifier uses the exact factorization

$$F_{\rm alg}(x)=A+0.6x_1JP,\qquad f(x)=F_{\rm alg}(x)x. \tag{T11}$$

This is sufficient for (T8) and avoids a looser enclosure. It need not equal the radial integral in (T5). The actual vector-field Jacobian is

$$J_f(x)=A+0.6[(JPx)e_1^\top+x_1JP], \tag{T12}$$

and its radial integral is $A+0.3[(JPx)e_1^\top+x_1JP]$. Multiplication of either factor by $x$ gives the same $f(x)$. In a general application, (T11) must not be substituted for the Jacobian; the omitted product-rule term matters.

### Quadratic upper and gradient bounds

If $\|B(x)\|\le\beta$ and $\|G(x)\|\le g$ on $D$, then

$$V(x)\le b\|x\|^2,\quad b=\varepsilon+\beta^2,\qquad
\|\nabla V(x)\|\le g\|x\|. \tag{T13}$$

The first inequality follows by (T1) and (T4); the second follows from $\nabla V=Gx$. A matrix interval $[L,U]$ admits the conservative norm bound $\|M\|_2\le\sqrt{\|K\|_1\|K\|_\infty}$ with $K_{ij}=\max(|L_{ij}|,|U_{ij}|)$. These computations require sound arithmetic if their outputs support a proof.

## 5. Invariant sublevel and exponential estimate — manuscript Corollary 1

**Statement.** Suppose on $D$

$$\varepsilon\|x\|^2\le V(x)\le b\|x\|^2,\qquad
\dot V(x)\le-c\|x\|^2, \tag{T14}$$

where $b,c>0$. Let $\rho>0$ and let the complete sublevel $\Omega_\rho=\{x:V(x)\le\rho\}$ be contained in $\operatorname{int}D$. Every solution with $x(0)\in\Omega_\rho$ exists for all $t\ge0$, remains there, and satisfies

$$\|x(t)\|\le\sqrt{b/\varepsilon}\,e^{-ct/(2b)}\|x(0)\|. \tag{T15}$$

**Proof.** The sublevel is closed and bounded by (T1), hence compact. On its boundary $V=\rho>0$, so $x\ne0$ and $\dot V<0$. A trajectory cannot exit to a larger value of $V$. More explicitly, integrating the differential inequality up to a first possible exit gives $V(t)\le V(0)$; a boundary trajectory immediately decreases, which rules out that exit. The solution therefore stays in a compact subset of the open existence domain. Local Lipschitz continuity and the standard continuation theorem preclude finite-time termination there. Since $V\le b\|x\|^2$, $\dot V\le-(c/b)V$. Integrating gives $V(x(t))\le V(x(0))e^{-ct/b}$. Apply the lower bound at $t$ and the upper bound at zero and take square roots. ∎

For $D=[-2,2]^2$ and $\varepsilon=0.02$, every point on or outside its boundary has $V\ge0.08$. Thus $\Omega_{0.04}\subset\operatorname{int}D$ follows **architecturally**. Invariance additionally requires the derivative inequality on that set; the numerical guarded calculation does not by itself prove it.

## 6. Structured robustness — manuscript Proposition 1

**Statement.** Assume (T14), $\|\nabla V(x)\|\le g\|x\|$ on $D$, and a locally Lipschitz perturbed field

$$f_{\rm true}(x)=f(x)+\delta Bx,\qquad
c_\delta=c-|\delta|g\|B\|>0. \tag{T16}$$

For a complete sublevel $\Omega_\rho\subset\operatorname{int}D$, the perturbed system is forward invariant there and

$$\|x(t)\|\le\sqrt{b/\varepsilon}\,e^{-c_\delta t/(2b)}\|x(0)\|. \tag{T17}$$

**Proof.** Cauchy–Schwarz and the induced matrix norm give

$$\begin{aligned}
\dot V_{\rm true}(x)
&=\nabla V(x)^\top f(x)+\delta\nabla V(x)^\top Bx\\
&\le-c\|x\|^2+|\delta|\,\|\nabla V(x)\|\,\|B\|\,\|x\|\\
&\le-c_\delta\|x\|^2.
\end{aligned}$$

The preceding invariance, continuation, and comparison proof applies with $c_\delta$ in place of $c$. ∎

The manuscript treats $\delta$ as a nonnegative perturbation magnitude. The absolute value in (T16) explicitly extends that convention to signed $\delta$. More generally $\|d(x)\|\le\mu\|x\|$ gives the reduced coefficient $c-g\mu$ under the same existence assumptions.

## 7. Two coupled subsystems — manuscript Proposition 2

**Statement.** Suppose (T14) and the gradient bound hold on $D$. Consider

$$\dot z_1=f(z_1)+\kappa(z_2-z_1),\qquad
\dot z_2=f(z_2)+\kappa(z_1-z_2), \tag{T18}$$

where $\kappa\in\mathbb R$. Set $V_\Sigma=V(z_1)+V(z_2)$ and $c_\Sigma=c-2|\kappa|g$. Then on $D\times D$

$$\dot V_\Sigma\le-c_\Sigma(\|z_1\|^2+\|z_2\|^2). \tag{T19}$$

If $|\kappa|<c/(2g)$ and $S_\rho=\{(z_1,z_2):V_\Sigma\le\rho\}\subset\operatorname{int}(D\times D)$, this sublevel is forward invariant and, for $z=(z_1,z_2)$,

$$\|z(t)\|\le\sqrt{b/\varepsilon}\,e^{-c_\Sigma t/(2b)}\|z(0)\|. \tag{T20}$$

**Proof.** Set $a=\|z_1\|$, $d=\|z_2\|$. The isolated terms sum to at most $-c(a^2+d^2)$. By the gradient bound and triangle inequality, the two coupling terms sum to at most

$$|\kappa|g[a(a+d)+d(d+a)]
=|\kappa|g(a+d)^2\le2|\kappa|g(a^2+d^2).$$

This proves (T19). Sum the two quadratic bounds in (T14), and apply the proof of Section 5 to the joint state and $c_\Sigma>0$. ∎

This is a sufficient bound for two identical diffusively coupled systems, not a general graph or ISS small-gain theorem. For the benchmark, the same floor implies $S_{0.04}\subset\operatorname{int}(D\times D)$.

## 8. Independent analytical benchmark identities

### Calibration system

$$A=\begin{bmatrix}-1&4\\-1/2&-1\end{bmatrix},\quad
P=\begin{bmatrix}17/48&7/24\\7/24&5/3\end{bmatrix},\quad
J=\begin{bmatrix}0&-1\\1&0\end{bmatrix}. \tag{T21}$$

Direct multiplication gives $A^\top P+PA=-I$. The leading minor $17/48>0$ and determinant $97/192>0$ show $P\succ0$. For $V_{\rm ref}=x^\top Px$ and the field in (T11),

$$\dot V_{\rm ref}=x^\top(A^\top P+PA)x+1.2x_1(Px)^\top J(Px)=-\|x\|^2. \tag{T22}$$

The last term vanishes because $J^\top=-J$. This is a global analytical certificate and is stronger than sampled evidence for a learned candidate.

### Non-polynomial reference

For $\dot x_1=-x_1+x_1x_2$, $\dot x_2=-x_2$, define

$$V_{\log}(x)=\log(1+x_1^2)+x_2^2. \tag{T23}$$

It is positive definite, smooth, and radially unbounded. Differentiation and completion of squares yield

$$\dot V_{\log}=
-\frac{x_1^2+2x_2^2+x_1^2x_2^2+(x_1-x_1x_2)^2}{1+x_1^2}<0\quad(x\ne0). \tag{T24}$$

All terms in the numerator are nonnegative, and $x_1^2+2x_2^2>0$ off the origin. Proper sublevels and the same continuation argument give global asymptotic stability. The claim that this polynomial vector field admits no global polynomial Lyapunov function is a cited result, not proved here: Ahmadi, Krstic, and Parrilo, CDC 2011, [doi:10.1109/CDC.2011.6161499](https://doi.org/10.1109/CDC.2011.6161499). A compact-domain neural experiment does not itself establish that global obstruction.

## 9. Numerical event and binomial bound

Fix the selected network before generating the test sample. Let $X_i$ be IID uniform on $D$ and define

$$E_\tau=\{x:\|x\|^2>10^{-8},\ m(x)>10^{-10}\}. \tag{T25}$$

The numerical implementation, precision, and tolerances are part of the experiment. The deterministic grid is excluded from the binomial trial count. If $p=\Pr(E_\tau)$, independence gives $\Pr(\text{zero events in }N)=(1-p)^N$. Inverting this probability at $\alpha=1-\gamma$ gives the exact one-sided zero-event Clopper–Pearson upper confidence endpoint

$$p_U=1-\alpha^{1/N}. \tag{T26}$$

At $N=200000$, $\gamma=0.95$, $p_U\simeq1.4978549\times10^{-5}$. This is a repeated-sampling confidence statement about the declared numerical event under this distribution. It does not bound the exact event $m(x)>0$, does not transfer automatically to another distribution, and does not imply continuum verification. With nonzero event counts, the zero-event formula must not be used.

## 10. Hard and soft CLF filters

For control-affine $\dot x=f_0(x)+g_0(x)u$, the hard filter minimizes $\|u-u_{\rm NN}(x)\|^2$ over $u\in U$ subject to $\nabla V^\top(f_0+g_0u)\le-c\|x\|^2$. If feasible throughout the operating set and the resulting dynamics admit solutions to which the derivative inequality applies, the same comparison proof establishes decay.

The soft filter adds $s\ge0$, a penalty $p s^2$, and allows $\nabla V^\top(f_0+g_0u)\le-c\|x\|^2+s$. Positive slack by itself does not imply strict decrease: it only gives the stated upper bound. A further bound such as $s(x)\le\sigma\|x\|^2$ with $\sigma<c$ would recover a reduced rate. Neither filter's numerical implementation is part of the supplied benchmark experiments; they are control-use formulations.
