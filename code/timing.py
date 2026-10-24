#!/usr/bin/env python3
"""Time-to-target experiment.

For each target, runs ./sa with several seeds and a CPU-time cap, stopping as soon as the
imbalance reaches the target. Every rectangle that reaches its target is re-checked with
verify.imbalance. Writes results/timing.csv with one row per (instance, target, seed).

Targets:
  beat_cp2025  strictly below the CP 2025 best known value (all cells improved in this work)
  match_cp2023 at most the value of the four rectangles whose SAT solving time is reported in
               Ramaswamy & Szeider (CP 2023), Fig. 2
"""
import csv
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction

from verify import imbalance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = [101, 102, 103, 104, 105]
CAP = 300                                   # CPU seconds per run
JOBS = int(os.environ.get('JOBS', 8))

# CP 2023, Fig. 2: (k, n, imbalance, reported SAT time in seconds)
CP2023 = [(3, 10, 84, 32 * 60), (4, 11, 118, 102 * 60), (6, 10, 96, 40 * 60), (6, 11, 124, 5.5 * 3600)]


def targets():
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, 'results', 'results.csv'))):
        if r['status'] == 'improved':
            p3 = int(r['previous_imbalance3'])
            out.append(('beat_cp2025', int(r['k']), int(r['n']), p3 - 1, ''))
    for k, n, I, t in CP2023:
        out.append(('match_cp2023', k, n, 3 * I, t))
    return out


def run(job):
    kind, k, n, t3, ref = job[:5]
    seed = job[5]
    p = subprocess.run(['./sa', str(k), str(n), str(CAP), str(seed), str(t3)],
                       capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    lines = p.stdout.strip().split('\n')
    c3 = int(lines[0].split()[1])
    R = [list(map(int, l.split())) for l in lines[1:]]
    assert 3 * imbalance(R) == c3, f"verification failed for {k}x{n} seed {seed}"
    t = float(p.stderr.split('TIME_TO_BEST')[1].split()[0])
    reached = c3 <= t3
    return dict(kind=kind, k=k, n=n, target3=t3, seed=seed, reached=int(reached),
                seconds=f"{t:.3f}" if reached else '', best3=c3, reference_seconds=ref)


def main():
    jobs = [t + (s,) for t in targets() for s in SEEDS]
    with ThreadPoolExecutor(JOBS) as ex:
        rows = list(ex.map(run, jobs))
    path = os.path.join(ROOT, 'results', 'timing.csv')
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    ok = sum(r['reached'] for r in rows)
    print(f"{ok}/{len(rows)} runs reached their target within {CAP} s; written to {path}")


if __name__ == '__main__':
    main()
