#!/usr/bin/env python3
"""Fill the results section of README.md (between the RESULTS markers) from
results/results.csv and results/budget.csv, so the README never drifts from the data."""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START, END = '<!-- RESULTS:START -->', '<!-- RESULTS:END -->'

rows = list(csv.DictReader(open(os.path.join(ROOT, 'results', 'results.csv'))))
for r in rows:
    r['k'], r['n'] = int(r['k']), int(r['n'])
    r['p3'] = int(r['previous_imbalance3'])
    r['c3'] = int(r['new_imbalance3'])
rows.sort(key=lambda r: (r['n'], r['k']))
cell = {(r['k'], r['n']): r for r in rows}
ns = sorted({r['n'] for r in rows})
ks = list(range(2, max(r['k'] for r in rows) + 1))
imp = [r for r in rows if r['c3'] < r['p3']]
mat = [r for r in rows if r['c3'] == r['p3']]
wor = [r for r in rows if r['c3'] > r['p3']]
gain = lambda r: 100 * (r['p3'] - r['c3']) / r['p3']
top = max(imp, key=gain)

budget = {}
for b in csv.DictReader(open(os.path.join(ROOT, 'results', 'budget.csv'))):
    budget.setdefault((int(b['k']), int(b['n'])), {})[int(b['seconds'])] = int(b['imbalance3'])
secs = sorted({s for d in budget.values() for s in d})
full = [c for c, d in budget.items() if all(s in d for s in secs)]


def fmt3(c3):
    q, m = divmod(c3, 3)
    return f"{q}.{[0, 3, 6][m]}"


out = [START, '', '## Results', '',
       f"**{len(imp)} improved, {len(mat)} matched, {len(wor)} worse** out of {len(rows)} instances. "
       f"Improvements average **{sum(map(gain, imp)) / len(imp):.1f}%** and reach "
       f"**{gain(top):.1f}%** ({top['k']}×{top['n']}: {top['previous']} → {top['new']}). "
       "Previous values are from Table 1 of CP 2025; all new values are verified by `code/verify.py`.", '',
       '### At a glance', '',
       '![New best imbalance per cell, shaded by reduction](figures/heatmap.png)', '',
       '*New best imbalance per cell (bold, k across, n down) with the previous best below it, '
       'shaded by the reduction relative to the previous best. Grey cells match the previous value.*', '',
       '### Full table', '',
       '**Bold** = new best value from this work, with the previous best struck through. '
       'Plain = matched. Columns are k (rows of the rectangle), rows are n (symbols).', '',
       '| n \\ k | ' + ' | '.join(map(str, ks)) + ' |',
       '|---:|' + ':---:|' * len(ks)]
for n in ns:
    line = []
    for k in ks:
        r = cell.get((k, n))
        if r is None:
            line.append('')
        elif r['c3'] < r['p3']:
            line.append(f"**{r['new']}** ~~{r['previous']}~~")
        else:
            line.append(r['new'])
    out.append(f'| **{n}** | ' + ' | '.join(line) + ' |')

out += ['', '### Every instance', '',
        'Imbalance values; `x.3` and `x.6` mean x + 1/3 and x + 2/3. '
        'The last column links to the rectangle that achieves the new value.', '',
        '| k × n | previous best | this work | change | reduction | status | rectangle |',
        '|---|---:|---:|---:|---:|---|---|']
for r in rows:
    d3 = r['c3'] - r['p3']
    change = '0' if d3 == 0 else ('−' if d3 < 0 else '+') + fmt3(abs(d3))
    red = f"{gain(r):.1f}%" if d3 < 0 else '—'
    status = '**improved**' if d3 < 0 else ('matched' if d3 == 0 else 'worse')
    link = f"[k{r['k']}_n{r['n']}.txt](results/rectangles/k{r['k']}_n{r['n']}.txt)"
    out.append(f"| {r['k']} × {r['n']} | {r['previous']} | {r['new']} | {change} | {red} | {status} | {link} |")

out += ['', '### Size of each improvement', '',
        '![Previous best vs. new value for every improved instance](figures/dumbbell.png)', '',
        '*Previous best (open circles) and new value (filled) for each improved instance. '
        'Gains grow with instance size.*', '',
        '### Effect of the time budget', '',
        '![Mean reduction vs. time per run](figures/budget.png)', '',
        f'*Mean reduction relative to the previous best over the {len(full)} instances run at all three '
        'budgets (k ≥ 4, n ≥ 9). One single-threaded run per budget, each with a different seed. '
        'Longer runs widen the margin; the table gives the exact numbers.*', '',
        '| time per run | ' + ' | '.join(f'{s // 60} min' for s in secs) + ' |',
        '|---|' + '---:|' * len(secs),
        '| mean reduction | ' + ' | '.join(
            f"{100 * sum((cell[c]['p3'] - budget[c][s]) / cell[c]['p3'] for c in full) / len(full):.1f}%"
            for s in secs) + ' |',
        '| instances improved | ' + ' | '.join(
            str(sum(budget[c][s] < cell[c]['p3'] for c in full)) + f' / {len(full)}' for s in secs) + ' |',
        '', END]

path = os.path.join(ROOT, 'README.md')
text = open(path).read()
if START in text:
    pre, rest = text.split(START, 1)
    post = rest.split(END, 1)[1]
    text = pre + '\n'.join(out) + post
else:
    anchor = '## Check the records'
    text = text.replace(anchor, '\n'.join(out) + '\n\n' + anchor, 1)
open(path, 'w').write(text)
print(f"README results section written: {len(rows)} instances, {len(full)} with all budgets")
