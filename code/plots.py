#!/usr/bin/env python3
"""Figures for the paper (PDF + PNG in figures/). Reads results/results.csv and results/budget.csv."""
import csv
import os
from fractions import Fraction

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, 'figures')

# Ink and ramp (validated reference palette, light surface)
SURFACE, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
BLUE_RAMP = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
BLUE, NEUTRAL = '#2a78d6', '#b9b8b2'

plt.rcParams.update({
    'font.family': 'serif', 'mathtext.fontset': 'dejavuserif', 'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
    'xtick.color': INK2, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.bbox': 'tight',
})


def save(fig, name):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIG, f'{name}.{ext}'), dpi=200)
    plt.close(fig)


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'results', 'results.csv'))))
    for r in rows:
        r['k'], r['n'] = int(r['k']), int(r['n'])
        r['p3'] = int(r['previous_imbalance3'])
        r['c3'] = int(r['new_imbalance3']) if r['new_imbalance3'] else None
    return rows


def _lum(c):
    r, g, b = matplotlib.colors.to_rgb(c)
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    """WCAG contrast ratio between two colours."""
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def heatmap(rows, sub_size=6.5):
    """Each cell: new best value, and for improved cells the previous best below it. After
    drawing, every label is measured; if one leaves its cell, the small line is redrawn at a
    smaller size (down to 4.5 pt), and the figure is rejected if it still does not fit."""
    ns = sorted({r['n'] for r in rows}); ks = list(range(2, max(r['k'] for r in rows) + 1))
    cmap = LinearSegmentedColormap.from_list('seq', BLUE_RAMP)
    vmax = max((r['p3'] - r['c3']) / r['p3'] for r in rows if r['c3'] is not None and r['p3'])
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    PAD = 0.04                                       # gap between cells, in cell units
    cells = []                                       # (label artists, cell rectangle)
    for r in rows:
        if r['c3'] is None:
            continue
        x, y = ks.index(r['k']), ns.index(r['n'])
        gain = (r['p3'] - r['c3']) / r['p3'] if r['p3'] else 0.0
        face = cmap(gain / vmax) if gain > 0 else '#f0efec'
        rect = plt.Rectangle((x - 0.5 + PAD, y - 0.5 + PAD), 1 - 2 * PAD, 1 - 2 * PAD,
                             facecolor=face, edgecolor='none')
        ax.add_patch(rect)
        dark = gain > 0 and contrast(face, '#ffffff') > contrast(face, INK)
        main_ink, sub_ink = ('white', 'white') if dark else (INK, INK)
        if gain > 0:
            t1 = ax.text(x, y + 0.15, r['new'], ha='center', va='center', fontsize=8,
                         color=main_ink, weight='bold')
            t2 = ax.text(x, y - 0.21, f"was {r['previous']}", ha='center', va='center',
                         fontsize=sub_size, color=sub_ink)
            cells.append(((t1, t2), rect))
        else:
            t1 = ax.text(x, y, r['new'], ha='center', va='center', fontsize=8, color=INK2)
            cells.append(((t1,), rect))
    ax.set_xlim(-0.5, len(ks) - 0.5); ax.set_ylim(-0.5, len(ns) - 0.5)
    ax.set_xticks(range(len(ks)), ks); ax.set_yticks(range(len(ns)), ns)
    ax.set_xlabel('rows $k$'); ax.set_ylabel('symbols $n$')
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100 * vmax))
    cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.015, format='%d%%')
    cb.set_label('reduction vs. previous best', color=INK2); cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, length=0)

    # Overflow check: every label must sit inside its cell with a small margin.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for texts, rect in cells:
        box = rect.get_window_extent(renderer)
        mx, my = 0.15 * box.width, 0.08 * box.height   # keep labels well clear of the cell edges
        for t in texts:
            tb = t.get_window_extent(renderer)
            if tb.x0 < box.x0 + mx or tb.x1 > box.x1 - mx or tb.y0 < box.y0 + my or tb.y1 > box.y1 - my:
                plt.close(fig)
                if sub_size <= 4.5:
                    raise SystemExit(f"heatmap label '{t.get_text()}' overflows its cell")
                return heatmap(rows, sub_size - 0.25)
    save(fig, 'heatmap')
    return sub_size


