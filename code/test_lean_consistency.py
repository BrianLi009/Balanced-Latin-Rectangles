#!/usr/bin/env python3
"""Check that the numbers printed in the arXiv paper are exactly the ones certified in Lean.

Lean certifies `rect_<name>.imb3 = V` (V = 3*I) for each rectangle. This script reads those
statements from lean/BalancedLatin/Certificates/*.lean and compares them with
  * every value from this work in arxiv/table.tex (Table 1: bold new values and plain matched values),
  * the annealing row of arxiv/table_k2.tex (Table 3),
  * the values quoted in the text and captions of arxiv/main.tex for 3 x 9, 2 x 16 and 12 x 13.
It also checks that every rectangle file has a certificate, with the same rows.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify import read_rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT = os.path.join(ROOT, 'lean', 'BalancedLatin', 'Certificates')


def lean_certified():
    """name -> (3I, rows) for every certificate."""
    out = {}
    for f in glob.glob(os.path.join(CERT, '*.lean')):
        text = open(f).read()
        for name, val in re.findall(r'theorem imb3_(\w+) : rect_\1\.imb3 = (\d+) := by decide \+kernel', text):
            body = re.search(r'def rows_' + name + r' : List \(List Nat\) :=\s*\[(.*?)\]\n', text, re.S).group(1)
            rows = [[int(x) for x in r.split(',')] for r in re.findall(r'\[([\d, ]+)\]', body)]
            out[name] = (int(val), rows)
    return out


def to3(s):
    """'53.3' -> 160 (x.0, x.3, x.6 mean x, x+1/3, x+2/3)."""
    q, r = s.split('.')
    return 3 * int(q) + {'0': 0, '3': 1, '6': 2}[r]


def main():
    cert = lean_certified()
    errors = []

    def expect(name, value3, where):
        if name not in cert:
            errors.append(f'{where}: no Lean certificate for {name}')
        elif cert[name][0] != value3:
            errors.append(f'{where}: paper says 3I={value3}, Lean certifies {cert[name][0]} ({name})')

    # every data file has a certificate with identical rows
    files = glob.glob(os.path.join(ROOT, 'results', 'rectangles', '*.txt')) + \
        glob.glob(os.path.join(ROOT, 'results', 'k2_large', '*.txt')) + \
        [(p, 'pub_') for p in glob.glob(os.path.join(ROOT, 'data', 'published', '*.txt'))]
    for f in files:
        f, prefix = f if isinstance(f, tuple) else (f, '')
        name = prefix + os.path.basename(f)[:-4]
        if name not in cert:
            errors.append(f'{f}: no certificate')
        elif cert[name][1] != read_rectangle(f):
            errors.append(f'{f}: rows differ from the Lean certificate')

    # Table 1: first number in each cell is the value from this work
    rows = 0
    for line in open(os.path.join(ROOT, 'arxiv', 'table.tex')):
        m = re.match(r'(\d+) & (.*)\\\\', line)
        if not m:
            continue
        n = int(m.group(1))
        for k, cell in enumerate(m.group(2).split('&'), start=2):
            v = re.search(r'(\d+\.\d)', cell)
            if v:
                expect(f'k{k}_n{n}', to3(v.group(1)), f'table.tex {k}x{n}')
                rows += 1
    if rows != 51:
        errors.append(f'table.tex: parsed {rows} cells, expected 51')

    # Table 3: annealing row, n = 14..20
    t2 = open(os.path.join(ROOT, 'arxiv', 'table_k2.tex')).read()
    ns = [int(x) for x in re.search(r'\$n\$ & ([\d &]+)\\\\', t2).group(1).split('&')]
    ann = re.findall(r'(\d+\.\d)', re.search(r'annealing.*', t2).group(0))
    if len(ns) != len(ann):
        errors.append('table_k2.tex: could not parse the annealing row')
    for n, v in zip(ns, ann):
        expect(f'k2_n{n}', to3(v), f'table_k2.tex n={n}')

    # values quoted in main.tex
    tex = open(os.path.join(ROOT, 'arxiv', 'main.tex')).read()
    if not re.search(r'3\\times 9\$ Latin rectangle is \$56\$', tex):
        errors.append('main.tex: statement of thm:3x9 changed; update this test')
    expect('k3_n9', 168, 'main.tex thm:3x9 / fig:optimum (I = 56)')
    if '$2\\times16$ rectangle with $I=422$' not in tex:
        errors.append('main.tex: fig:geometry caption changed; update this test')
    expect('k2_n16', 1266, 'main.tex fig:geometry (2x16, I = 422)')
    expect('k12_n13', 498, 'README/abstract headline (12x13, I = 166)')

    if errors:
        print('\n'.join(errors))
        return 1
    print(f'{len(cert)} Lean certificates; Table 1 ({rows} cells), Table 3 ({len(ann)} values) '
          f'and quoted values all match.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
