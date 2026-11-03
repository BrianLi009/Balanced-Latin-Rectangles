"""Figures for the arXiv paper (arxiv/main.tex).

Usage:  python code/arxiv_figures.py          (run from the repository root)
Writes vector PDFs to arxiv/figures/.  Needs numpy, matplotlib and sympy.
"""
import csv
import glob
import os
import re
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "arxiv", "figures")
os.makedirs(OUT, exist_ok=True)

BLUE = "#2c6fd1"
DARK = "#1b2a41"
GREY = "#b9b9b4"
LIGHT = "#e6e6e1"
RED = "#c8553d"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#555555",
    "axes.linewidth": 0.8,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
})


# ---------------------------------------------------------------- helpers
def read_rect(path):
    rows = []
    for line in open(path):
        tok = line.split()
        if tok and tok[0].isdigit():
            rows.append([int(x) for x in tok])
    return rows


def positions(R):
    """pos[i][u] = column (0-based) of symbol u (0-based) in row i."""
    pos = []
    for r in R:
        p = [0] * len(r)
        for j, s in enumerate(r):
            p[s - 1] = j
        pos.append(p)
    return pos


def cost3(R):
    k, n = len(R), len(R[0])
    pos = positions(R)
    t3 = k * (n + 1)
    return sum(abs(3 * sum(abs(p[u] - p[v]) for p in pos) - t3)
               for u, v in combinations(range(n), 2))


def fmt(c3):
    return f"{c3 // 3}.{'036'[c3 % 3]}"


# ------------------------------------------------- Fig 1: the 3 x 9 optimum
def fig_optimum():
    R = read_rect(os.path.join(ROOT, "results", "rectangles", "k3_n9.txt"))
    k, n = len(R), len(R[0])
    pos = positions(R)
    t = k * (n + 1) / 3
    D = np.array([[sum(abs(p[u] - p[v]) for p in pos) for v in range(n)] for u in range(n)], float)
    dev = D - t
    np.fill_diagonal(dev, np.nan)

    fig = plt.figure(figsize=(6.8, 2.3))
    ax = fig.add_axes([0.0, 0.22, 0.36, 0.52])
    ax2 = fig.add_axes([0.42, 0.10, 0.25, 0.78])
    axc = fig.add_axes([0.675, 0.18, 0.010, 0.62])
    ax3 = fig.add_axes([0.80, 0.20, 0.20, 0.66])

    cmap = plt.get_cmap("twilight_shifted")
    cols = [cmap(0.08 + 0.84 * u / (n - 1)) for u in range(n)]
    for i, r in enumerate(R):
        for j, s in enumerate(r):
            ax.add_patch(plt.Rectangle((j, k - 1 - i), 0.94, 0.94, color=cols[s - 1], lw=0))
            lum = np.dot(cols[s - 1][:3], [0.299, 0.587, 0.114])
            ax.text(j + 0.47, k - 1 - i + 0.47, str(s), ha="center", va="center",
                    color="white" if lum < 0.55 else DARK, fontsize=10)
    ax.set_xlim(-0.05, n); ax.set_ylim(-0.05, k); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(r"(a) an optimal $3\times 9$ rectangle, $I=56$", loc="left", pad=14)

    norm = TwoSlopeNorm(vmin=-6, vcenter=0, vmax=6)
    cm = LinearSegmentedColormap.from_list("dev", [RED, "#f3efe9", BLUE])
    im = ax2.imshow(dev, cmap=cm, norm=norm)
    ax2.set_xticks(range(n)); ax2.set_yticks(range(n))
    ax2.set_xticklabels(range(1, n + 1), fontsize=7); ax2.set_yticklabels(range(1, n + 1), fontsize=7)
    ax2.tick_params(length=0)
    for s in ax2.spines.values():
        s.set_visible(False)
    ax2.set_title(r"(b) $d(u,v)-t$,  $t=10$", loc="left", pad=6)
    cb = fig.colorbar(im, cax=axc, ticks=[-6, -3, 0, 3, 6])
    cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7, length=0)

    devs = dev[np.triu_indices(n, 1)]
    vals, cnts = np.unique(devs, return_counts=True)
    ax3.bar(vals, cnts, width=0.8, color=[BLUE if v > 0 else RED if v < 0 else DARK for v in vals])
    ax3.set_xticks([-6, -3, 0, 3, 6])
    ax3.spines["left"].set_visible(False)
    ax3.tick_params(axis="y", length=0, labelsize=7)
    ax3.tick_params(axis="x", labelsize=7)
    ax3.set_yticks([0, 5, 10])
    ax3.set_title("(c) the 36 pairs", loc="left", pad=6)
    ax3.set_xlabel(r"$d-t$")
    fig.savefig(os.path.join(OUT, "optimum3x9.pdf"))
    plt.close(fig)


