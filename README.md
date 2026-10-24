# Balanced Latin Rectangles: new best-known values

A simple simulated-annealing search improves the best known imbalance of **33 of the 51**
non-square instances (8 ≤ n ≤ 13) from
[Voboril, Peruvemba Ramaswamy & Szeider, CP 2025](https://doi.org/10.4230/LIPIcs.CP.2025.36),
and matches the other 18. Every rectangle is included and can be checked independently.

Paper: [`paper/main.pdf`](paper/main.pdf) — *Simple Local Search Sets 33 New Records for Balanced Latin Rectangles*.

![New best imbalance per cell](figures/heatmap.png)

## Check the records (no build needed)

```sh
python3 code/verify.py
```

This reads every rectangle in `results/rectangles/`, checks that it is a Latin rectangle, recomputes
its imbalance with exact rational arithmetic, and compares it with `results/results.csv`.
The checker shares no code with the solver and needs only the Python standard library.
To check a single file: `python3 code/verify.py results/rectangles/k12_n13.txt`.

**Definition** ([Ramaswamy & Szeider, CP 2023](https://doi.org/10.4230/LIPIcs.CP.2023.48)): for a
k × n Latin rectangle with c_i(u) the column of symbol u in row i,
d(u,v) = Σ_i |c_i(u) − c_i(v)| and I(L) = Σ_{u<v} |d(u,v) − k(n+1)/3|.
Values like `158.6` mean 158 + 2/3, and `.3` means + 1/3, as in the literature.

## Repository layout

| Path | Contents |
|---|---|
| `results/rectangles/` | Best rectangle for every cell (`k{k}_n{n}.txt`, symbols 1..n, one row per line) |
| `results/results.csv` | Previous best vs. new value for every cell (`imbalance3` = 3·I, exact integer) |
| `results/budget.csv` | Best value per cell for each time budget |
| `results/raw/` | Raw solver output of every run |
| `data/previous_best.csv` | Baseline: CP 2025, Table 1 |
| `code/sa.c` | The search (simulated annealing, about 130 lines of C) |
| `code/verify.py` | Independent checker |
| `code/collect.py` | Verifies all raw runs and builds `results/` |
| `code/plots.py`, `code/make_tables.py` | Figures and the paper's table and numbers |
| `code/run_all.sh` | Reproduces every run (about 1.5 hours on 8 cores) |
| `paper/` | LaTeX source and PDF |

## Reproduce

```sh
cd code
./run_all.sh                 # build, run all budgets, collect, verify
python3 plots.py             # figures (needs matplotlib)
python3 make_tables.py       # paper/table.tex and paper/numbers.tex
cd ../paper && tectonic main.tex   # or: pdflatex + bibtex
```

Single run: `./sa k n seconds seed` prints `COST3 <3·I>` followed by the rectangle.
Runs measure CPU time and are single-threaded. Results depend on the seed and the machine speed,
so a rerun will not reproduce the exact rectangles, but it should give values of similar quality.

## Scope and caveats

- The new values are **upper bounds**. Optimality is open for every improved instance.
- One run per cell and time budget. No variance across seeds is reported.
- The comparison with CP 2025 uses their reported results. We did not rerun their pipeline.
- The code and paper were produced with an AI coding assistant (Claude), directed by the author.
  See the paper's "How this work was done" paragraph.
