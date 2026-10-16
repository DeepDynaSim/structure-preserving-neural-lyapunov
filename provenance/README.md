# Provenance of the public snapshot

The reference file is `SAGE_PII_Structure_Preserving_Neural_Lyapunov_Functions_Caglar_Uyulan.docx`, supplied by the author. It is preserved unchanged. Its embedded images were extracted without resampling, and drawing descriptions are in `manuscript/figures/alt_text.json`.

All supplied MATLAB, Python, and PowerShell sources in `article_build/` and `article_revision/` are copied unchanged under `original_sources/`. The SHA-256 manifest records their source paths and the hashes of all copied original results, checkpoints, and supplementary network exports. It does not claim these historical programs all implement the final manuscript; consult the correspondence notes.

Active MATLAB copies in `matlab/` add portable path handling and write into `generated/`. The training copy also replaces the hard-coded zero Monte Carlo count with the selected model's actual IID event count and a conditional zero-event bound. The active verifier warns that its fixed guard is not validated outward rounding. Core original network training and guarded interval calculations are otherwise retained. `run_reproduction.m`, both non-polynomial training examples, independent NumPy evaluation, tests, and repository documentation were added during public-repository preparation.

No original program for the supplementary stress-test training or final SAGE document assembly was found in the supplied workspace. This absence is disclosed; no reconstructed file is labeled as recovered original source. Earlier builders may contain earlier claims and environment-specific paths and are historical records only. Their third-party bibliography entries are citations, not bundled reference works.

Third-party reference PDFs, peer-review reports, correspondence, temporary render directories, and unrelated manuscripts are not included in the public snapshot. No Git history from the source workspace existed. The first repository commit therefore records this prepared snapshot rather than an earlier development history.
