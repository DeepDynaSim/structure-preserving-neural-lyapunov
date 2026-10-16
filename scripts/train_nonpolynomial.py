"""Derivative-only reconstruction, not the missing historical training script.

Optional dependency: PyTorch. This creates a new candidate and records settings;
the supplied JSON remains the source of the manuscript's archived model.
"""
import argparse
import json
from pathlib import Path
import torch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iterations', type=int, default=5000)
    parser.add_argument('--batch-size', type=int, default=2048)
    parser.add_argument('--seed', type=int, default=20261016)
    parser.add_argument('--output', type=Path, default=Path('generated/nonpolynomial_retrained.json'))
    args = parser.parse_args()
    if args.iterations < 1 or args.batch_size < 1:
        parser.error('iterations and batch-size must be positive')
    torch.manual_seed(args.seed)
    torch.set_default_dtype(torch.float64)
    net = torch.nn.Sequential(torch.nn.Linear(2, 8, bias=False), torch.nn.Tanh(),
                              torch.nn.Linear(8, 4, bias=False), torch.nn.Tanh())
    optimizer = torch.optim.Adam(net.parameters(), lr=1e-3)
    eps, c, eta = 0.02, 0.03, 0.05
    for step in range(args.iterations):
        x = (3.8*torch.rand(args.batch_size, 2)-1.9).requires_grad_(True)
        q = (x*x).sum(1)
        phi = net(x)-net(torch.zeros(1, 2))
        value = eps*q+(phi*phi).sum(1)
        grad = torch.autograd.grad(value.sum(), x, create_graph=True)[0]
        field = torch.stack([-x[:, 0]+x[:, 0]*x[:, 1], -x[:, 1]], dim=1)
        dot = (grad*field).sum(1)
        margin = dot+c*q
        loss = (((dot+q)/(q+eta))**2).mean()+8*((torch.relu(margin)/(q+eta))**2).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if step == 0 or (step+1) % 500 == 0:
            print(f'{step+1}/{args.iterations}: loss={loss.item():.6g}')
    result = {'seed': args.seed, 'eps': eps, 'c': c, 'eta': eta,
              'weights': {'l1.weight': net[0].weight.detach().tolist(),
                          'l2.weight': net[2].weight.detach().tolist()},
              'provenance': 'New derivative-only reconstruction; not the historical manuscript checkpoint',
              'settings': {'iterations': args.iterations, 'batch_size': args.batch_size,
                           'optimizer': 'Adam', 'learning_rate': 1e-3,
                           'dtype': 'float64', 'pytorch': torch.__version__}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
