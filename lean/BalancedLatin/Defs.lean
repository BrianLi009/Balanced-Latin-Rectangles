/-!
# Balanced Latin rectangles: definitions (core Lean only, no Mathlib)

This file is the whole trusted specification. It imports nothing beyond Lean's core library,
so the certificates in `BalancedLatin/Certificates/` depend only on these few lines and on
Lean's kernel.

We use the *point picture* of the paper. A `k × n` Latin rectangle is recorded by `col i u`,
the column (in `Fin n`) of symbol `u` (in `Fin n`) in row `i` (in `Fin k`). Symbol `u` is
then the point `x_u = (col 0 u, …, col (k-1) u)` of the grid `[n]^k`.

* Row condition: in each row, distinct symbols occupy distinct columns.
* Column condition: no column contains a symbol twice, i.e. the `k` coordinates of each point
  are distinct.

Distance and imbalance follow Díaz, Le Bras and Gomes (2017) and Peruvemba Ramaswamy and
Szeider (CP 2023):
`d(u,v) = ∑ᵢ |cᵢ(u) − cᵢ(v)|` and `I(L) = ∑_{u<v} |d(u,v) − k(n+1)/3|`.
Since `3·I(L) = ∑_{u<v} |3·d(u,v) − k(n+1)|` is an integer, we define that integer, `imb3`.
The file `BalancedLatin/Cubic.lean` defines `I` itself over `ℚ` and proves `I = imb3 / 3`.
Indices are 0-based; this shift does not change any difference of columns.
-/

namespace BalancedLatin

/-- Sum of a function on `Fin n`. (Mathlib's `List.sum_ofFn` identifies it with `∑ i, f i`.) -/
def fsum {α : Type} [Add α] [OfNat α 0] {n : Nat} (f : Fin n → α) : α := (List.ofFn f).sum

/-- `|a − b|` for natural numbers. (This is Mathlib's `Nat.dist`, by definition.) -/
def absDiff (a b : Nat) : Nat := a - b + (b - a)

/-- A `k × n` Latin rectangle, given by the column `col i u` of symbol `u` in row `i`. -/
structure LatinRect (k n : Nat) where
  /-- `col i u` is the column of symbol `u` in row `i`. -/
  col : Fin k → Fin n → Fin n
  /-- Each row is a permutation: two symbols never share a column of the same row. -/
  row_inj : ∀ i u v, col i u = col i v → u = v
  /-- Each column is free of repeats: a symbol never sits in the same column of two rows. -/
  col_inj : ∀ u i j, col i u = col j u → i = j

namespace LatinRect

variable {k n : Nat}

/-- The `ℓ₁` distance `d(u,v) = ∑ᵢ |cᵢ(u) − cᵢ(v)|` between the points of two symbols. -/
def dist (L : LatinRect k n) (u v : Fin n) : Nat :=
  fsum fun i => absDiff (L.col i u).val (L.col i v).val

/-- The integer `3·I(L) = ∑_{u<v} |3·d(u,v) − k(n+1)|`, three times the imbalance. -/
def imb3 (L : LatinRect k n) : Nat :=
  fsum fun u => fsum fun v =>
    if u < v then ((3 * L.dist u v : Int) - k * (n + 1)).natAbs else 0

end LatinRect

/-! ### Reading a rectangle in the format of the data files -/

/-- Column of symbol `u` (0-based) in a row written with symbols `1, …, n`, as in
`results/rectangles/*.txt`. Rows that are not permutations are rejected by `LatinRect`'s
conditions, which are checked separately. -/
def colOfRows {k n : Nat} (rows : List (List Nat)) (i : Fin k) (u : Fin n) : Fin n :=
  ⟨(rows.getD i.val []).idxOf (u.val + 1) % n, Nat.mod_lt _ u.pos⟩

/-- The rows read back from the columns agree with the data: the entry of row `i` in column
`colOfRows rows i u` is the symbol `u + 1`. Together with the row and column conditions this
says that the rectangle is exactly the one written in `rows`. -/
def Faithful (k n : Nat) (rows : List (List Nat)) : Prop :=
  rows.length = k ∧ (∀ r ∈ rows, r.length = n) ∧
    ∀ (i : Fin k) (u : Fin n), (rows.getD i.val []).getD (colOfRows rows i u).val 0 = u.val + 1

instance (k n : Nat) (rows : List (List Nat)) : Decidable (Faithful k n rows) := by
  unfold Faithful; exact inferInstance

end BalancedLatin