# ------------------------------------------- Fig 2: the row group of records
def row_group_kind(R):
    """Row group <r_i r_1^{-1}>: returns ('S'|'A'|order as text, order). Needs sympy."""
    from math import factorial
    from sympy.combinatorics import Permutation, PermutationGroup
    n = len(R[0])
    gens = []
    for r in R[1:]:
        p = [0] * n
        for j in range(n):
            p[R[0][j] - 1] = r[j] - 1   # symbol in row 1 -> symbol in row i, same column
        gens.append(Permutation(p))
    o = PermutationGroup(gens).order()
    if o == factorial(n):
        return "S", o
    if 2 * o == factorial(n):
        return "A", o
    return str(o), o


def fig_rowgroups():
    res = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "results.csv"))):
        k, n = int(r["k"]), int(r["n"])
        res[(k, n)] = (r["status"], float(r["previous"]), float(r["new"]))
    fig, ax = plt.subplots(figsize=(6.4, 2.75))
    cm = LinearSegmentedColormap.from_list("imp", ["#dce8f8", BLUE, "#123a7a"])
    for (k, n), (st, old, new) in res.items():
        R = read_rect(os.path.join(ROOT, "results", "rectangles", f"k{k}_n{n}.txt"))
        lab, o = row_group_kind(R)
        x, y = k, n
        if st == "improved":
            g = (old - new) / old
            fc = cm(min(1.0, g / 0.40))
            tc = "white" if g > 0.17 else DARK
        else:
            fc, tc = LIGHT, "#555555"
        ax.add_patch(plt.Rectangle((x - 0.46, y - 0.44), 0.92, 0.88, color=fc, lw=0))
        if lab in ("S", "A"):
            txt = rf"$\mathrm{{{lab}}}_{{{n}}}$"
            fs = 9
        else:
            txt = lab
            fs = 6.5 if len(lab) > 3 else 8
        ax.text(x, y, txt, ha="center", va="center", color=tc, fontsize=fs)
    ax.set_xlim(1.4, 12.6); ax.set_ylim(13.6, 7.4)
    ax.set_xticks(range(2, 13)); ax.set_yticks(range(8, 14))
    ax.set_xlabel(r"rows $k$"); ax.set_ylabel(r"symbols $n$")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    sm = plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(0, 40))
    cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("improvement over previous best (%)", fontsize=8)
    cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7, length=0)
    fig.savefig(os.path.join(OUT, "rowgroups.pdf"))
    plt.close(fig)


# ------------------------------------------ Fig 3: pigeonhole + limit shapes
def k2_files():
    out = {}
    for f in glob.glob(os.path.join(ROOT, "results", "k2_large", "k2_n*.txt")):
        n = int(re.search(r"n(\d+)", f).group(1))
        out[n] = f
    return out


