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


import statistics as st
timing = {}
for t in csv.DictReader(open(os.path.join(ROOT, 'results', 'timing.csv'))):
    timing.setdefault((t['kind'], int(t['k']), int(t['n'])), []).append(t)


def tsec(key):
    return [float(t['seconds']) for t in timing.get(key, []) if t['seconds']]


def fmt_s(x):
    if x < 0.01:
        return f"{1000 * x:.0f} ms"
    if x < 60:
        return f"{x:.2f} s" if x < 10 else f"{x:.0f} s"
    return f"{x / 60:.1f} min"


def fmt_ref(x):
    return f"{x / 60:.0f} min" if x < 3600 else f"{x / 3600:.1f} h"


def fmt3(c3):
    q, m = divmod(c3, 3)
    return f"{q}.{[0, 3, 6][m]}"


ALLBEAT = [x for key in timing if key[0] == 'beat_cp2025' for x in tsec(key)]
SEEDS = sorted({t['seed'] for key in timing if key[0] == 'beat_cp2025' for t in timing[key]})

out = [START, '', '## Results', '',
       f"**{len(imp)} improved, {len(mat)} matched, {len(wor)} worse** out of {len(rows)} instances. "
       f"Improvements average **{sum(map(gain, imp)) / len(imp):.1f}%** and reach "
       f"**{gain(top):.1f}%** ({top['k']}×{top['n']}: {top['previous']} → {top['new']}). "
       "Previous values are from Table 1 of CP 2025; all new values are verified by `code/verify.py`.", '',
       '### Speed', '',
       f"Beyond better values, the search is fast. With {len(SEEDS)} seeds per instance, each stopping as soon as it "
       f"beats the CP 2025 record, the **median time to beat a record is {fmt_s(st.median(ALLBEAT))}** of CPU time on "
       f"one laptop core, and **every run beats it within {fmt_s(max(ALLBEAT))}**. The CP 2025 pipeline spends at least "
       "4 hours per instance per approach (after a 4-hour Gurobi baseline), on 10-core servers.", '',
       '![Time until each CP 2025 record is beaten](figures/speed.png)', '',
       '*CPU time until the search beats the CP 2025 record: median (dot) and range (bar) over 5 seeds, '
       'log scale. The dashed line marks one 4-hour run of one CP 2025 approach.*', '',
       'The SAT approach of CP 2023 reports solving times for four rectangles. '
       'The search reaches the same imbalance in under a tenth of a second:', '',
       '![Time to match the CP 2023 SAT results](figures/speed_cp2023.png)', '',
       '| instance | imbalance | SAT, CP 2023 (reported) | this work (median of 5) | this work (slowest) |',
       '|---|---:|---:|---:|---:|'] + [
       f"| {k} × {n} | {int(timing[(kind, k, n)][0]['target3']) // 3} | "
       f"{fmt_ref(float(timing[(kind, k, n)][0]['reference_seconds']))} | "
       f"{fmt_s(st.median(tsec((kind, k, n))))} | {fmt_s(max(tsec((kind, k, n))))} |"
       for (kind, k, n) in sorted([x for x in timing if x[0] == 'match_cp2023'], key=lambda t: (t[2], t[1]))] + [
       '', '*Caveats: different hardware (Xeon E5-2640 v4 servers vs. an Apple M3 laptop; the single-core gap is a '
       'small factor), CP 2025 does not report when within its runs each record was found, and we did not rerun '
       'either pipeline. See the paper for details.*', '',
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
        '| k × n | previous best | this work | change | reduction | time to beat (median of 5) | status | rectangle |',
        '|---|---:|---:|---:|---:|---:|---|---|']
for r in rows:
    d3 = r['c3'] - r['p3']
    change = '0' if d3 == 0 else ('−' if d3 < 0 else '+') + fmt3(abs(d3))
    red = f"{gain(r):.1f}%" if d3 < 0 else '—'
    status = '**improved**' if d3 < 0 else ('matched' if d3 == 0 else 'worse')
    link = f"[k{r['k']}_n{r['n']}.txt](results/rectangles/k{r['k']}_n{r['n']}.txt)"
    tb = tsec(('beat_cp2025', r['k'], r['n']))
    tcol = fmt_s(st.median(tb)) if tb else '—'
    out.append(f"| {r['k']} × {r['n']} | {r['previous']} | {r['new']} | {change} | {red} | {tcol} | {status} | {link} |")

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
