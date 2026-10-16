# Reading and maintaining the formulas

The README and complete proofs use self-contained SVG equations. The Greek letters, matrix rows, fractions, norm bars, and subscripts are embedded as vector paths, so the pages do not need mathematical webfonts or a browser-side formula renderer. The white equation background preserves contrast in either GitHub theme. Images have text alternatives, and their full LaTeX source remains editable.

## Notation

| Name | Meaning in this repository |
|---|---|
| `x`, `z_1`, `z_2` | State vector and the two subsystem states |
| `V`, `V_theta` | Lyapunov candidate |
| `phi`, `phi_theta` | Feature network; the Greek letter phi |
| `epsilon` | Positive quadratic floor; the Greek letter epsilon |
| `grad V` or `nabla V` | Gradient of the candidate |
| `dot V` | Derivative along the system trajectories |
| `J_phi`, `J_f` | Jacobian matrices of the features and vector field |
| `norm(x)` | Euclidean vector norm; matrix norms are specified in the proof |
| `Omega_rho`, `S_rho` | Single-system and joint Lyapunov sublevels |
| `rho` | Sublevel value; the Greek letter rho |
| `delta`, `kappa` | Perturbation magnitude and coupling coefficient |
| `b`, `c`, `g` | Value upper coefficient, decay coefficient, gradient gain |
| `lambda_max` | Largest eigenvalue of a symmetric matrix |
| `R(Q)` | Smallest axis-aligned box containing the origin and box Q |
| `T1` through `T26` | Equation labels in the complete proofs |

## Editable sources

- [README source](sources/README.md.in)
- [Full proof source](sources/THEORY.md.in)
- [Equation manifest](assets/math/manifest.json), including every source expression and the SVG checksum

The `.md.in` files are plain-text templates, so GitHub displays their LaTeX literally for copying. Edit these templates rather than the generated `README.md` or `THEORY.md` pages.

From the repository root, using Node.js 20 or later and pnpm:

```sh
pnpm install --dir tools/math-renderer --frozen-lockfile
node scripts/render_math.mjs
node scripts/render_math.mjs --check
```

The renderer fails on invalid TeX, oversized display equations, missing generated files, or changed output. The generated SVG files contain embedded glyph paths and no scripts, external fonts, or external image services. They can be inspected directly at full resolution. Equation labels are outside the image so that references such as `(T21)` remain searchable.

This presentation repair preserves the mathematical assumptions and scientific scope. It addresses the observed rejected macros, Markdown backslash loss, and broken native mathematical layout. The original DOCX, source-code snapshots, network weights, numerical results, and their provenance hashes are unchanged.

The rendering tool uses MathJax 3.2.2 under the [Apache 2.0 license](../tools/math-renderer/MATHJAX-LICENSE.txt); its equation glyphs are distributed with that attribution. GitHub's own [mathematical-expression guide](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions) describes its native math support; the supplied SVGs also work where that renderer is unavailable.
