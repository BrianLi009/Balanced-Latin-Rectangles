#!/usr/bin/env python3
"""Collect solver runs into the published results.

Reads results/raw/r_{k}_{n}_s{seed}.txt (output of ./sa), re-verifies every run with
verify.imbalance, keeps the best rectangle per (k, n), and writes
  results/rectangles/k{k}_n{n}.txt   one file per cell (best rectangle found)
  results/results.csv                previous vs new imbalance for every cell
  results/budget.csv                 best value per cell for each time budget
Seeds map to budgets via BUDGET below.
"""
import csv
import glob
import os
import re
from fractions import Fraction

from verify import imbalance, fmt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGET = {1: 60, 2: 300, 3: 600}   # seed -> seconds per run


def load_previous():
    prev = {}
    with open(os.path.join(ROOT, 'data', 'previous_best.csv')) as fh:
        rows = [l for l in fh if not l.startswith('#')]
    for row in csv.DictReader(rows):
        prev[(int(row['k']), int(row['n']))] = int(row['imbalance3'])
    return prev


def load_runs():
    runs = []
    for f in glob.glob(os.path.join(ROOT, 'results', 'raw', 'r_*_s*.txt')):
        k, n, seed = map(int, re.search(r'r_(\d+)_(\d+)_s(\d+)\.txt$', f).groups())
        lines = open(f).read().strip().split('\n')
        if not lines[0].startswith('COST3'):
            continue            # unfinished or failed run
        c3 = int(lines[0].split()[1])
        R = [list(map(int, l.split())) for l in lines[1:]]
        if 3 * imbalance(R) != c3:
            raise SystemExit(f"solver claim does not verify: {f}")
        runs.append((k, n, seed, c3, R))
    return runs


def main():
    prev = load_previous()
    runs = load_runs()
    best, by_budget = {}, {}
    for k, n, seed, c3, R in runs:
        if (k, n) not in prev:
            continue
        if (k, n) not in best or c3 < best[(k, n)][0]:
            best[(k, n)] = (c3, R)
        key = (k, n, BUDGET[seed])
        by_budget[key] = min(c3, by_budget.get(key, c3))

    rect_dir = os.path.join(ROOT, 'results', 'rectangles')
    for f in glob.glob(os.path.join(rect_dir, '*.txt')):
        os.remove(f)
    with open(os.path.join(ROOT, 'results', 'results.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['k', 'n', 'previous_imbalance3', 'new_imbalance3', 'previous', 'new', 'status'])
        for (k, n) in sorted(prev, key=lambda t: (t[1], t[0])):
            p = prev[(k, n)]
            if (k, n) not in best:
                w.writerow([k, n, p, '', fmt(Fraction(p, 3)), '', 'not run']); continue
            c3, R = best[(k, n)]
            status = 'improved' if c3 < p else ('matched' if c3 == p else 'worse')
            w.writerow([k, n, p, c3, fmt(Fraction(p, 3)), fmt(Fraction(c3, 3)), status])
            if c3 <= p:
                with open(os.path.join(rect_dir, f'k{k}_n{n}.txt'), 'w') as out:
                    out.write(f"# {k} x {n} Latin rectangle, imbalance {fmt(Fraction(c3, 3))} "
                              f"(previous best {fmt(Fraction(p, 3))})\n")
                    for row in R:
                        out.write(' '.join(f'{x:2d}' for x in row) + '\n')
    with open(os.path.join(ROOT, 'results', 'budget.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['k', 'n', 'seconds', 'imbalance3'])
        for (k, n, s) in sorted(by_budget, key=lambda t: (t[1], t[0], t[2])):
            w.writerow([k, n, s, by_budget[(k, n, s)]])

    stats = {}
    for (k, n), p in prev.items():
        if (k, n) in best:
            c3 = best[(k, n)][0]
            st = 'improved' if c3 < p else ('matched' if c3 == p else 'worse')
            stats[st] = stats.get(st, 0) + 1
    print(f"{len(runs)} verified runs; cells: {stats}")


if __name__ == '__main__':
    main()
