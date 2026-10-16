"""Independent double-precision evaluation of the supplied feature exports."""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Model:
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray
    epsilon: float
    decay: float
    output_tanh: bool

    def feature_jacobian(self, x):
        """x has shape (n, count); Jacobian has shape (r, n, count)."""
        x = np.asarray(x, dtype=np.float64)
        a = np.tanh(self.w1 @ x + self.b1[:, None])
        phi = self.w2 @ a + self.b2[:, None]
        jac = np.einsum('rh,hN,hi->riN', self.w2, 1-a*a, self.w1)
        if self.output_tanh:
            phi = np.tanh(phi)
            jac *= (1-phi*phi)[:, None, :]
        return phi, jac

    def value_gradient(self, x):
        x = np.asarray(x, dtype=np.float64)
        phi, jac = self.feature_jacobian(x)
        phi0, _ = self.feature_jacobian(np.zeros((x.shape[0], 1)))
        difference = phi-phi0
        value = self.epsilon*np.sum(x*x, axis=0)+np.sum(difference*difference, axis=0)
        grad = 2*self.epsilon*x+2*np.einsum('riN,rN->iN', jac, difference)
        return value, grad


def load_main(root=ROOT):
    p = Path(root)/'results/revision'
    def csv(name):
        return np.loadtxt(p/name, delimiter=',', ndmin=2)
    return Model(csv('network_W1.csv'), csv('network_b1.csv').ravel(),
                 csv('network_W2.csv'), csv('network_b2.csv').ravel(),
                 0.02, 0.15, False)


def load_nonpolynomial(root=ROOT):
    p = Path(root)/'results/nonpolynomial/Supplementary_Nonpolynomial_Network_Model.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    w1, w2 = np.array(d['weights']['l1.weight']), np.array(d['weights']['l2.weight'])
    return Model(w1, np.zeros(w1.shape[0]), w2, np.zeros(w2.shape[0]),
                 d['eps'], d['c'], True)


def main_dynamics(x):
    pth = ROOT/'results/revision'
    a = np.loadtxt(pth/'dynamics_A.csv', delimiter=',')
    p = np.loadtxt(pth/'dynamics_P.csv', delimiter=',')
    j = np.loadtxt(pth/'dynamics_J.csv', delimiter=',')
    return a@x+0.6*x[0]*(j@p@x)


def reference_dynamics(x):
    a = np.array([[-1., 4.], [-0.5, -1.]])
    p = np.array([[17/48, 7/24], [7/24, 5/3]])
    j = np.array([[0., -1.], [1., 0.]])
    return a@x+0.6*x[0]*(j@p@x)


def nonpolynomial_dynamics(x):
    return np.stack([-x[0]+x[0]*x[1], -x[1]])


def zero_failure_upper(n, confidence=0.95):
    if n <= 0 or not 0 < confidence < 1:
        raise ValueError('Require positive n and confidence in (0,1)')
    return float(-np.expm1(np.log1p(-confidence)/n))
