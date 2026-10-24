#!/usr/bin/env python3
"""Check all 14 printed examples in CP 2023 (Figs. 1, 2) and CP 2025 (Figs. 1, 6).

Require the complete named fixture set and exact published values. These examples
are regression checks, not a proof that the checker is correct on all inputs.
"""
from pathlib import Path
import re
import sys
from verify import imbalance, read_rectangle, fmt

ROOT = Path(__file__).resolve().parents[1]
# Filename, k, n, exact 3*imbalance. Sources are identified in each fixture header.
EXAMPLES = {
    'cp2023_fig1a_3x5.txt': (3, 5, 18),
    'cp2023_fig2a_3x10.txt': (3, 10, 252),
    'cp2023_fig2b_4x11.txt': (4, 11, 354),
    'cp2023_fig2c_6x10.txt': (6, 10, 288),
    'cp2023_fig2d_6x11.txt': (6, 11, 372),
    'cp2025_fig1_3x4.txt': (3, 4, 12),
    'cp2025_fig6a_6x10.txt': (6, 10, 210),
    'cp2025_fig6b_7x9.txt': (7, 9, 154),
    'cp2025_fig6c_4x12.txt': (4, 12, 464),
    'cp2025_fig6d_5x12.txt': (5, 12, 436),
    'cp2025_fig6e_8x12.txt': (8, 12, 444),
    'cp2025_fig6f_8x13.txt': (8, 13, 662),
    'cp2025_fig6g_11x13.txt': (11, 13, 672),
    'cp2025_fig6h_12x13.txt': (12, 13, 822),
}

def main():
    directory = ROOT / 'data' / 'published'
    if {p.name for p in directory.glob('*.txt')} != set(EXAMPLES):
        raise ValueError('published fixtures must contain exactly the 14 named examples')
    for name, (k, n, c3) in sorted(EXAMPLES.items()):
        path = directory / name
        R = read_rectangle(path)
        got = imbalance(R)
        if (len(R), len(R[0])) != (k, n) or 3 * got != c3:
            raise ValueError(f'incorrect dimensions or imbalance: {name}')
        header = re.search(r'reported imbalance ([0-9.]+)', path.read_text().splitlines()[0])
        if not header or header.group(1) != fmt(got):
            raise ValueError(f'incorrect reported value in fixture header: {name}')
        print(f'{name:28s}  I = {fmt(got):>6}  OK')
    print('\n14 published rectangles, 0 mismatches.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print(f'Fixture verification failed: {exc}', file=sys.stderr)
        sys.exit(1)
