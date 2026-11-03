import Mathlib.Logic.Equiv.Fintype
import Mathlib.Data.Fintype.EquivFin
import BalancedLatin.Cubic

/-!
# Is the specification the right one?

Checks that guard against verifying the wrong statement.

* `arrayEquiv`: `LatinRect k n` is in bijection with Latin rectangles as the paper defines
  them, i.e. arrays `A i j` (row `i`, column `j`) whose rows are permutations of the symbols and
  whose columns have no repeats. Under it, `col i u` is the column of symbol `u` in row `i`
  (`ofArray_col`), which is `cᵢ(u)` in the paper.
* `nonempty_of_le`: for every `k ≤ n` there is a `k × n` Latin rectangle (the cyclic one). So
  `LatinRect` is not accidentally empty, and the universally quantified theorems of
  `Cubic.lean` are not vacuous.
* `cubic_lower_bound_ceil`: the pigeonhole theorem exactly as stated in the paper, with
  `B = ⌈n/s⌉^k`.

Separately, `Certificates/Published.lean` checks that `imb3` reproduces the imbalances that
Peruvemba Ramaswamy–Szeider (CP 2023) and Voboril et al. (CP 2025) report for the 14 rectangles
printed in their papers. This validates `dist` and `imb3` against the literature's definition.
-/

namespace BalancedLatin

variable {k n : ℕ}

/-- A Latin rectangle as defined in the paper: `A i j` is the symbol in row `i` and column `j`.
Every row is a permutation of the symbols, and no column repeats a symbol. -/
def IsLatinArray (A : Fin k → Fin n → Fin n) : Prop :=
  (∀ i, Function.Bijective (A i)) ∧ ∀ j i i', A i j = A i' j → i = i'

namespace LatinRect

theorem ext' {L L' : LatinRect k n} (h : L.col = L'.col) : L = L' := by
  cases L; cases L'; cases h; rfl

theorem col_bijective (L : LatinRect k n) (i : Fin k) : Function.Bijective (L.col i) :=
  (L.row_injective i).bijective_of_finite

/-- The array of a rectangle: `toArray L i j` is the symbol in row `i`, column `j`. -/
noncomputable def toArray (L : LatinRect k n) : Fin k → Fin n → Fin n :=
  fun i => (Equiv.ofBijective _ (L.col_bijective i)).symm

theorem col_toArray (L : LatinRect k n) (i : Fin k) (j : Fin n) : L.col i (L.toArray i j) = j :=
  Equiv.ofBijective_apply_symm_apply _ _ j

theorem toArray_col (L : LatinRect k n) (i : Fin k) (u : Fin n) : L.toArray i (L.col i u) = u :=
  Equiv.ofBijective_symm_apply_apply _ _ u

theorem toArray_isLatin (L : LatinRect k n) : IsLatinArray L.toArray := by
  refine ⟨fun i => (Equiv.ofBijective _ (L.col_bijective i)).symm.bijective, fun j i i' h => ?_⟩
  apply L.col_inj (L.toArray i j)
  rw [col_toArray, h, col_toArray]

end LatinRect

/-- The rectangle of an array: `col i u` is the column of `u` in row `i`. -/
noncomputable def ofArray (A : Fin k → Fin n → Fin n) (h : IsLatinArray A) : LatinRect k n where
  col i := (Equiv.ofBijective _ (h.1 i)).symm
  row_inj i u v huv := (Equiv.ofBijective _ (h.1 i)).symm.injective huv
  col_inj u i i' hii := by
    have h1 : A i ((Equiv.ofBijective _ (h.1 i)).symm u) = u :=
      Equiv.ofBijective_apply_symm_apply _ _ u
    have h2 : A i' ((Equiv.ofBijective _ (h.1 i')).symm u) = u :=
      Equiv.ofBijective_apply_symm_apply _ _ u
    refine h.2 ((Equiv.ofBijective _ (h.1 i)).symm u) i i' ?_
    change (Equiv.ofBijective _ (h.1 i)).symm u = (Equiv.ofBijective _ (h.1 i')).symm u at hii
    rw [h1, hii, h2]

/-- In the rectangle of an array, the column of the symbol `A i j` in row `i` is `j`: this is
the paper's `cᵢ(u)`. -/
theorem ofArray_col (A : Fin k → Fin n → Fin n) (h : IsLatinArray A) (i : Fin k) (j : Fin n) :
    (ofArray A h).col i (A i j) = j :=
  Equiv.ofBijective_symm_apply_apply _ _ j

/-- `LatinRect k n` is in bijection with the Latin arrays of the paper. -/
noncomputable def arrayEquiv : {A : Fin k → Fin n → Fin n // IsLatinArray A} ≃ LatinRect k n where
  toFun A := ofArray A.1 A.2
  invFun L := ⟨L.toArray, L.toArray_isLatin⟩
  left_inv := by
    rintro ⟨A, h⟩
    apply Subtype.ext
    funext i j
    show (ofArray A h).toArray i j = A i j
    apply (ofArray A h).row_injective i
    rw [LatinRect.col_toArray, ofArray_col]
  right_inv L := by
    apply LatinRect.ext'
    funext i u
    have := ofArray_col L.toArray L.toArray_isLatin i (L.col i u)
    rw [L.toArray_col] at this
    exact this

/-- The cyclic rectangle `A i j = j + i` shows that `LatinRect k n` is inhabited for `k ≤ n`. -/
theorem nonempty_of_le (h : k ≤ n) : Nonempty (LatinRect k n) := by
  rcases Nat.eq_zero_or_pos n with rfl | hn
  · obtain rfl : k = 0 := by omega
    exact ⟨⟨fun i => i.elim0, fun i => i.elim0, fun u => u.elim0⟩⟩
  have : NeZero n := ⟨by omega⟩
  let A : Fin k → Fin n → Fin n := fun i j => j + Fin.castLE h i
  refine ⟨ofArray A ⟨fun i => (add_left_injective _).bijective_of_finite, fun j i i' hii => ?_⟩⟩
  exact Fin.castLE_injective h (add_left_cancel hii)

/-- The pigeonhole theorem exactly as stated in the paper, with `B = ⌈n/s⌉^k`. -/
theorem LatinRect.cubic_lower_bound_ceil (L : LatinRect k n) (s : ℕ) (hs : 1 ≤ s)
    (ht : (k : ℚ) * (s - 1) ≤ k * (n + 1) / 3) :
    (n : ℚ) * (n / (⌈(n : ℚ) / s⌉₊ : ℚ) ^ k - 1) * (k * (n + 1) / 3 - k * (s - 1))
      ≤ L.imbalance := by
  have hM : n ≤ ⌈(n : ℚ) / s⌉₊ * s := by
    have hsq : (0 : ℚ) < s := by exact_mod_cast hs
    have := Nat.le_ceil ((n : ℚ) / s)
    rw [div_le_iff₀ hsq] at this
    exact_mod_cast this
  exact L.cubic_lower_bound s _ (by omega) hM ht

end BalancedLatin
