"""Build the peer-review revised, interval-verified neural Lyapunov article."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
sys.path.insert(0, str(WORKSPACE))
from article_build import build_manuscript as bm  # noqa: E402


ORIGINAL_RESULTS = WORKSPACE / "article_build" / "results"
RESULTS = HERE / "revision_results"
OUTPUT_DIR = WORKSPACE / "output" / "docx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUTPUT_DIR / "Interval_Verified_Structure_Preserving_Neural_Lyapunov_Certificates_Revised.docx"


def read_csv(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def metric_map(name: str) -> dict[str, float]:
    return {row["Metric"]: float(row["Value"]) for row in read_csv(name)}


def add_figure(doc: Document, path: Path, caption: str, alt: str, width=6.45) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    shape = p.add_run().add_picture(str(path), width=Inches(width))
    shape._inline.docPr.set("descr", alt)
    shape._inline.docPr.set("name", alt[:120])
    bm.add_caption(doc, caption)


def add_title_block(doc: Document) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(10)
    bm.set_run_font(p.add_run("REVISED RESEARCH ARTICLE  •  AUGUST 2026"), size=10, bold=True, color=bm.TEAL)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    bm.set_run_font(
        p.add_run("Interval-Verified Structure-Preserving Neural Lyapunov Certificates for Intelligent Nonlinear Control"),
        size=22, bold=True, color=bm.NAVY,
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    bm.set_run_font(
        p.add_run("Failure-aware synthesis, certified regions of attraction, robustness bounds, and compositional scaling"),
        size=12.5, italic=True, color=bm.DARK_BLUE,
    )
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
    bm.set_run_font(p.add_run("Çağlar Uyulan"), size=12, bold=True, color=bm.BLACK)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
    bm.set_run_font(
        p.add_run("Department of Mechanical Engineering, Faculty of Engineering and Architecture, İzmir Kâtip Çelebi University, İzmir, Türkiye"),
        size=9.5, color=bm.MUTED,
    )
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(16)
    bm.set_run_font(
        p.add_run("Correspondence: caglar.uyulan@ikcu.edu.tr  |  ORCID: 0000-0002-6423-6720"),
        size=9.5, color=bm.MUTED,
    )


def configure_header(doc: Document) -> None:
    p = doc.sections[0].header.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    bm.set_run_font(p.add_run("INTERVAL-VERIFIED NEURAL LYAPUNOV CERTIFICATES"), size=8.5, bold=True, color=bm.MUTED)


def ref_paragraph(doc: Document, text: str, url: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.28)
    p.paragraph_format.first_line_indent = Inches(-0.28)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    bm.set_run_font(p.add_run(text + " "), size=9, color=bm.BLACK)
    bm.add_hyperlink(p, "DOI record" if "doi.org" in url else "Source record", url, color=bm.BLUE, underline=False)


def build() -> None:
    formal = metric_map("formal_verification_metrics.csv")
    summary = read_csv("multiseed_summary.csv")[0]
    mc = read_csv("monte_carlo_confidence.csv")[0]
    ablation = read_csv("ablation_metrics.csv")
    sensitivity = read_csv("sensitivity_metrics.csv")
    benchmarks = read_csv("benchmark_suite_metrics.csv")
    unconstrained = read_csv("derivative_unconstrained_metrics.csv")[0]

    doc = Document()
    bm.setup_styles(doc)
    bm.setup_page(doc)
    configure_header(doc)
    add_title_block(doc)

    bm.section(doc, "Abstract", 1)
    bm.add_body(doc,
        "Neural Lyapunov functions can enlarge the representational class available to nonlinear control, but a fitted surface becomes a stability certificate only after its equilibrium, positivity, orbital derivative, and invariant-domain claims are proved. This revised study develops an auditable pipeline around the structure-preserving candidate Vθ(x)=ε||x||²+||ϕθ(x)-ϕθ(0)||² and resolves the distinction between candidate generation, sampled falsification, and continuum verification. The starting article and code associated with Efficient Computation of Lyapunov Functions Using DNNs are treated as a reproducibility case study: an even-power example is shown analytically to admit positive orbital derivatives and finite escape, demonstrating why value regression is insufficient. The revised principal method uses no analytical value anchors, separates model selection from an untouched final test, and is evaluated over ten independent training seeds. All ten runs pass the sampled decay gate; the mean normalized transport residual is 0.11987±0.00376 and the mean worst normalized decay margin is -0.70089±0.00496. On 200,000 independent Monte Carlo states, zero violations imply a one-sided 95% Clopper-Pearson upper failure-probability bound of 1.50×10⁻⁵. More importantly, a conservative interval/Jacobian branch-and-bound procedure verifies dot(Vθ)+0.15||x||²≤0 over the full square [-2,2]² for the selected no-anchor network: 6,541 boxes are explored, no box remains unresolved, and a local matrix bound closes the origin neighborhood. The same proof artifacts yield Vθ≤3.76998||x||², a certified invariant sublevel Ω0.04, an exponential state bound, a structured uncertainty radius δ<0.11041, and a learned compositional small-gain threshold κ<0.01616. Cumulative ablations, 17 sensitivity settings, a torque-saturated inverted pendulum, and a four-state nonlinear oscillator test identify which conclusions are formal and which remain empirical. The resulting contribution is not a new isolated loss term; it is a failure-aware synthesis and evidence protocol that couples exact architectural constraints, normalized Lyapunov transport learning, independent statistics, explicit uncertainty accounting, and machine-checkable interval verification for intelligent control.")
    p = doc.add_paragraph()
    bm.set_run_font(p.add_run("Keywords: "), bold=True, color=bm.NAVY)
    p.add_run("Lyapunov stability; neural certificates; intelligent control; interval analysis; branch-and-bound; region of attraction; robust nonlinear control; compositional systems")

    bm.section(doc, "Research highlights", 1)
    bullets = bm.create_numbering(doc, bullet=True)
    for item in [
        "The principal 2-24-8 tanh certificate is trained without analytical Lyapunov-value anchors and tested across ten independent seeds.",
        "A guarded interval/Jacobian branch-and-bound verifier discharges the prescribed derivative inequality on the entire claimed square with no unresolved boxes.",
        "A certified sublevel set, exponential decay constants, a structured uncertainty radius, and a learned compositional small-gain threshold are reported numerically.",
        "Cumulative ablation and 17-setting sensitivity studies separate the effect of transport learning, hinge penalties, near-origin sampling, anchors, hard-state recycling, and network size.",
        "Additional actuator-saturated and four-dimensional benchmarks broaden empirical evidence while preserving a clear boundary around the formally verified two-dimensional claim.",
    ]:
        bm.add_list_item(doc, item, bullets)
    bm.add_callout(doc, "Claim taxonomy.",
        "Architectural means true for every network weight by algebra; sampled means tested on the stated finite set; interval-verified means the exported network and dynamics were discharged on every box of the stated continuum under the documented floating-point guard model. Only the principal two-state benchmark receives the third label.", "warning")

    bm.section(doc, "1. Introduction", 1)
    bm.add_body(doc,
        "Lyapunov theory replaces an infinite-horizon trajectory question with inequalities on a scalar energy-like function. For a locally Lipschitz closed-loop vector field, a positive function with a strictly negative orbital derivative proves stability without requiring a closed-form state trajectory [1-3]. The same object supports region-of-attraction (ROA) estimation, control-Lyapunov-function quadratic programs, robust and adaptive control, observer design, and networked small-gain arguments [4,5,28,29]. Constructing it remains difficult: quadratic equations are decisive for linear systems, polynomial sum-of-squares (SOS) programs extend the reach to semialgebraic dynamics, and rational or PDE-based constructions address cases where polynomial templates are restrictive [6,7,30].")
    bm.add_body(doc,
        "Deep neural networks offer flexible differentiable templates, but approximation power is not the missing theorem. A small value error does not bound the projected gradient error ∇e(x)ᵀf(x), and therefore does not preserve the sign of dot(V). The literature has consequently progressed from value fitting to positive-definite architectures, learner-falsifier loops, SMT verification, bound propagation, verifier-aware controller synthesis, Zubov-domain expansion, and training-time branch-and-bound [11-24]. Lyapunov-Net established a peer-reviewed positive architecture at CDC 2022 [14]; Yang et al. formally verified state- and output-feedback neural control with post-hoc branch-and-bound [20]; Liu et al. connected Lyapunov and Zubov PDE learning to verification and ROA estimation [22]; Li et al. expanded verified ROAs through two-stage Zubov sampling [23]; and CT-BaB aligned training with certified bounds [24].")
    bm.add_body(doc,
        "This work began from the 2023 preprint Efficient Computation of Lyapunov Functions Using Deep Neural Networks [8]. The revised article does not claim that positivity architecture, transport residuals, counterexample mining, or interval splitting are individually new. Its contribution is a reproducible synthesis built after an equation-code audit: a concrete failure is isolated; the main learner is stripped of privileged analytical anchors; selection and final testing are separated; seed variation and ablations are quantified; a continuum derivative claim is discharged; and robustness, ROA, and compositional constants are derived from the verified bounds.")
    bm.add_body(doc, "The specific contributions are:")
    numbered = bm.create_numbering(doc, bullet=False)
    for item in [
        "a source-fidelity audit showing analytically and numerically why the original even-power example cannot support the claimed stability conclusion;",
        "a smooth structure-preserving neural candidate with exact equilibrium anchoring and a global quadratic lower bound, trained through a normalized Lyapunov transport equation and a prescribed-decay hinge;",
        "a guarded interval/Jacobian branch-and-bound verifier with exported weights, dynamics, partition, metrics, and execution log;",
        "a certified ROA sublevel, exponential estimate, structured robustness radius, and learned-certificate compositional small-gain theorem;",
        "ten-seed statistics, an untouched final set with an exact binomial confidence bound, a cumulative ablation, 17 sensitivity configurations, and two additional nonlinear benchmarks; and",
        "an intelligent-control deployment interpretation that distinguishes an offline Lyapunov proof from online policy performance and uncertainty monitoring.",
    ]:
        bm.add_list_item(doc, item, numbered)

    add_figure(doc, ORIGINAL_RESULTS / "fig01_method_workflow.png",
        "Figure 1. Revised evidence pipeline. Candidate generation, independent falsification, continuum interval verification, and deployment are separate gates; any failed gate returns the model to training or shrinks the claim domain.",
        "Workflow showing audited dynamics, positive neural architecture, transport learning, independent validation, interval branch-and-bound verification, and intelligent-control deployment.", 5.8)

    bm.section(doc, "2. Stability framework and evidence hierarchy", 1)
    bm.section(doc, "2.1 Closed-loop problem", 2)
    bm.add_body(doc, "After shifting an equilibrium to the origin, consider the autonomous closed loop")
    bm.add_native_equation(doc, "ẋ=fκ(x):=f(x,κω(x)),     fκ(0)=0,     x∈D⊂ℝⁿ.", 1)
    bm.add_body(doc, "Assume fκ is locally Lipschitz on an open set containing the compact verification domain D. A continuously differentiable V is a strict Lyapunov function on D if")
    bm.add_native_equation(doc, "V(0)=0,     V(x)>0,     V̇(x)=∇V(x)ᵀfκ(x)<0,     x∈D∖{0}.", 2)
    bm.add_body(doc, "A level set Ωρ={x:V(x)≤ρ} is a certified inner ROA estimate only when Ωρ⊂int(D); decrease then prevents an outward crossing of its boundary.")
    bm.add_native_equation(doc, "Ωρ:={x:V(x)≤ρ},     Ωρ⊂int(D),     V̇<0 on Ωρ∖{0}.", 3)

    bm.section(doc, "2.2 Why value accuracy is not derivative validity", 2)
    bm.add_body(doc, "Let V̂=V*+e where V* is valid. Even a small uniform value error leaves the gradient error uncontrolled:")
    bm.add_native_equation(doc, "V̂̇=V̇*+∇e(x)ᵀfκ(x).", 4)
    bm.add_body(doc,
        "An arbitrarily small high-frequency e can reverse the second term. The operative quantities are therefore V(0), a positive lower bound, a decay margin, domain containment, and a proof of those inequalities—not regression RMSE alone. The derivative-trained unconstrained comparator in Section 7 illustrates a subtler version: it has positive sampled values but still leaves three prescribed-margin failures on the untouched test set.")

    bm.section(doc, "2.3 What each validation layer establishes", 2)
    bm.add_table(doc,
        ["Layer", "Mechanism", "Valid conclusion", "What remains"],
        [
            ["Algebraic architecture", "ε||x||² plus a squared feature difference", "V(0)=0 and V≥ε||x||² for all x", "Derivative sign and useful level-set size"],
            ["Independent sampling", "held-out grid, Monte Carlo, trajectories", "Finite-set falsification and statistical evidence", "Uniform continuum inequality"],
            ["Interval/Jacobian BaB", "sound over-approximations and adaptive box splitting", "All states in the encoded domain satisfy the bound", "Unmodeled dynamics and implementation mismatch"],
            ["Robustness theorem", "gradient and model-error gains", "Stability for a quantified uncertainty class", "Validity of the uncertainty envelope"],
            ["Compositional theorem", "local decay and small-gain bound", "Scalable interconnection result under stated coupling", "Heterogeneous or unmodeled couplings"],
        ], [1650, 2550, 2460, 2700], "Table 1. Evidence layers and their epistemic scope.", 8.5)

    bm.section(doc, "2.4 Position relative to classical and modern methods", 2)
    bm.add_table(doc,
        ["Family", "Representative method", "Strength", "Limitation / role here"],
        [
            ["Quadratic / LMI", "AᵀP+PA≺0", "Exact and inexpensive for linear dynamics", "Used as an analytical gold standard"],
            ["SOS / SDP", "Polynomial V and multiplier constraints", "Machine-checkable semialgebraic certificate", "Degree and dimension growth; no superiority claim is made"],
            ["Rational Lyapunov", "p(x)/q(x), q>0", "Can represent non-polynomial geometry", "Denominator positivity and nonconvex search"],
            ["Lyapunov-Net", "positive neural architecture [14]", "Positivity by construction", "Our Eq. (6) is a smooth vector-feature specialization"],
            ["Physics-informed / SMT", "Lyapunov or Zubov PDE plus dReal [22]", "PDE theory, ROA, formal verification", "Different solver; motivates terminology correction"],
            ["α,β-CROWN / BaB", "Yang et al. [20], Li et al. [23]", "Scalable verified controller and ROA synthesis", "Stronger general verifier than the low-dimensional interval implementation here"],
            ["CT-BaB", "certified bounds during training [24]", "Verification-aware partitions and larger verified ROA", "Our splitting is post-training, not CT-BaB"],
            ["Compositional ISS", "Zhang et al. [18]", "Scales through subsystem gains", "Our learned result is a two-subsystem small-gain instance"],
        ], [1500, 2300, 2500, 3060], "Table 2. Relationship to classical and current neural-certificate baselines.", 8.2)

    bm.section(doc, "3. Source-fidelity audit", 1)
    bm.section(doc, "3.1 Paper-code reconciliation", 2)
    bm.add_body(doc,
        "The baseline PDF [8], its associated notebooks, and the local MATLAB material were inspected as one evidence set. The notebooks primarily fit known Lyapunov values; a later visualization cell changes the vector field; paper and code differ in the exponent of one four-state channel; and one MATLAB checker pairs coordinates rather than forming the intended Cartesian product. These are not editorial details: each changes the quantified stability statement.")
    bm.add_table(doc,
        ["Audited item", "Observation", "Consequence", "Revision"],
        [
            ["Gradient bounds", "A vector is compared with scalar radial bounds", "Condition is dimensionally undefined", "Bound V and the scalar orbital derivative separately"],
            ["Even-power state", "ẋ₁=-x₁² with a term x₁⁴ in V", "-4x₁⁵>0 for x₁<0", "Reject the pair; do not repair it by regression"],
            ["Paper vs code", "Dynamics differ across artifacts", "Reproduction target is ambiguous", "Export equations and matrices beside the model"],
            ["Value supervision", "MSE fits a known candidate", "No derivative-sign guarantee", "Train the transport and decay equations"],
            ["Grid construction", "Paired samples replace a Cartesian grid", "Large regions are untested", "Use meshgrid plus independent Monte Carlo sampling"],
        ], [1700, 2500, 2460, 2700], "Table 3. Source-audit findings and corrections.", 8.4)

    bm.section(doc, "3.2 Analytical counterexample", 2)
    bm.add_body(doc, "For the displayed candidate V=x₁⁴+x₂²+x₃⁶+x₄² and even-power dissipative channels, the computed orbital derivative is")
    bm.add_native_equation(doc, "V̇=-4x₁⁵-2x₂²-6x₃⁷-2x₄².", 5)
    bm.add_body(doc,
        "Setting x₂=x₃=x₄=0 and x₁<0 gives dot(V)>0. Moreover, ẋ=-x² has x(t)=x₀/(1+x₀t), so x₀=-0.5 has a pole at t=2. In the local audit, 19.0952% of 250,000 uniform samples violate decrease. The corrected study therefore uses a different nonlinear system whose exact energy identity is known.")
    add_figure(doc, ORIGINAL_RESULTS / "fig02_source_example_audit.png",
        "Figure 2. Source-example audit. The even-power scalar channel diverges from a negative initial condition at its analytical finite-escape time and produces a positive candidate derivative; an odd dissipative replacement restores the expected qualitative behavior.",
        "Finite-escape trajectory and positive Lyapunov derivative for x dot equals minus x squared, compared with a stable odd-power alternative.")

    bm.section(doc, "4. Structure-preserving synthesis", 1)
    bm.section(doc, "4.1 Positive neural candidate", 2)
    bm.add_body(doc, "Let ϕθ:ℝⁿ→ℝʳ be a differentiable feature network. The candidate is")
    bm.add_native_equation(doc, "Vθ(x)=ε‖x‖₂²+‖ϕθ(x)-ϕθ(0)‖₂²,     ε>0.", 6)
    bm.add_body(doc,
        "The construction is a smooth vector-feature specialization of Lyapunov-Net [14]. It ensures Vθ(0)=0 and Vθ(x)≥ε||x||² independently of training. The present network has a 2-24-8 tanh feature map and 272 trainable parameters. It is not claimed as a novel universal architecture; its role is to remove origin and positivity failure modes before derivative learning begins.")

    bm.section(doc, "4.2 Normalized Lyapunov transport objective", 2)
    bm.add_body(doc,
        "With q(x)=||x||², define the Lyapunov transport residual rθ=∇Vθᵀfκ+q and the prescribed-decay margin mθ=∇Vθᵀfκ+c||x||². The phrase “Zubov-type” used in the earlier version is removed: without a bounded Zubov transform and its boundary equation, the trained relation is a normalized Lyapunov transport/PDE equation, not Zubov's PDE [9,22,23].")
    bm.add_native_equation(doc, "rθ(x)=∇Vθ(x)ᵀfκ(x)+‖x‖²,     mθ(x)=∇Vθ(x)ᵀfκ(x)+c‖x‖².", 7)
    bm.add_native_equation(doc, "L(θ)=E[(rθ/(‖x‖²+η))²]+λhE[([mθ]₊/(‖x‖²+η))²]+λaLa.", 8)
    bm.add_body(doc,
        "The reference values are ε=0.02, c=0.15, η=0.05, and λh=8. Uniform states, near-origin Gaussian states, and recycled hard states are mixed. Every 200 steps, 12,000 fresh states are scored and the 192 largest margins are recycled. The principal method fixes λa=0: it receives no exact V* values.")

    bm.section(doc, "4.3 Anchor specification and removal", 2)
    bm.add_body(doc,
        "For the ablation only, the privileged anchor term uses four coordinates (1.5,1), (-1.5,-1), (1,-1.5), and (-1,1.5), with targets V*(x)=xᵀPx and λa=0.05. These anchors are deterministic analytical supervision and are therefore excluded from the principal ten-seed result, the selected formal model, and the additional benchmarks. Comparing the anchor and no-anchor rows tests whether the method depends on this privilege.")

    bm.section(doc, "4.4 Independent selection and test protocol", 2)
    bm.add_body(doc,
        "Ten seeds, 20260826-20260835, are trained for 2,200 iterations. Model selection uses a fixed 50,000-state validation set generated with seed 314159. Only after selecting seed 20260834 is the untouched final set generated: a 181×181 grid plus 200,000 uniform states using seed 271828. The origin is evaluated exactly but excluded from strict off-origin ratios when ||x||²≤10⁻⁸. An inequality is counted as violated only above +10⁻¹⁰; positivity is counted as violated below -10⁻¹⁰. This prevents the mathematical equality at x=0 and floating-point noise from being mislabeled as failure.")
    bm.add_native_equation(doc, "pU=1-(1-γ)^(1/N),     γ=0.95,     N=200000,     k=0.", 9)
    bm.add_body(doc,
        "Equation (9) is the exact one-sided Clopper-Pearson upper bound when zero failures are observed. It is a statement about IID sampling from the uniform test distribution, not a continuum certificate.")

    bm.section(doc, "4.5 Guarded interval/Jacobian verifier", 2)
    bm.add_body(doc,
        "For tanh features, the mean-value representation ϕ(x)-ϕ(0)=B(x)x uses B(x)=∫₀¹Jϕ(tx)dt. Hence ∇Vθ(x)=G(x)x with G(x)=2εI+2Jϕ(x)ᵀB(x). The benchmark field can be written f(x)=F(x)x. Interval bounds on tanh derivatives enclose Jϕ and B; interval matrix products then enclose GᵀF. A box is accepted when a Gershgorin upper bound on the largest eigenvalue of sym(GᵀF)+cI is negative, or when a direct natural interval extension of mθ is negative.")
    bm.add_native_equation(doc, "ϕθ(x)-ϕθ(0)=Bθ(x)x,     Bθ(x)=∫₀¹Jϕθ(τx)dτ.", 10)
    bm.add_native_equation(doc, "∇Vθ(x)=Gθ(x)x,     Gθ(x)=2εI+2Jϕθ(x)ᵀBθ(x).", 11)
    bm.add_native_equation(doc, "supx∈Q λmax(sym(Gθ(x)ᵀF(x))+cI)<0  ⇒  mθ(x)<0 on Q∖{0}.", 12)
    bm.add_body(doc,
        "The origin-containing square [-0.2,0.2]² is discharged by Eq. (12), avoiding the zero-margin singularity at x=0. Outside it, adaptive bisection continues to minimum width 2⁻¹². Each interval primitive is expanded by 10⁻¹²(1+maximum magnitude); acceptance requires an upper bound below -10⁻¹⁰. The exact network weights, dynamics, partition, radius scan, metrics, and log are exported. This is a transparent low-dimensional validated interval implementation, not a replacement for general α,β-CROWN, SMT, or proof-assistant infrastructure.")

    bm.section(doc, "5. Theoretical results", 1)
    bm.section(doc, "Theorem 1 — Architectural positivity", 2)
    bm.add_callout(doc, "Theorem 1.",
        "For every ε>0 and every differentiable ϕθ, Eq. (6) satisfies Vθ(0)=0 and Vθ(x)≥ε||x||² for all x. Thus Vθ is positive definite and radially unbounded.")
    bm.add_body(doc, "Proof. Both terms vanish at the origin. Away from it, the first term is strictly positive and the feature norm is nonnegative. The quadratic lower bound diverges with ||x||. □")

    bm.section(doc, "Theorem 2 — Interval-verified exponential stability", 2)
    bm.add_callout(doc, "Theorem 2.",
        "For the exported seed-20260834 network and benchmark dynamics, dot(Vθ)(x)≤-0.15||x||² for every x∈[-2,2]². Moreover, Vθ(x)≤b||x||² with b=3.7699728 on that square.")
    bm.add_body(doc,
        "Proof. The local matrix enclosure gives λmax≤-0.0902273 for sym(GᵀF)+0.15I on [-0.2,0.2]². Adaptive direct interval evaluation accepts the remaining 3,251 terminal boxes. Across 6,541 explored boxes, none remains unresolved; the closest accepted direct upper bound is -5.996×10⁻⁵. The feature-Jacobian spectral enclosure gives ||Bθ||≤sqrt(b-ε), hence Eq. (6) gives the stated upper bound. □")

    bm.section(doc, "Corollary 1 — Certified ROA and convergence rate", 2)
    bm.add_callout(doc, "Corollary 1.",
        "The sublevel Ωρ with ρ=0.04 is contained in (-2,2)² and is forward invariant. Every trajectory starting in Ωρ satisfies the exponential estimate in Eq. (13).")
    bm.add_native_equation(doc, "‖x(t)‖≤√(b/ε) exp[-ct/(2b)]‖x(0)‖=13.7295e^(-0.019894t)‖x(0)‖.", 13)
    bm.add_body(doc,
        "Proof. On the square boundary, ||x||²≥4 and therefore Vθ≥0.02·4=0.08>ρ, proving Ωρ⊂int(D). Theorem 2 gives dot(V)≤-(c/b)V. Integration and the lower/upper quadratic bounds yield Eq. (13). □")

    bm.section(doc, "Proposition 1 — Certified structured robustness", 2)
    bm.add_callout(doc, "Proposition 1.",
        "Let the true dynamics be ftrue(x)=f(x)+δBx with B=[[0.20,0.15],[-0.10,0.25]]. On D, the exported interval bound ||∇Vθ(x)||≤g||x|| has g=4.6406655. The nominal decrease remains strict for |δ|<0.1104129.")
    bm.add_native_equation(doc, "V̇true≤-[c-|δ|g‖B‖₂]‖x‖²,     |δ|<c/(g‖B‖₂)=0.1104129.", 14)
    bm.add_body(doc, "The result follows from Cauchy-Schwarz and ||B||₂=0.2927461. The bound is sufficient and conservative; it is reported separately from any larger empirical tolerance.")

    bm.section(doc, "Proposition 2 — Learned-certificate compositional small gain", 2)
    bm.add_callout(doc, "Proposition 2.",
        "Consider two identical verified subsystems with local certificates Vθ(zi) and diffusive coupling κ(zj-zi). If ||∇Vθ(zi)||≤g||zi|| and dot(Vθ)(zi)≤-c||zi||², then VΣ=Vθ(z1)+Vθ(z2) decreases whenever κ<c/(2g).")
    bm.add_native_equation(doc, "V̇Σ≤-[c-2κg](‖z₁‖²+‖z₂‖²).", 15)
    bm.add_body(doc,
        "Proof. Bound each coupling term by κg||zi||||zj-zi|| and use 2||z1||||z2||≤||z1||²+||z2||². With g=4.6406655, κmax=0.0161615. Selecting the certified design point κ=0.01 retains decay coefficient 0.0571867. Larger rings require an explicit graph/ISS gain operator as in [4,5,18]; the earlier sampled κ=0.08 result is not promoted to a learned formal guarantee.")

    bm.section(doc, "6. Reproducible numerical study", 1)
    bm.section(doc, "6.1 Principal auditable benchmark", 2)
    bm.add_body(doc, "The nonlinear benchmark is designed to have curved trajectories and an exact certificate:")
    bm.add_native_equation(doc, "f(x)=Ax+0.6x₁JPx,     A=[-1  4; -0.5  -1],     J=[0  -1; 1  0].", 16)
    bm.add_native_equation(doc, "P=[17/48  7/24; 7/24  5/3],     AᵀP+PA=-I,     P≻0.", 17)
    bm.add_native_equation(doc, "V*(x)=xᵀPx,     V̇*(x)=-‖x‖².", 18)
    bm.add_body(doc,
        "The nonlinear term is P-energy preserving because yᵀJy=0. The exact quadratic is simultaneously a classical Lyapunov, degree-two SOS, and rational-with-unit-denominator reference; it supplies a best-case analytical comparator without being used as principal training supervision.")

    bm.section(doc, "6.2 Additional nonlinear benchmarks", 2)
    bm.add_body(doc, "A torque-saturated inverted pendulum uses a smooth bounded controller")
    bm.add_native_equation(doc, "θ̇=ω,     ω̇=sinθ+umax tanh[(-k₁θ-k₂ω)/umax].", 19)
    bm.add_body(doc,
        "This case tests actuator saturation and robotic dynamics. A four-state pair of coupled nonlinear oscillators uses cubic stiffness and cross-coupling, has no analytical V-value supervision, and tests dimension beyond the formally verified network:")
    bm.add_native_equation(doc, "ẋ₁=x₂,  ẋ₂=-2x₁-1.2x₂-0.2x₁³+0.15x₃,  ẋ₃=x₄,  ẋ₄=-1.5x₃-x₄-0.15x₃³+0.15x₁.", 20)
    bm.add_body(doc,
        "Both additional systems are candidate-generation and sampled-validation studies only. Their role is to test training behavior under actuator nonlinearity and higher dimension, not to extend the interval theorem beyond the exported two-state benchmark.")

    bm.section(doc, "6.3 Training, baselines, and compute", 2)
    bm.add_table(doc,
        ["Setting", "Principal method", "Derivative-unconstrained baseline"],
        [
            ["Architecture", "2-24-8 tanh feature map in Eq. (6)", "2-32-32-1 tanh scalar network"],
            ["Objective", "normalized transport + decay hinge", "same derivative goals plus sampled positivity penalty"],
            ["Analytical anchors", "none", "none"],
            ["Iterations / batch", "2,200 / 1,024", "2,200 / 1,024"],
            ["Hard-state mining", "12,000 pool; 192 recycled every 200 steps", "same pool schedule"],
            ["Selection / final", "50,000 selection; 181²+200,000 untouched", "same final gate"],
            ["Software", "MATLAB R2024b, Deep Learning Toolbox, CPU", "same"],
            ["Hardware", "Intel i7-11800H; 8 physical / 16 logical cores", "same"],
        ], [2350, 3505, 3505], "Table 4. Reproducible training and comparator configuration.", 8.45)
    bm.add_body(doc,
        "The exact quadratic provides the classical reference. Published Lyapunov-Net, physics-informed/SMT, Yang branch-and-bound, NeurIPS two-stage, and CT-BaB results are compared methodologically in Table 2 rather than rerun under altered implementations. SOS and rational methods are represented by the exact degree-two solution on the principal system; no state-of-the-art superiority claim is made. Training uses single precision; interval verification uses exported double-precision parameters.")

    bm.section(doc, "7. Results", 1)
    bm.section(doc, "7.1 Ten-seed statistics and untouched final test", 2)
    bm.add_table(doc,
        ["Quantity", "Mean", "Std.", "Range / outcome"],
        [
            ["Training time (s)", f"{float(summary['MeanTrainingTime_s']):.3f}", f"{float(summary['StdTrainingTime_s']):.3f}", "37.35-47.28 s"],
            ["Transport/PDE RMSE", f"{float(summary['MeanPDERMSE']):.6f}", f"{float(summary['StdPDERMSE']):.6f}", "0.11479-0.12653"],
            ["Worst normalized decay margin", f"{float(summary['MeanMaxMarginRatio']):.6f}", f"{float(summary['StdMaxMarginRatio']):.6f}", "-0.71085 to -0.69732"],
            ["Sampled gate success", "10/10", "—", "all independent seeds"],
            ["Selected seed", summary["ValidationSelectedSeed"], "—", "chosen only on 50,000-state validation set"],
            ["Untouched Monte Carlo", mc["ObservedFailures"] + "/" + mc["IIDMonteCarloTrials"], "—", f"95% upper p={float(mc['ClopperPearsonUpper']):.3e}"],
        ], [2650, 1500, 1400, 3810], "Table 5. Multi-seed and untouched-test statistics.", 8.5)
    bm.add_body(doc,
        "Seed variation is small relative to the negative decay margin, and all runs pass the finite-set gate. Nevertheless, the exact binomial result quantifies only the probability mass of violations under uniform IID sampling. Continuum validity is supplied independently by Section 7.2.")
    add_figure(doc, RESULTS / "fig08_multiseed_statistics.png",
        "Figure 3. Ten independent no-anchor runs. Transport residual, untouched-test normalized decay margin, and wall-clock training time are reported per seed; all ten sampled certificate gates pass.",
        "Three bar charts showing transport residual, negative normalized decay margin, and training time for ten independent seeds.")

    bm.section(doc, "7.2 Interval certificate, ROA, and exported proof artifacts", 2)
    bm.add_table(doc,
        ["Verified quantity", "Value", "Interpretation"],
        [
            ["Domain", "[-2,2]²", "continuum claim for exported seed-20260834 network"],
            ["Local matrix square", "[-0.2,0.2]²", "origin handled analytically; λ upper=-0.0902273"],
            ["BaB boxes", "6,541 explored", "20 local; 3,251 direct; 0 unresolved"],
            ["Closest direct upper bound", "-5.9957×10⁻⁵", "strictly below -10⁻¹⁰ acceptance threshold"],
            ["Global gradient gain", "g≤4.6406655", "used for robustness and interconnection bounds"],
            ["Global value upper coefficient", "b≤3.7699728", "combined with ε=0.02"],
            ["Certified ROA", "ρ=0.04", "boundary lower bound 0.08 proves containment"],
            ["Verifier time", f"{formal['VerificationTimeSeconds']:.3f} s", "MATLAB CPU; excludes training and plotting"],
        ], [2800, 1900, 4660], "Table 6. Machine-checkable interval-verification result.", 8.5)
    add_figure(doc, RESULTS / "fig11_interval_verification.png",
        "Figure 4. Interval proof partition. The local origin square is discharged by a matrix inequality; every outer terminal box has a negative direct interval upper bound. Color in the right panel denotes branch depth; no unresolved box remains.",
        "Certified square partition with a local orange matrix-bound region and blue direct interval boxes, plus negative accepted upper bounds by branch depth.")
    add_figure(doc, RESULTS / "fig12_certified_candidate_fields.png",
        "Figure 5. Selected no-anchor certificate. The black contour is the certified ρ=0.04 sublevel; the center panel visualizes sampled decay margins while the interval proof covers the full square; exact and learned level sets show similar non-normal geometry without value supervision.",
        "Learned Lyapunov surface with certified sublevel set, sampled negative decay-margin heatmap, and exact versus learned contour comparison.")

    bm.section(doc, "7.3 Cumulative ablation and sensitivity", 2)
    chosen_ablation = {r["Variant"]: r for r in ablation}
    bm.add_table(doc,
        ["Cumulative variant", "PDE RMSE", "Worst margin ratio", "Observed gate"],
        [
            ["Positive value regression", f"{float(chosen_ablation['Positive value regression']['PDERMSE']):.4f}", f"{float(chosen_ablation['Positive value regression']['MaxMarginRatio']):.4f}", "pass on easy benchmark"],
            ["+ transport residual", f"{float(chosen_ablation['+ transport residual']['PDERMSE']):.4f}", f"{float(chosen_ablation['+ transport residual']['MaxMarginRatio']):.4f}", "largest residual improvement"],
            ["+ decay hinge", f"{float(chosen_ablation['+ decay hinge']['PDERMSE']):.4f}", f"{float(chosen_ablation['+ decay hinge']['MaxMarginRatio']):.4f}", "strongest sampled margin"],
            ["+ near-origin sampling", f"{float(chosen_ablation['+ near-origin sampling']['PDERMSE']):.4f}", f"{float(chosen_ablation['+ near-origin sampling']['MaxMarginRatio']):.4f}", "minor additional gain"],
            ["+ normalization", f"{float(chosen_ablation['+ normalization']['PDERMSE']):.4f}", f"{float(chosen_ablation['+ normalization']['MaxMarginRatio']):.4f}", "changes objective weighting"],
            ["+ privileged anchors", f"{float(chosen_ablation['+ privileged anchors']['PDERMSE']):.4f}", f"{float(chosen_ablation['+ privileged anchors']['MaxMarginRatio']):.4f}", "not required for gate"],
            ["+ hard-state recycling", f"{float(chosen_ablation['+ hard-state recycling']['PDERMSE']):.4f}", f"{float(chosen_ablation['+ hard-state recycling']['MaxMarginRatio']):.4f}", "not uniquely causal here"],
            ["Full without anchors", f"{float(chosen_ablation['Full without anchors']['PDERMSE']):.4f}", f"{float(chosen_ablation['Full without anchors']['MaxMarginRatio']):.4f}", "principal specification"],
        ], [3000, 1650, 1800, 2910], "Table 7. Cumulative ablation at a fixed 1,600-iteration budget.", 8.35)
    bm.add_body(doc,
        "All ablation variants happen to pass on the analytically benign principal benchmark, so the experiment does not support a claim that every component is necessary. The transport residual supplies the clearest improvement over value regression; anchors and hard-state recycling are not uniquely causal on this system. Across 17 one-factor sensitivity settings, every sampled gate passes. The worst margin ratios range from -0.5493 (two hidden layers) to -0.7343 (c=0.10), while PDE RMSE ranges from 0.1273 (width 32) to 0.2666 (depth two). This exposes a trade-off between transport fit and the prescribed gate rather than a brittle single optimum.")
    add_figure(doc, RESULTS / "fig09_ablation_sensitivity.png",
        "Figure 6. Cumulative ablation and one-factor sensitivity. Bars report normalized decay margins (negative is feasible), while lines or companion bars report transport fit. The anchor-free reference remains feasible throughout the tested neighborhood.",
        "Ablation chart for training components and horizontal sensitivity charts for decay margin and transport residual across 17 configurations.")

    bm.section(doc, "7.4 Baseline comparison", 2)
    baseline_deriv_pct = 100 * float(unconstrained["DerivativeViolationRate"])
    baseline_margin_pct = 100 * float(unconstrained["MarginViolationRate"])
    bm.add_table(doc,
        ["Method", "Positivity", "Derivative / margin failures", "Worst normalized margin", "Proof status"],
        [
            ["Exact quadratic / degree-2 SOS", "analytic", "0 / 0", "-0.8500", "global analytic identity"],
            ["Derivative-trained unconstrained DNN", "0 sampled", f"{baseline_deriv_pct:.6f}% / {baseline_margin_pct:.6f}%", f"{float(unconstrained['MaximumMarginRatio']):.4f}", "fails untouched gate"],
            ["Structure-preserving no-anchor DNN", "architectural", "0 / 0 sampled", f"{float(benchmarks[0]['MaxMarginRatio']):.4f}", "interval-verified on [-2,2]²"],
        ], [2250, 1650, 2300, 1700, 1460], "Table 8. Numerical baselines on the principal benchmark.", 8.25)
    bm.add_body(doc,
        "The unconstrained derivative-trained scalar network nearly succeeds, which is more informative than comparing only against value MSE: its V(0)=1.91×10⁻⁶ and sampled minimum is positive, yet two derivative failures and three c-margin failures remain among 232,761 final states, with a worst normalized margin of 1.8111. The structural floor removes positivity as an optimization burden and the interval stage closes the residual continuum question. The exact quadratic remains better on this deliberately auditable system; the neural result demonstrates verification of a learned representation, not superiority over a known analytical certificate.")

    bm.section(doc, "7.5 Extended benchmark suite", 2)
    bm.add_table(doc,
        ["Benchmark", "n", "PDE RMSE", "Worst margin ratio", "Empirical outcome"],
        [[r["Benchmark"], r["Dimension"], f"{float(r['PDERMSE']):.4f}", f"{float(r['MaxMarginRatio']):.4f}",
          f"margin {100*float(r['MarginViolationRate']):.3f}%; trajectory {100*float(r['TrajectoryViolationRate']):.3f}%"] for r in benchmarks],
        [2900, 650, 1500, 1750, 2560], "Table 9. Independent sampled results for the benchmark suite.", 8.35)
    bm.add_body(doc,
        "The saturated pendulum and four-state oscillator both show zero sampled margin and trajectory violations; maximum terminal norms are 1.00×10⁻⁶ and 2.52×10⁻³, respectively. These results answer the narrow generalization question—whether the training code survives actuator saturation and higher dimension—without implying a formal guarantee. Extending the interval proof to these systems is a defined next step.")
    add_figure(doc, RESULTS / "fig10_extended_benchmarks.png",
        "Figure 7. Extended nonlinear benchmarks. The sampled certificate gate is negative for all three systems; transport residuals and representative saturated-pendulum and four-state trajectories are shown. Only the first system is interval verified.",
        "Benchmark comparison bars, phase trajectories of a torque-saturated pendulum, and state norm decay for four-state nonlinear oscillators.")

    bm.section(doc, "7.6 Certified robustness and compositional quantities", 2)
    bm.add_table(doc,
        ["Quantity", "Certified value", "Scope"],
        [
            ["Gradient gain", "g≤4.6406655", "selected network on [-2,2]²"],
            ["Perturbation matrix norm", "||B||₂=0.2927461", "specified structured model-error direction"],
            ["Robust uncertainty radius", "|δ|<0.1104129", "sufficient, not necessary"],
            ["Two-subsystem coupling", "κ<0.0161615", "learned VΣ small-gain condition"],
            ["Certified design coupling", "κ=0.01", "retained decay coefficient 0.0571867"],
        ], [2900, 2000, 4460], "Table 10. Certified robustness and learned compositional bounds.", 8.5)
    bm.add_body(doc,
        "The earlier empirical robustness sweep remained feasible to a much larger perturbation, but it is no longer presented as a certificate. Likewise, the exact quadratic ring identity can tolerate κ=0.08 because its coupling energy cancels favorably; the learned certificate receives only the conservative small-gain value proved from g. This separation prevents analytical structure of V* from being silently transferred to Vθ.")

    bm.section(doc, "8. Implications for intelligent control", 1)
    bm.section(doc, "8.1 Neural policy with a CLF-QP filter", 2)
    bm.add_body(doc,
        "For control-affine dynamics, a learned policy uNN may propose performance actions while a certificate-aware quadratic program filters them:")
    bm.add_native_equation(doc, "u*=argminu ‖u-uNN(x)‖²  s.t.  ∇Vθᵀ(f+gu)≤-c‖x‖²+s,     s≥0.", 21)
    bm.add_body(doc,
        "Actuator bounds and barrier constraints can be added [17,29]. A formal offline Vθ does not automatically certify an arbitrary online policy: the encoded plant, controller, estimator, discretization, and actuator model must match the proof or be covered by Proposition 1.")

    bm.section(doc, "8.2 Adaptive and model-learning control", 2)
    bm.add_body(doc,
        "In adaptive neural control, approximation residuals should enter a Lyapunov inequality as a quantified disturbance rather than an uncalibrated confidence score. Proposition 1 converts a certified model-error envelope into a permissible δ. If online identification reports a larger envelope, a supervisory controller should shrink the operating set or switch to a known recovery policy. This connects DNN accuracy to the exact robust margin used in stability theory.")

    bm.section(doc, "8.3 Output feedback and digital twins", 2)
    bm.add_body(doc,
        "Evaluating Vθ at an estimated state introduces observer error. Joint controller-observer verification, as in [20], is the principled solution; a conservative alternative reserves part of the decrease margin for Lipschitz propagation of estimation and sampling errors. In a digital twin, disagreement between the predicted transport residual and measured energy change can be used as a stability-relevant anomaly signal, provided numerical differentiation noise is bounded.")

    bm.section(doc, "8.4 Networked systems", 2)
    bm.add_body(doc,
        "Large MIMO systems should be decomposed when repeated physics permits local ISS gains. Proposition 2 is intentionally narrower than the compositional neural-certificate framework of [18]: it proves a two-subsystem diffusive result from the exported local g and c. General graphs require an ISS gain matrix or dissipativity inequality whose spectral/small-gain condition is itself verified. Weight sharing reduces parameters, but it does not by itself prove stability.")

    bm.section(doc, "9. Threats to validity and open work", 1)
    limitations = bm.create_numbering(doc, bullet=True)
    for item in [
        "The interval proof is specific to the two-dimensional tanh benchmark and a documented 10⁻¹² outward guard. A production artifact should be independently cross-checked with α,β-CROWN, dReal/SMT, INTLAB-style directed rounding, or a proof assistant.",
        "The exact quadratic makes the principal system intentionally auditable and favors classical methods. The neural model is not claimed to outperform SOS, rational, Lyapunov-Net, Yang, NeurIPS two-stage, or CT-BaB implementations.",
        "The pendulum and four-state oscillator results are empirical. Higher-dimensional formal scaling, heterogeneous subsystems, delays, hybrid modes, and sampled-data implementation remain unresolved.",
        "The Monte Carlo confidence bound assumes IID uniform draws and does not transfer to another operational distribution. Formal verification, not the binomial bound, supports the continuum claim.",
        "The robustness radius covers only Δ(x)=δBx. Data-driven model error needs a certified state-dependent envelope; sensor, actuator, and observer errors must be included explicitly.",
        "All training is CPU single precision and all simulations are software-in-the-loop. Hardware, timing jitter, quantization, and solver tolerances can invalidate a continuous-time result if omitted.",
        "A complete local reproducibility archive is generated, but no DOI or external immutable public release is fabricated here. Public archival and independent reproduction remain pre-publication actions.",
    ]:
        bm.add_list_item(doc, item, limitations)

    bm.section(doc, "10. Conclusions", 1)
    bm.add_body(doc,
        "The revision changes the status of the central result. The main no-anchor network is no longer only a candidate with zero observed violations: a conservative interval/Jacobian branch-and-bound calculation verifies its prescribed derivative inequality on the full square [-2,2]², and a local matrix enclosure handles the origin exactly. The verified gradient and value bounds produce a concrete invariant sublevel, exponential estimate, structured robustness radius, and learned-certificate small-gain condition.")
    bm.add_body(doc,
        "Equally important, the negative results remain visible. The source even-power example is unstable; analytical anchors are unnecessary on the principal benchmark; hard-state recycling is not uniquely causal in the ablation; the exact quadratic outperforms the neural representation when it is known; and additional systems have only empirical support. This claim discipline is the main lesson for intelligent control: neural flexibility becomes scientifically useful when architectural invariants, derivative-aware learning, independent statistics, quantitative uncertainty, and machine-checkable continuum verification are treated as one pipeline.")

    bm.section(doc, "Declarations", 1)
    bm.add_body(doc, "Competing interests. The author declares no competing interests.")
    bm.add_body(doc, "Funding. No external funding is reported for this synthesized study.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.add_run("Data and code availability. The revised MATLAB training study is article_revision/revision_training_study.m and the interval verifier is article_revision/revision_formal_verifier.m. Exact network and dynamics arrays, MAT checkpoints, CSV tables, the complete accepted partition, verification logs, and vector/raster figures are stored in article_revision/revision_results. These files form a local reproducibility package. A public immutable DOI has not yet been assigned and must be created by the author before external submission.")
    bm.add_body(doc, "Author contributions. C.U.: conceptualization, methodology, software, validation, formal analysis, visualization, and manuscript preparation.")
    bm.add_body(doc,
        "AI-assisted drafting disclosure. Generative AI assistance supported literature organization, reproducible document-generation code, and language editing. The mathematical derivations, simulations, interval outputs, and scientific claims were checked against the exported equations, weights, logs, and deterministic MATLAB results; publication responsibility remains with the author.")

    bm.section(doc, "Appendix A. Verification derivations", 1)
    bm.section(doc, "A.1 Local matrix enclosure", 2)
    bm.add_body(doc,
        "For each interval box, tanh derivative bounds satisfy 0≤sech²(z)≤1. Interval outer products of the layer weights and these derivative intervals enclose Jϕ. The integral mean-value matrix B lies in the same enclosure along any segment contained in the box family. Interval products then enclose G and F. Gershgorin's theorem upper-bounds λmax of the symmetric 2×2 interval matrix. The radius scan is negative through R=0.2 and becomes positive at R=0.3, motivating the local/outer hybrid partition.")
    bm.section(doc, "A.2 ROA containment", 2)
    bm.add_body(doc,
        "Every point outside D=[-2,2]² has at least one coordinate of magnitude greater than two, so ||x||²>4. The global architectural floor then yields Vθ>0.08 outside D. Choosing ρ=0.04 therefore proves Ωρ⊂int(D) directly; Theorem 2 supplies strict decrease away from the origin and forward invariance.")
    bm.section(doc, "A.3 Reproducibility checklist", 2)
    checklist = bm.create_numbering(doc, bullet=True)
    for item in [
        "MATLAB R2024b; Deep Learning Toolbox; CPU execution; single precision for training and double precision for exported verification.",
        "Principal seeds 20260826-20260835; selection seed 314159; untouched final-test seed 271828.",
        "Run revision_training_study, then revision_formal_verifier from a MATLAB-supported path.",
        "Confirm formal_verification_metrics.csv reports 6,541 explored boxes and zero unresolved boxes.",
        "Confirm certified_network_and_dynamics.mat and the W1, b1, W2, b2, A, P, J CSV files match the manuscript archive.",
        "Regenerate Figures 3-7 and compare all CSV tables before submission; archive the package with an immutable public identifier.",
    ]:
        bm.add_list_item(doc, item, checklist)

    bm.section(doc, "Appendix B. Sensitivity data", 1)
    sens_selected = [
        "reference", "epsilon=0.01", "epsilon=0.04", "c=0.10", "c=0.20",
        "hinge=4", "hinge=12", "offset=0.02", "offset=0.10", "anchors=0.05",
        "hard=96", "hard=384", "recycle=100", "recycle=400", "width=16", "width=32", "depth=2",
    ]
    smap = {r["Configuration"]: r for r in sensitivity}
    bm.add_table(doc,
        ["Configuration", "PDE RMSE", "Worst margin ratio", "Gate"],
        [[key, f"{float(smap[key]['PDERMSE']):.4f}", f"{float(smap[key]['MaxMarginRatio']):.4f}",
          "pass" if float(smap[key]["MarginViolationRate"]) == 0 else "fail"] for key in sens_selected],
        [2900, 1800, 2200, 2460], "Table B1. Complete one-factor sensitivity results (1,000 iterations each).", 8.2)

    bm.section(doc, "References", 1)
    references = [
        ("[1] Lyapunov, A.M. (1992). The General Problem of the Stability of Motion. Taylor & Francis.", "https://doi.org/10.1080/00411457108231482"),
        ("[2] Khalil, H.K. (2002). Nonlinear Systems, 3rd ed. Prentice Hall.", "https://www.pearson.com/en-us/subject-catalog/p/nonlinear-systems/P200000003223"),
        ("[3] Haddad, W.M., and Chellaboina, V. (2008). Nonlinear Dynamical Systems and Control. Princeton University Press.", "https://doi.org/10.1515/9781400832243"),
        ("[4] Jiang, Z.-P., Teel, A.R., and Praly, L. (1994). Small-gain theorem for ISS systems and applications. Mathematics of Control, Signals and Systems, 7, 95-120.", "https://doi.org/10.1007/BF01211469"),
        ("[5] Dashkovskiy, S.N., Rüffer, B.S., and Wirth, F.R. (2007). An ISS small gain theorem for general networks. Mathematics of Control, Signals, and Systems, 19, 93-122.", "https://doi.org/10.1007/s00498-007-0014-8"),
        ("[6] Parrilo, P.A. (2000). Structured Semidefinite Programs and Semialgebraic Geometry Methods in Robustness and Optimization. PhD thesis, Caltech.", "https://thesis.library.caltech.edu/1647/"),
        ("[7] Prajna, S., Papachristodoulou, A., and Parrilo, P.A. (2004). SOSTOOLS: Sum of squares optimization toolbox for MATLAB. CDC.", "https://doi.org/10.1109/CDC.2002.1184414"),
        ("[8] Uyulan, C. (2023). Efficient Computation of Lyapunov Functions Using Deep Neural Networks for the Assessment of Stability in Controller Design. Research Square preprint.", "https://doi.org/10.21203/rs.3.rs-3698604/v1"),
        ("[9] Grüne, L. (2021). Computing Lyapunov functions using deep neural networks. Journal of Computational Dynamics, 8(2), 131-152.", "https://doi.org/10.3934/jcd.2021006"),
        ("[10] Grüne, L. (2021). Overcoming the curse of dimensionality for approximating Lyapunov functions with DNNs under a small-gain condition. IFAC-PapersOnLine, 54(9), 317-322.", "https://doi.org/10.1016/j.ifacol.2021.06.152"),
        ("[11] Richards, S.M., Berkenkamp, F., and Krause, A. (2018). The Lyapunov Neural Network: Adaptive stability certification for safe learning. PMLR 87, 466-476.", "https://proceedings.mlr.press/v87/richards18a.html"),
        ("[12] Chang, Y.-C., Roohi, N., and Gao, S. (2019). Neural Lyapunov control. NeurIPS 32.", "https://proceedings.neurips.cc/paper/2019/hash/2647c1dba23bc0e0f9cdf75339e120d2-Abstract.html"),
        ("[13] Abate, A., Ahmed, D., Giacobbe, M., and Peruffo, A. (2021). Formal synthesis of Lyapunov neural networks. IEEE Control Systems Letters, 5(3), 773-778.", "https://doi.org/10.1109/LCSYS.2020.3005328"),
        ("[14] Gaby, N., Zhang, F., and Ye, X. (2022). Lyapunov-Net: A Deep Neural Network Architecture for Lyapunov Function Approximation. IEEE CDC, 2091-2096.", "https://doi.org/10.1109/CDC51059.2022.9993006"),
        ("[15] Boffi, N., Tu, S., Matni, N., Slotine, J.-J., and Sindhwani, V. (2021). Learning stability certificates from data. PMLR 155, 1341-1350.", "https://proceedings.mlr.press/v155/boffi21a.html"),
        ("[16] Zhou, R., Quartz, T., De Sterck, H., and Liu, J. (2022). Neural Lyapunov control of unknown nonlinear systems with stability guarantees. NeurIPS 35.", "https://proceedings.neurips.cc/paper_files/paper/2022/hash/bba3160c42f4c1d23175b5abf04347f5-Abstract-Conference.html"),
        ("[17] Dawson, C., Gao, S., and Fan, C. (2023). Safe control with learned certificates: A survey. IEEE Transactions on Robotics, 39(3), 1749-1767.", "https://doi.org/10.1109/TRO.2022.3232542"),
        ("[18] Zhang, S., Xiu, Y., Qu, G., and Fan, C. (2023). Compositional neural certificates for networked dynamical systems. PMLR 211, 272-285.", "https://proceedings.mlr.press/v211/zhang23a.html"),
        ("[19] Wu, J., Clark, A., Kantaros, Y., and Vorobeychik, Y. (2023). Neural Lyapunov control for discrete-time systems. NeurIPS 36.", "https://papers.neurips.cc/paper_files/paper/2023/hash/08bf1773e94763b6cc366ee7c6582f27-Abstract-Conference.html"),
        ("[20] Yang, L., Dai, H., Shi, Z., Hsieh, C.-J., Tedrake, R., and Zhang, H. (2024). Lyapunov-stable neural control for state and output feedback. ICML, PMLR 235, 56033-56046.", "https://proceedings.mlr.press/v235/yang24f.html"),
        ("[21] Zhang, S., and Fan, C. (2024). Learning to stabilize high-dimensional unknown systems using Lyapunov-guided exploration. PMLR 242, 52-67.", "https://proceedings.mlr.press/v242/zhang24a.html"),
        ("[22] Liu, J., Meng, Y., Fitzsimmons, M., and Zhou, R. (2025). Physics-informed neural network Lyapunov functions: PDE characterization, learning, and verification. Automatica, 175, 112193.", "https://doi.org/10.1016/j.automatica.2025.112193"),
        ("[23] Li, H., Zhong, X., Hu, B., and Zhang, H. (2025). Two-Stage Learning of Stabilizing Neural Controllers via Zubov Sampling and Iterative Domain Expansion. NeurIPS 38.", "https://proceedings.neurips.cc/paper_files/paper/2025/hash/6b0affe7b3440f503acf499f9ac1d3cc-Abstract-Conference.html"),
        ("[24] Shi, Z., Li, H., Hsieh, C.-J., and Zhang, H. (2026). Certified Training with Branch-and-Bound for Lyapunov-stable Neural Control. L4DC, PMLR 331, 788-808.", "https://proceedings.mlr.press/v331/shi26a.html"),
        ("[25] Huh, S., Tonietti, G., and Bicchi, A. (2008). Neural network based robust adaptive control for a variable stiffness actuator. MED, 1028-1033.", "https://ieeexplore.ieee.org/document/4602116"),
        ("[26] Hornik, K., Stinchcombe, M., and White, H. (1989). Multilayer feedforward networks are universal approximators. Neural Networks, 2(5), 359-366.", "https://doi.org/10.1016/0893-6080(89)90020-8"),
        ("[27] Kingma, D.P., and Ba, J. (2015). Adam: A method for stochastic optimization. ICLR.", "https://arxiv.org/abs/1412.6980"),
        ("[28] Sontag, E.D. (1989). A universal construction of Artstein's theorem on nonlinear stabilization. Systems & Control Letters, 13(2), 117-123.", "https://doi.org/10.1016/0167-6911(89)90028-5"),
        ("[29] Ames, A.D., Xu, X., Grizzle, J.W., and Tabuada, P. (2017). Control barrier function based quadratic programs for safety critical systems. IEEE TAC, 62(8), 3861-3876.", "https://doi.org/10.1109/TAC.2016.2638961"),
        ("[30] Johansen, T.A. (2000). Computation of Lyapunov functions for smooth nonlinear systems using convex optimization. Automatica, 36(11), 1617-1626.", "https://doi.org/10.1016/S0005-1098(00)00088-1"),
    ]
    for text, url in references:
        ref_paragraph(doc, text, url)

    doc.core_properties.title = "Interval-Verified Structure-Preserving Neural Lyapunov Certificates for Intelligent Nonlinear Control"
    doc.core_properties.subject = "Peer-review revised article on neural Lyapunov stability, interval verification, robust and compositional intelligent control"
    doc.core_properties.author = "Çağlar Uyulan"
    doc.core_properties.keywords = "Lyapunov; neural certificates; intelligent control; interval verification; region of attraction; robustness; small gain"
    doc.core_properties.comments = "Peer-review revised manuscript with editable OMML equations and MATLAB-validated figures."
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    doc.settings.element.append(update)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