def fig_geometry():
    files = k2_files()
    shapes = [n for n in (24, 32, 48, 64) if n in files]
    fig = plt.figure(figsize=(6.6, 1.85))
    w = 1.0 / (len(shapes) + 1.25)
    # (a) pigeonhole picture for n = 16, m = 4 boxes per side
    R = read_rect(files[16])
    n = 16
    pos = positions(R)
    ax = fig.add_axes([0.0, 0.0, w * 1.1, 0.86])
    m = 4
    for a in range(1, m):
        ax.axvline(a * n / m - 0.5, color=GREY, lw=0.7)
        ax.axhline(a * n / m - 0.5, color=GREY, lw=0.7)
    pts = [(pos[0][u], pos[1][u]) for u in range(n)]
    box = lambda p: (int(p[0] // (n / m)), int(p[1] // (n / m)))
    for u, v in combinations(range(n), 2):
        if box(pts[u]) == box(pts[v]):
            ax.plot([pts[u][0], pts[v][0]], [pts[u][1], pts[v][1]], color=RED, lw=1.1, zorder=2)
    ax.scatter(*zip(*pts), s=14, color=DARK, zorder=3, lw=0)
    ax.set_xlim(-0.5, n - 0.5); ax.set_ylim(-0.5, n - 0.5); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_color("#888888")
    ax.set_title(rf"(a) $2\times16$, $I={fmt(cost3(R))}$", loc="left", fontsize=8.5)
    for i, n in enumerate(shapes):
        R = read_rect(files[n])
        pos = positions(R)
        ax = fig.add_axes([w * (1.25 + i), 0.0, w * 0.92, 0.86])
        x = (np.array(pos[0]) + 0.5) / n
        y = (np.array(pos[1]) + 0.5) / n
        ax.scatter(x, y, s=max(3, 200 / n), color=BLUE, lw=0)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(True); s.set_color("#888888")
        c = cost3(R) / 3 / n ** 3
        ax.set_title(rf"$n={n}$,  $I/n^3={c:.3f}$", loc="left", fontsize=8.5)
        if i == 0:
            ax.text(-0.02, 1.13, "(b)", transform=ax.transAxes, fontsize=8.5, ha="right")
    fig.savefig(os.path.join(OUT, "geometry.pdf"))
    plt.close(fig)


# ---------------------------------------------------- Fig 4: the cubic law
EXACT2 = {2: 0, 3: 4, 4: 8, 5: 24, 6: 48, 7: 84, 8: 120, 9: 196, 10: 276, 11: 372,
          12: 504, 13: 656}  # 3I, proven optimal (n<=11 our B&B; 12,13 Mirka et al.)
MIRKA_LB = {14: 201.57, 15: 252.66, 16: 273.82, 17: 252.0, 18: 402.66, 19: 465.33, 20: 155.0}
MIRKA_UB = {14: 268.0, 15: 345.33, 16: 427.33, 17: 508.0, 18: 617.33, 19: 732.0, 20: 816.0}


def floor_bound(n, k=2):
    """Best bound of Theorem 1 over m (equal-side boxes, side ceil(n/m))."""
    best = 0.0
    for m in range(1, n + 1):
        s = -(-n // m)
        B = (-(-n // s)) ** k
        val = n * (n / B - 1) * (k * (n + 1) / 3 - k * (s - 1))
        if n / B > 1 and k * (n + 1) / 3 > k * (s - 1):
            best = max(best, val)
    return best


def fig_cubic():
    files = k2_files()
    fig, ax = plt.subplots(figsize=(6.0, 2.7))
    ns = np.arange(3, 14)
    ax.plot(ns, [EXACT2[n] / 3 / n ** 3 for n in ns], "o", color=DARK, ms=4.2,
            label="proven optimum", zorder=4)
    for n in MIRKA_LB:
        ax.plot([n, n], [MIRKA_LB[n] / n ** 3, MIRKA_UB[n] / n ** 3], color=GREY, lw=2.2,
                solid_capstyle="round", zorder=1)
    ax.plot([], [], color=GREY, lw=2.2, label="bounds of Mirka et al. (6 h MIP)")
    big = sorted(files)
    big = [n for n in big if n >= 14]
    ax.plot(big, [cost3(read_rect(files[n])) / 3 / n ** 3 for n in big], "o", color=BLUE, ms=4.2,
            label="this work (annealing, 2 min)", zorder=5)
    xs = np.arange(3, 70)
    fb = [floor_bound(n) / n ** 3 for n in xs]
    ax.plot(xs, fb, color=RED, lw=1.2, label="pigeonhole bound at each $n$")
    c2 = 4 / 375
    ax.axhline(0.13604, color="#888888", lw=0.8, ls=(0, (1, 2)))
    ax.text(68, 0.1385, "random second row", ha="right", va="bottom", fontsize=7.5, color="#666666")
    ax.axhline(0.1196, color=BLUE, lw=0.8, ls=(0, (4, 3)))
    ax.text(3.0, 0.1215, r"permuton of the $2\times64$ rectangle: $C\approx0.120$", ha="left",
            va="bottom", fontsize=7.5, color=BLUE)
    ax.axhline(c2, color=RED, lw=0.8, ls=(0, (4, 3)))
    ax.text(68, c2 + 0.003, r"$c_2=4/375$", ha="right", va="bottom", fontsize=7.5, color=RED)
    ax.set_xscale("log")
    ax.set_xticks([3, 4, 6, 8, 12, 16, 24, 32, 48, 64])
    ax.set_xticklabels([3, 4, 6, 8, 12, 16, 24, 32, 48, 64])
    ax.minorticks_off()
    ax.set_xlim(2.8, 70); ax.set_ylim(-0.003, 0.16)
    ax.set_xlabel(r"$n$ (log scale)"); ax.set_ylabel(r"$I/n^3$ for $k=2$")
    ax.grid(axis="y", color="#eeeeee", lw=0.6)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7.5, handlelength=1.6, columnspacing=1.5)
    fig.savefig(os.path.join(OUT, "cubic.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig_optimum()
    fig_rowgroups()
    fig_geometry()
    fig_cubic()
    print("figures written to", OUT)