def dumbbell(rows):
    imp = [r for r in rows if r['c3'] is not None and r['c3'] < r['p3']]
    imp.sort(key=lambda r: (r['n'], r['k']))
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for i, r in enumerate(imp):
        y = len(imp) - 1 - i
        p, c = r['p3'] / 3, r['c3'] / 3
        ax.plot([c, p], [y, y], color=GRID, linewidth=2, solid_capstyle='round', zorder=1)
        ax.scatter([p], [y], s=26, facecolor='white', edgecolor=NEUTRAL, linewidth=1.5, zorder=2)
        ax.scatter([c], [y], s=30, color=BLUE, edgecolor='white', linewidth=1.2, zorder=3)
    ax.set_yticks(range(len(imp)), [f"{r['k']}×{r['n']}" for r in reversed(imp)], fontsize=6.5)
    ax.set_xlabel('imbalance $I(L)$ (lower is better)')
    ax.grid(axis='x', color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0)
    ax.scatter([], [], s=26, facecolor='white', edgecolor=NEUTRAL, linewidth=1.5, label='previous best (CP 2025)')
    ax.scatter([], [], s=30, color=BLUE, label='this work')
    ax.legend(loc='upper right', frameon=False, fontsize=8)
    ax.set_ylim(-0.8, len(imp) - 0.2)
    save(fig, 'dumbbell')


