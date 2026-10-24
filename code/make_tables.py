#!/usr/bin/env python3
"""Write paper/table.tex (results table) and paper/numbers.tex (macros used in the text)
from results/results.csv and results/budget.csv, so the paper never drifts from the data."""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(ROOT, 'results', 'results.csv'))))
for r in rows:
    r['k'], r['n'] = int(r['k']), int(r['n'])
    r['p3'] = int(r['previous_imbalance3'])
    r['c3'] = int(r['new_imbalance3']) if r['new_imbalance3'] else None

ns = sorted({r['n'] for r in rows})
ks = list(range(2, max(r['k'] for r in rows) + 1))
cell = {(r['k'], r['n']): r for r in rows}

out = [r'\begin{tabular}{r' + 'c' * len(ks) + '}', r'\toprule',
       r'$n \backslash k$ & ' + ' & '.join(map(str, ks)) + r' \\', r'\midrule']
for n in ns:
    line = [str(n)]
    for k in ks:
        r = cell.get((k, n))
        if r is None or r['c3'] is None:
            line.append('')
        elif r['c3'] < r['p3']:
            line.append(r'\shortstack{\textbf{' + r['new'] + r'}\\{\tiny\sout{' + r['previous'] + '}}}')
        else:
            line.append(r['new'])
    out.append(' & '.join(line) + r' \\[2pt]')
out += [r'\bottomrule', r'\end{tabular}']
open(os.path.join(ROOT, 'paper', 'table.tex'), 'w').write('\n'.join(out) + '\n')

imp = [r for r in rows if r['c3'] is not None and r['c3'] < r['p3']]
mat = [r for r in rows if r['c3'] is not None and r['c3'] == r['p3']]
wor = [r for r in rows if r['c3'] is not None and r['c3'] > r['p3']]
gains = sorted(((r['p3'] - r['c3']) / r['p3'] for r in imp), reverse=True)
top = max(imp, key=lambda r: (r['p3'] - r['c3']) / r['p3'])
budget = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'results', 'budget.csv'))):
    budget.setdefault((int(r['k']), int(r['n'])), {})[int(r['seconds'])] = int(r['imbalance3'])
one_min = [c for c, d in budget.items() if 60 in d and d[60] < cell[c]['p3']]
macros = {
    'NumCells': len(rows), 'NumImproved': len(imp), 'NumMatched': len(mat), 'NumWorse': len(wor),
    'MeanGain': f"{100 * sum(gains) / len(gains):.1f}", 'MaxGain': f"{100 * gains[0]:.1f}",
    'TopCell': f"${top['k']}\\times{top['n']}$", 'TopOld': top['previous'], 'TopNew': top['new'],
    'NumImprovedOneMin': len(one_min),
}
with open(os.path.join(ROOT, 'paper', 'numbers.tex'), 'w') as fh:
    for k, v in macros.items():
        fh.write(f'\\newcommand{{\\{k}}}{{{v}}}\n')
print(macros)
