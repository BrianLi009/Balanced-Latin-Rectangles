#!/usr/bin/env python3
"""Independent checker for balanced Latin rectangles.

Reads k x n rectangles (whitespace-separated symbols 1..n, one row per line),
checks the Latin property, and recomputes the imbalance exactly
(Ramaswamy & Szeider, CP 2023, eqs. (1)-(4)):

    d(u, v) = sum_i |col_i(u) - col_i(v)|,   I(L) = sum_{u<v} |d(u, v) - k(n+1)/3|.

Usage:
    verify.py                         # check results/rectangles/*.txt against results/results.csv
    verify.py FILE [FILE ...]         # print the imbalance of each file
"""
from pathlib import Path
import csv
import glob
import os
import re
import sys
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_CELLS = {(k, n) for n in range(8, 14) for k in range(2, n)}


def read_rectangle(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            rows.append([int(x) for x in line.split()])
    return rows


def imbalance(R):
    if not R or not R[0]:
        raise ValueError("empty rectangle")
    k, n = len(R), len(R[0])
    if k > n:
        raise ValueError("more rows than columns")
    for r in R:
        if sorted(r) != list(range(1, n + 1)):
            raise ValueError(f"row {r} is not a permutation of 1..{n}")
    for j in range(n):
        if len({R[i][j] for i in range(k)}) != k:
            raise ValueError(f"column {j + 1} repeats a symbol")
    pos = [{s: j for j, s in enumerate(r)} for r in R]
    Z = Fraction(k * (n + 1), 3)
    return sum(abs(sum(abs(p[u] - p[v]) for p in pos) - Z)
               for u in range(1, n + 1) for v in range(u + 1, n + 1))


def fmt(I):
    """Format like the literature: x.0, x.3, x.6 for x, x+1/3, x+2/3."""
    q, r = divmod(int(3 * I), 3)
    return f"{q}.{[0, 3, 6][r]}"


def main(argv):
    if argv:
        for f in argv:
            R = read_rectangle(f)
            I = imbalance(R)
            print(f"{f}: {len(R)}x{len(R[0])}  I = {I} ({fmt(I)})")
        return 0
    claimed = {}
    with open(os.path.join(ROOT, 'results', 'results.csv')) as fh:
        for row in csv.DictReader(fh):
            key = (int(row['k']), int(row['n']))
            if key in claimed:
                raise ValueError(f"duplicate CSV instance: {key}")
            claimed[key] = int(row['new_imbalance3'])
    if set(claimed) != EXPECTED_CELLS:
        raise ValueError("results.csv must contain exactly the 51 benchmark instances")
    bad = 0
    files = sorted(glob.glob(os.path.join(ROOT, 'results', 'rectangles', '*.txt')))
    expected_files = {f'k{k}_n{n}.txt' for k, n in EXPECTED_CELLS}
    if {os.path.basename(f) for f in files} != expected_files:
        raise ValueError("rectangle files must cover exactly the 51 benchmark instances")
    for f in files:
        R = read_rectangle(f)
        I = imbalance(R)
        k, n = map(int, re.fullmatch(r'k(\d+)_n(\d+)\.txt', os.path.basename(f)).groups())
        if (len(R), len(R[0])) != (k, n):
            raise ValueError(f"filename dimensions do not match rectangle: {f}")
        ok = claimed.get((k, n)) == 3 * I
        bad += not ok
        print(f"{k:2d} x {n:2d}  I = {fmt(I):>6}  {'OK' if ok else 'MISMATCH with results.csv'}")
    print(f"\n{len(files)} rectangles checked, {bad} problems.")
    return 1 if bad else 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, OSError, KeyError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
