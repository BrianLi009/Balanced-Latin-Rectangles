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
    'font.family': 'serif', 'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
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


def heatmap(rows):
    ns = sorted({r['n'] for r in rows}); ks = list(range(2, max(r['k'] for r in rows) + 1))
    cmap = LinearSegmentedColormap.from_list('seq', BLUE_RAMP)
    vmax = max((r['p3'] - r['c3']) / r['p3'] for r in rows if r['c3'] is not None and r['p3'])
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    for r in rows:
        x, y = ks.index(r['k']), ns.index(r['n'])
        if r['c3'] is None:
            continue
        gain = (r['p3'] - r['c3']) / r['p3'] if r['p3'] else 0.0
        face = cmap(gain / vmax) if gain > 0 else '#f0efec'
        ax.add_patch(plt.Rectangle((x - 0.5 + 0.03, y - 0.5 + 0.03), 0.94, 0.94, facecolor=face,
                                   edgecolor='white', linewidth=1.0))
        dark = gain / vmax > 0.55
        ink = 'white' if dark else INK
        if gain > 0:
            ax.text(x, y + 0.14, r['new'], ha='center', va='center', fontsize=7.2, color=ink, weight='bold')
            ax.text(x, y - 0.20, f"was {r['previous']}", ha='center', va='center', fontsize=5.4,
                    color='white' if dark else INK2)
        else:
            ax.text(x, y, r['new'], ha='center', va='center', fontsize=7.2, color=INK2)
    ax.set_xlim(-0.5, len(ks) - 0.5); ax.set_ylim(-0.5, len(ns) - 0.5)
    ax.set_xticks(range(len(ks)), ks); ax.set_yticks(range(len(ns)), ns)
    ax.set_xlabel('rows $k$'); ax.set_ylabel('columns / symbols $n$')
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100 * vmax))
    cb = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label('reduction vs. previous best (%)', color=INK2); cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, length=0)
    save(fig, 'heatmap')


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


if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    rows = load()
    heatmap(rows); dumbbell(rows)
    print('budget cells / mean gain:', budget(rows))
