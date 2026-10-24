#!/usr/bin/env python3
"""Time-to-target experiment with per-run witnesses and execution metadata.

Default output: results/timing.csv (explicitly replaced when this script is run).
Each invocation also retains a unique archive under results/timing_runs/.
Use --output PATH for a separate experiment. Failed targets are retained and cause
an unsuccessful exit; paper generators reject incomplete/censored measurements.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from verify import imbalance, EXPECTED_CELLS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = [101, 102, 103, 104, 105]
CAP = 300
JOBS = int(os.environ.get('JOBS', 8))
CP2023 = [(3, 10, 84, 32 * 60), (4, 11, 118, 102 * 60),
          (6, 10, 96, 40 * 60), (6, 11, 124, 5.5 * 3600)]


def targets():
    out = []
    seen = set()
    with open(os.path.join(ROOT, 'results', 'results.csv')) as fh:
        for r in csv.DictReader(fh):
            key = (int(r['k']), int(r['n']))
            if key in seen or key not in EXPECTED_CELLS:
                raise ValueError('duplicate or unexpected result instance')
            seen.add(key)
            old, new = int(r['previous_imbalance3']), int(r['new_imbalance3'])
            status = 'improved' if new < old else ('matched' if new == old else 'worse')
            if r['status'] != status:
                raise ValueError('result status disagrees with objective values')
            if r['status'] == 'improved':
                out.append(('beat_cp2025', int(r['k']), int(r['n']),
                            int(r['previous_imbalance3']) - 1, ''))
    if seen != EXPECTED_CELLS:
        raise ValueError('result data must cover all 51 instances')
    out.extend(('match_cp2023', k, n, 3 * I, t) for k, n, I, t in CP2023)
    return out


def load_timing_results():
    """Require complete five-seed, successful measurements before generating the paper."""
    with open(os.path.join(ROOT, 'results', 'timing.csv')) as fh:
        rows = list(csv.DictReader(fh))
    expected = {(kind, k, n, seed): (t3, ref)
                for kind, k, n, t3, ref in targets() for seed in SEEDS}
    seen = set()
    for r in rows:
        key = (r['kind'], int(r['k']), int(r['n']), int(r['seed']))
        if key in seen or key not in expected:
            raise ValueError(f'duplicate/unexpected timing row: {key}')
        seen.add(key)
        target, ref = expected[key]
        if int(r['target3']) != target or int(r['best3']) > target or r['reached'] != '1':
            raise ValueError(f'target not reached or incorrect: {key}; do not publish a success-only summary')
        seconds = float(r['seconds'])
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError(f'invalid time: {key}')
        if ref != '' and float(r['reference_seconds']) != ref:
            raise ValueError(f'incorrect historical reference time: {key}')
    if seen != set(expected):
        raise ValueError('timing data must include every expected instance and all five seeds')
    return rows


def run(job, archive_dir, cap=CAP):
    kind, k, n, t3, ref, seed = job
    cmd = ['./sa', str(k), str(n), str(cap), str(seed), str(t3)]
    start = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.abspath(__file__)))
    name = f'{kind}_{k}_{n}_{seed}'
    archive_dir = Path(archive_dir)
    (archive_dir / (name + '.stdout')).write_text(p.stdout)
    (archive_dir / (name + '.stderr')).write_text(p.stderr)
    (archive_dir / (name + '.json')).write_text(json.dumps({
        'command': cmd, 'returncode': p.returncode,
        'wall_seconds': time.monotonic() - start,
    }, indent=2) + '\n')
    if p.returncode:
        raise RuntimeError(f'solver failed for {name}; see archived stderr')
    lines = p.stdout.strip().splitlines()
    if not lines or len(lines[0].split()) != 2 or lines[0].split()[0] != 'COST3':
        raise ValueError(f'malformed solver output for {name}')
    c3 = int(lines[0].split()[1])
    R = [list(map(int, line.split())) for line in lines[1:]]
    if len(R) != k or any(len(row) != n for row in R) or 3 * imbalance(R) != c3:
        raise ValueError(f'verification failed for {name}')
    t = float(p.stderr.split('TIME_TO_BEST')[1].split()[0])
    if not math.isfinite(t) or t < 0:
        raise ValueError(f'invalid solver time for {name}')
    reached = c3 <= t3
    return dict(kind=kind, k=k, n=n, target3=t3, seed=seed, reached=int(reached),
                seconds=f'{t:.3f}' if reached else '', best3=c3, reference_seconds=ref)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(ROOT) / 'results/timing.csv')
    parser.add_argument('--cap', type=float, default=CAP)
    parser.add_argument('--jobs', type=int, default=JOBS)
    args = parser.parse_args()
    if args.jobs < 1 or not math.isfinite(args.cap) or args.cap <= 0:
        parser.error('jobs and finite CPU cap must be positive')
    parent = Path(ROOT) / 'results/timing_runs'
    parent.mkdir(parents=True, exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-'), dir=parent))
    source = Path(ROOT) / 'code/sa.c'
    binary = Path(ROOT) / 'code/sa'
    metadata = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'platform': platform.platform(), 'processor': platform.processor(),
        'python': sys.version, 'jobs': args.jobs, 'cpu_cap_seconds': args.cap,
        'seeds': SEEDS, 'targets': targets(),
        'solver_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'solver_binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'timing_scope': 'process CPU from after initialization to first target incumbent; excludes launch/output/verification',
    }
    # Preserve the source present; hashes alone do not prove how an existing binary was built.
    (archive / 'sa.c').write_bytes(source.read_bytes())
    (archive / 'environment.json').write_text(json.dumps(metadata, indent=2) + '\n')
    jobs = [t + (s,) for t in targets() for s in SEEDS]
    with ThreadPoolExecutor(args.jobs) as ex:
        rows = list(ex.map(lambda job: run(job, archive, args.cap), jobs))
    archive_csv = archive / 'timing.csv'
    with archive_csv.open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Replace only after every solver process and witness check completed.
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as fh:
        fh.write(archive_csv.read_bytes())
        temporary = fh.name
    os.replace(temporary, args.output)
    ok = sum(r['reached'] for r in rows)
    print(f'{ok}/{len(rows)} targets reached; output: {args.output}; witnesses: {archive}')
    return 0 if ok == len(rows) else 1


if __name__ == '__main__':
    sys.exit(main())
