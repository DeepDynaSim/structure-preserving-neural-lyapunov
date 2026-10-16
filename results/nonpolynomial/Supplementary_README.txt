Supplementary material for "Structure-Preserving Neural Lyapunov Functions for Nonlinear Systems: Verification Conditions and Robust Stability Bounds"

Files:
1. Supplementary_Nonpolynomial_Network_Weights.csv
   Exact exported weights of the bias-free 2-8-4 tanh feature network used in the non-polynomial Lyapunov stress test.
2. Supplementary_Nonpolynomial_Network_Model.json
   Machine-readable model export and metadata for the same stress-test network.

Stress-test system:
  x1_dot = -x1 + x1*x2
  x2_dot = -x2
Domain used for finite testing: [-1.9, 1.9]^2
Structure-preserving floor: epsilon = 0.02
Prescribed decay coefficient: c = 0.03

Important scope statement:
These files reproduce the sampled stress-test network. They do not constitute a validated outward-rounded continuum certificate. Any formal continuum claim for a trained network must additionally include a sound interval/SMT/bound-propagation verifier artifact, including the complete partition/log and rounding model.
