"""Re-evaluate archived exports. No interval soundness or formal proof is claimed."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from models import (ROOT, load_main, load_nonpolynomial, main_dynamics,
                    nonpolynomial_dynamics, zero_failure_upper)


def sample_statistics(model, dynamics, x, exclusion, tolerance, batch=8192):
    failures = 0
    worst = -float('inf')
    for start in range(0, x.shape[1], batch):
        points = x[:, start:start+batch]
        value, grad = model.value_gradient(points)
        q = np.sum(points*points, axis=0)
        margin = np.sum(grad*dynamics(points), axis=0)+model.decay*q
        mask = q > exclusion
        failures += int(np.count_nonzero(mask & (margin > tolerance)))
        if np.any(mask):
            worst = max(worst, float(np.max(margin[mask]/q[mask])))
        if np.any(value+1e-12 < model.epsilon*q):
            raise AssertionError('Architectural floor violated numerically')
    return {'points': x.shape[1], 'events': failures,
            'origin_exclusion_norm_squared': exclusion,
            'margin_tolerance': tolerance, 'worst_margin_ratio': worst}


def check_partition():
    """Check the archived binary tree geometry, not its arithmetic soundness."""
    p = np.genfromtxt(ROOT/'results/revision/formal_verified_partition.csv',
                      delimiter=',', names=True)
    lo = np.stack([p['LowerX1'], p['LowerX2']], axis=1)
    hi = np.stack([p['UpperX1'], p['UpperX2']], axis=1)
    if not np.all((hi > lo) & (lo >= -2) & (hi <= 2)):
        raise AssertionError('Invalid partition box')
    leaves = [(lo[i], hi[i]) for i in range(len(p))]

    def cover(lower, upper, subset):
        if len(subset) == 1:
            a, b = subset[0]
            if not (np.array_equal(a, lower) and np.array_equal(b, upper)):
                raise AssertionError('Partition contains a gap')
            return
        widths = upper-lower
        k = int(np.argmax(widths))
        mid = (lower[k]+upper[k])/2
        left = [box for box in subset if box[1][k] <= mid]
        right = [box for box in subset if box[0][k] >= mid]
        if len(left)+len(right) != len(subset) or not left or not right:
            raise AssertionError('Overlap or non-binary partition')
        u, l = upper.copy(), lower.copy()
        u[k], l[k] = mid, mid
        cover(lower, u, left)
        cover(l, upper, right)

    cover(np.array([-2., -2.]), np.array([2., 2.]), leaves)
    methods = p['MethodCode'].astype(int)
    if not np.all(np.isin(methods, [1, 2])):
        raise AssertionError('Unresolved leaf')
    central = methods == 1
    if not np.all((lo[central] >= -0.2) & (hi[central] <= 0.2)):
        raise AssertionError('Invalid local leaf')
    if not np.all(p['MarginUpper'][methods == 2] < 0):
        raise AssertionError('Nonnegative archived direct upper margin')
    return {'leaf_boxes': len(p), 'local_leaves': int(np.sum(central)),
            'direct_leaves': int(np.sum(methods == 2)),
            'geometry_covers_square': True, 'validated_outward_rounding': False}


def check_provenance():
    d = json.loads((ROOT/'provenance/manifest.json').read_text(encoding='utf-8'))
    for f in d['copied_unchanged_files']:
        data = (ROOT/f['destination']).read_bytes()
        if hashlib.sha256(data).hexdigest() != f['sha256']:
            raise AssertionError(f"Changed supplied artifact: {f['destination']}")
    return {'unchanged_artifacts_checked': len(d['copied_unchanged_files'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'generated/python_audit.json')
    args = parser.parse_args()
    a = np.array([[-1., 4.], [-0.5, -1.]])
    p = np.array([[17/48, 7/24], [7/24, 5/3]])
    residual = float(np.linalg.norm(a.T@p+p@a+np.eye(2)))
    if residual > 1e-12:
        raise AssertionError('Quadratic identity failed')
    out = {'scope': 'Independent floating-point audit; not a formal machine certificate',
           'python': sys.version.split()[0], 'numpy': np.__version__,
           'quadratic_identity_residual': residual,
           'provenance': check_provenance(), 'partition': check_partition()}
    for name, model, dynamics, radius, count, exclusion, tol in [
        ('main', load_main(), main_dynamics, 2., 181, 1e-8, 1e-10),
        ('nonpolynomial', load_nonpolynomial(), nonpolynomial_dynamics, 1.9, 401, 1e-12, 0.)
    ]:
        axis = np.linspace(-radius, radius, count)
        xx, yy = np.meshgrid(axis, axis)
        grid = np.stack([xx.ravel(), yy.ravel()])
        # Independent NumPy stream; deliberately no equality claim with MATLAB RNG.
        random = np.random.default_rng(271828).uniform(-radius, radius, (2, 200000))
        grid_stats = sample_statistics(model, dynamics, grid, exclusion, tol)
        mc_stats = sample_statistics(model, dynamics, random, exclusion, tol)
        if mc_stats['events'] == 0:
            mc_stats['zero_event_one_sided_95_percent_upper'] = zero_failure_upper(random.shape[1])
        value0, gradient0 = model.value_gradient(np.zeros((2, 1)))
        out[name] = {'feature_output_activation': 'tanh' if model.output_tanh else 'identity',
                     'grid': grid_stats, 'iid_monte_carlo': mc_stats,
                     'value_at_origin': float(value0[0]),
                     'gradient_norm_at_origin': float(np.linalg.norm(gradient0))}
        if grid_stats['events'] or mc_stats['events']:
            raise AssertionError(f'Detected sampled margin failures for {name}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