def budget(rows):
    prev = {(r['k'], r['n']): r['p3'] for r in rows}
    data = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'results', 'budget.csv'))):
        data.setdefault((int(r['k']), int(r['n'])), {})[int(r['seconds'])] = int(r['imbalance3'])
    secs = sorted({s for d in data.values() for s in d})
    cells = [c for c, d in data.items() if all(s in d for s in secs)]
    mean_gain = [100 * sum((prev[c] - data[c][s]) / prev[c] for c in cells) / len(cells) for s in secs]
    fig, ax = plt.subplots(figsize=(3.3, 2.3))
    ax.plot(secs, mean_gain, color=BLUE, linewidth=2, marker='o', markersize=5,
            markeredgecolor='white', markeredgewidth=1.2)
    for s, g in zip(secs, mean_gain):
        ax.annotate(f'{g:.1f}%', (s, g), textcoords='offset points', xytext=(0, 7), ha='center',
                    fontsize=7.5, color=INK)
    ax.set_xticks(secs, [f'{s // 60} min' for s in secs])
    ax.set_ylabel('mean reduction (%)'); ax.set_xlabel('time per run (one run, one core)')
    ax.set_ylim(0, max(mean_gain) * 1.25)
    ax.grid(axis='y', color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    save(fig, 'budget')
    return len(cells), dict(zip(secs, mean_gain))


def load_timing():
    path = os.path.join(ROOT, 'results', 'timing.csv')
    if not os.path.exists(path):
        return None
    g = {}
    for r in csv.DictReader(open(path)):
        key = (r['kind'], int(r['k']), int(r['n']))
        g.setdefault(key, {'t': [], 'ref': r['reference_seconds'], 'reached': []})
        g[key]['reached'].append(int(r['reached']))
        if r['seconds']:
            g[key]['t'].append(float(r['seconds']))
    return g


def fmt_time(s):
    if s < 0.01: return f'{1000 * s:.0f} ms'
    if s < 1: return f'{s:.2f} s'
    if s < 60: return f'{s:.0f} s'
    if s < 3600: return f'{s / 60:.0f} min'
    return f'{s / 3600:.1f} h'


def speed(g):
    """Time to beat each CP 2025 record: median and range over seeds, log scale."""
    import statistics as st
    rows = sorted([k for k in g if k[0] == 'beat_cp2025'], key=lambda t: (t[2], t[1]))
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    floor = 0.01                                     # display floor for log scale (10 ms)
    for i, key in enumerate(rows):
        y = len(rows) - 1 - i
        t = [max(v, floor) for v in g[key]['t']]
        ax.plot([min(t), max(t)], [y, y], color=GRID, linewidth=3, solid_capstyle='round', zorder=1)
        ax.scatter([st.median(t)], [y], s=28, color=BLUE, edgecolor='white', linewidth=1.2, zorder=3)
    for x, label, side in ((60, '1 min', 'left'), (4 * 3600, 'one CP 2025 run:\n4 h per approach,\nper instance', 'right')):
        ax.axvline(x, color=INK2, linewidth=0.8, linestyle=(0, (3, 3)), zorder=0)
        ax.text(x * 1.15 if side == 'left' else x / 1.15, len(rows) - 0.6, label, fontsize=7.5,
                color=INK2, va='top', ha=side)
    ax.set_xscale('log')
    ax.set_xlim(floor * 0.7, 4 * 3600 * 5)
    ticks = [0.01, 0.1, 1, 10, 60, 600, 3600, 4 * 3600]
    ax.set_xticks(ticks, ['10 ms', '0.1 s', '1 s', '10 s', '1 min', '10 min', '1 h', '4 h'])
    ax.minorticks_off()
    ax.set_yticks(range(len(rows)), [f'{k}×{n}' for _, k, n in reversed(rows)], fontsize=6.5)
    ax.tick_params(axis='y', length=0)
    ax.set_xlabel('CPU time until the CP 2025 record is beaten (log scale)')
    ax.grid(axis='x', color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    save(fig, 'speed')


def speed_cp2023(g):
    """The four rectangles whose SAT solving time CP 2023 reports, vs. our time to match them."""
    import statistics as st
    rows = sorted([k for k in g if k[0] == 'match_cp2023'], key=lambda t: (t[2], t[1]))
    fig, ax = plt.subplots(figsize=(6.6, 1.9))
    for i, key in enumerate(rows):
        y = len(rows) - 1 - i
        ref = float(g[key]['ref'])
        ours = max(st.median(g[key]['t']), 0.001)
        ax.plot([ours, ref], [y, y], color=GRID, linewidth=2, zorder=1)
        ax.scatter([ref], [y], s=30, facecolor='white', edgecolor=NEUTRAL, linewidth=1.5, zorder=2)
        ax.scatter([ours], [y], s=32, color=BLUE, edgecolor='white', linewidth=1.2, zorder=3)
        ax.text(ref * 1.6, y, fmt_time(ref), va='center', fontsize=7.5, color=INK2)
        ax.text(ours / 1.6, y, fmt_time(ours), va='center', ha='right',
                fontsize=7.5, color=INK)
    ax.set_xscale('log'); ax.set_xlim(0.0003, 2e5); ax.minorticks_off()
    ax.set_xticks([0.001, 0.1, 10, 600, 36000], ['1 ms', '0.1 s', '10 s', '10 min', '10 h'])
    ax.set_yticks(range(len(rows)), [f'{k}×{n}' for _, k, n in reversed(rows)])
    ax.tick_params(axis='y', length=0)
    ax.set_xlabel('time to find a rectangle of the same imbalance (log scale)')
    ax.scatter([], [], s=30, facecolor='white', edgecolor=NEUTRAL, linewidth=1.5, label='SAT, CP 2023 (reported)')
    ax.scatter([], [], s=32, color=BLUE, label='this work (median of 5 seeds)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.28), ncol=2, frameon=False, fontsize=8)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.grid(axis='x', color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    save(fig, 'speed_cp2023')


if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    rows = load()
    print('heatmap sub-label size:', heatmap(rows)); dumbbell(rows)
    print('budget cells / mean gain:', budget(rows))
    g = load_timing()
    if g:
        speed(g); speed_cp2023(g)
