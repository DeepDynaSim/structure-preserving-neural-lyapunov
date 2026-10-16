# Repository preparation validation

Checked on 17 October 2026 with the bundled Python 3.12.14 / NumPy 2.3.5 runtime and MATLAB R2024b:

- Eight Python unit tests passed.
- Both supplied networks had zero detected events on their stated Cartesian grids and separate 200,000-point IID NumPy tests.
- The non-polynomial grid reproduced the reported worst normalized margin to the paper's displayed precision.
- All 66 hashed supplied artifacts matched their unchanged copies.
- The 3,271 archived partition leaves covered `[-2,2]^2` without overlap or gaps in the binary geometry audit.
- The MATLAB verifier rerun reproduced all non-timing values in the archived verification metrics exactly, including 6,541 explored nodes and zero unresolved boxes.
- MATLAB code analysis found no parse errors in the active `.m` files; the reconstructed non-polynomial trainer completed a two-iteration smoke run.

The full training campaign was not rerun during repository preparation. The optional PyTorch trainer was syntax checked but not executed because PyTorch was unavailable in the bundled environment. Neither the unit tests nor these floating-point reruns constitute validated outward-rounded verification. JSON and MATLAB logs in this directory record the executed checks.
