# Lean 4 formalization

Machine-checked results from *Leaving the Cyclic Orbit* (`../arxiv/main.pdf`).

| what | file | depends on |
|---|---|---|
| Specification: Latin rectangle, distance `d`, `3·I` | `BalancedLatin/Defs.lean` (74 lines) | Lean core only |
| All 62 reported rectangles: Latin and `3·I` = claimed value | `BalancedLatin/Certificates/*.lean` (generated) | `Defs.lean` only |
| Equation (1), the pigeonhole theorem, the cubic law, the constants `c_k` | `BalancedLatin/Cubic.lean` | Mathlib |
| Map from statements in the paper to Lean names | `BalancedLatin/Paper.lean` | everything |

## Build

```sh
cd lean
lake exe cache get   # downloads prebuilt Mathlib (needed only for Cubic.lean)
lake build
lake env lean Audit.lean   # prints the axioms each headline theorem uses
```

A clean build of this project takes about 30 s on an Apple M3 laptop, once Mathlib is downloaded.
Toolchain `leanprover/lean4:v4.35.0-rc2`; the Mathlib revision is pinned in `lakefile.toml`.

## What is certified, and what you have to trust

**Certificates (upper bounds).** For each rectangle `code/make_lean.py` copies the rows from
`results/rectangles/*.txt` or `results/k2_large/*.txt` verbatim into a Lean list. Three facts are
checked by `decide +kernel`, i.e. by evaluation in Lean's kernel:

1. the rows form a Latin rectangle (`row_inj`, `col_inj`);
2. the columns are read faithfully from the rows (`faithful_*`);
3. `imb3 = 3·I` equals the claimed value (`imb3_*`).

`#print axioms` reports only `propext` for these theorems. There is no `native_decide` and no
`sorry`, so neither the Lean compiler nor Mathlib is trusted: only the kernel and the 74 lines
of `Defs.lean`, which are written directly from the definition in the literature:

```lean
structure LatinRect (k n : Nat) where
  col : Fin k → Fin n → Fin n               -- column of symbol u in row i
  row_inj : ∀ i u v, col i u = col i v → u = v
  col_inj : ∀ u i j, col i u = col j u → i = j

def dist (L : LatinRect k n) (u v : Fin n) : Nat :=
  fsum fun i => absDiff (L.col i u).val (L.col i v).val          -- ∑ᵢ |cᵢ(u) − cᵢ(v)|

def imb3 (L : LatinRect k n) : Nat :=                              -- 3·∑_{u<v} |d(u,v) − k(n+1)/3|
  fsum fun u => fsum fun v =>
    if u < v then ((3 * L.dist u v : Int) - k * (n + 1)).natAbs else 0
```

`Cubic.lean` proves `imbalance = imb3 / 3` for the imbalance defined over `ℚ`, so the
certificates and the theorems talk about the same quantity.

**Cubic law (lower and upper bounds).** `cubic_lower_bound` is the pigeonhole theorem of the paper (`thm:cubic`). It is
slightly stronger: it needs only `k(s−1) ≤ t`, and any number `M` of intervals per axis with
`n ≤ M·s`. `eventually_lower_bound` gives `I ≥ (k·m^{-k}·(1/3 − 1/m) − ε)·n³` for all large `n`,
i.e. `liminf min I/n³ ≥ c_k`, and `imbalance_le` gives `I ≤ k·n³/3`. These use the standard
axioms `propext`, `Classical.choice` and `Quot.sound`.

## Not formalized

* Optimality of `3 × 9` (`thm:3x9`) rests on the C branch and bound (`code/bnb.c`). A verified
  checker for it is future work.
* The row-group proposition, the permuton limit and the equilateral-set remark.

## Regenerating the certificates

```sh
python3 code/make_lean.py
```

This cross-checks every claimed value against `code/verify.py` before writing any Lean file.
CI (`.github/workflows/lean.yml`) rebuilds the project, runs the axiom audit, and checks that the
committed certificates match the data files.
