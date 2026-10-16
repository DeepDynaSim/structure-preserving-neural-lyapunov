"""Checks target independent identities and exported models, not formal enclosure."""
import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from models import load_main, load_nonpolynomial, reference_dynamics, zero_failure_upper
from audit_exports import check_partition, check_provenance


class ExportTests(unittest.TestCase):
    def test_gradient_against_finite_differences(self):
        x = np.array([[0.13, -0.4, 1.1], [-0.2, 0.7, -1.5]])
        for model in [load_main(), load_nonpolynomial()]:
            _, grad = model.value_gradient(x)
            for i in range(2):
                h = np.zeros_like(x)
                h[i] = 1e-6
                plus, _ = model.value_gradient(x+h)
                minus, _ = model.value_gradient(x-h)
                np.testing.assert_allclose(grad[i], (plus-minus)/2e-6, rtol=2e-6, atol=2e-8)

    def test_reference_orbital_identity(self):
        x = np.random.default_rng(4).normal(size=(2, 100))
        p = np.array([[17/48, 7/24], [7/24, 5/3]])
        dot = np.sum((2*p@x)*reference_dynamics(x), axis=0)
        np.testing.assert_allclose(dot, -np.sum(x*x, axis=0), rtol=1e-12, atol=1e-12)

    def test_logarithmic_square_completion(self):
        x, y = np.random.default_rng(8).normal(size=(2, 100))
        direct = 2*x*(-x+x*y)/(1+x*x)-2*y*y
        squares = -(x*x+2*y*y+x*x*y*y+(x-x*y)**2)/(1+x*x)
        np.testing.assert_allclose(direct, squares, atol=1e-12)
        self.assertTrue(np.all(squares < 0))

    def test_architectural_origin_and_floor(self):
        x = np.array([[0., 0.7, -2.], [0., -1.1, 2.]])
        for model in [load_main(), load_nonpolynomial()]:
            v, grad = model.value_gradient(x)
            # Different BLAS batch sizes can introduce cancellation at zero.
            self.assertLess(abs(v[0]), 1e-28)
            np.testing.assert_allclose(grad[:, 0], 0., atol=1e-14)
            self.assertTrue(np.all(v >= model.epsilon*np.sum(x*x, axis=0)))

    def test_nonpolynomial_architecture_matches_reported_grid_ratio(self):
        # The full-grid ratio diagnoses the exported output activation.
        model = load_nonpolynomial()
        self.assertTrue(model.output_tanh)
        axis = np.linspace(-1.9, 1.9, 401)
        from audit_exports import sample_statistics
        from models import nonpolynomial_dynamics
        xx, yy = np.meshgrid(axis, axis)
        st = sample_statistics(model, nonpolynomial_dynamics,
                               np.stack([xx.ravel(), yy.ravel()]), 1e-12, 0.)
        self.assertAlmostEqual(st['worst_margin_ratio'], -0.01982632904223272, places=10)

    def test_zero_event_bound_inverts_binomial_probability(self):
        upper = zero_failure_upper(200000)
        self.assertAlmostEqual((1-upper)**200000, 0.05, places=10)
        with self.assertRaises(ValueError):
            zero_failure_upper(0)

    def test_partition_geometry(self):
        stats = check_partition()
        self.assertEqual(stats['leaf_boxes'], 3271)
        self.assertFalse(stats['validated_outward_rounding'])

    def test_supplied_artifacts_unchanged(self):
        self.assertGreater(check_provenance()['unchanged_artifacts_checked'], 60)


if __name__ == '__main__':
    unittest.main()
