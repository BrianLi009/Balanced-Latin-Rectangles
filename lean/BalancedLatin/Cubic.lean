import Mathlib.Algebra.Order.Chebyshev
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.Floor.Semiring
import Mathlib.Data.Rat.Floor
import Mathlib.Data.Nat.Dist
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Order.Filter.AtTopBot.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.GCongr
import Mathlib.Tactic.IntervalCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring
import BalancedLatin.Defs

/-!
# The cubic law

For a `k × n` Latin rectangle `L` we prove, with `t = k(n+1)/3`:

* `imbalance_eq_imb3`: `I(L) = imb3(L)/3`, linking the core definition of
  `BalancedLatin.Defs` to the imbalance over `ℚ`.
* `sum_dist`: the distances sum to `k·(n−1)·n·(n+1)/3` over ordered pairs, so `t` is the
  average distance.
* `imbalance_eq_two_mul_sum_pos`: `I(L) = 2·∑_{u<v} (t − d(u,v))⁺` (equation (1) of the paper).
* `cubic_lower_bound` (the pigeonhole theorem of the paper, `thm:cubic`): if every axis of `[n]^k` is cut into `M`
  intervals of `s` consecutive values (`n ≤ M·s`), then
  `I(L) ≥ n·(n/M^k − 1)·(t − k(s−1))` whenever `k(s−1) ≤ t`.
* `lower_bound_explicit`, `eventually_lower_bound`: for every `m ≥ 3`,
  `I(L) ≥ k·(1/3 − 1/m)·(n³/m^k − n²)`, so `liminf min I / n³ ≥ k·m^{-k}·(1/3 − 1/m)`.
* `imbalance_le`: `I(L) ≤ k·n³/3`.
* `lowerConst_two_le`, `lowerConst_le_four`: the best constant is `4/375` for `k = 2`
  (at `m = 5`) and `k/(12·4^k)` for `k ≥ 3` (at `m = 4`).
-/

open Finset

namespace BalancedLatin

variable {k n : ℕ}

theorem fsum_eq_sum {β : Type} [AddCommMonoid β] {m : ℕ} (f : Fin m → β) :
    fsum f = ∑ i, f i := List.sum_ofFn

namespace LatinRect

/-- Column of `u` in row `i`, as a natural number. -/
abbrev c (L : LatinRect k n) (i : Fin k) (u : Fin n) : ℕ := (L.col i u).val

theorem dist_eq (L : LatinRect k n) (u v : Fin n) :
    L.dist u v = ∑ i, Nat.dist (L.c i u) (L.c i v) := fsum_eq_sum _

theorem dist_self (L : LatinRect k n) (u : Fin n) : L.dist u u = 0 := by
  simp [dist_eq, Nat.dist_self]

theorem dist_comm (L : LatinRect k n) (u v : Fin n) : L.dist u v = L.dist v u := by
  simp [dist_eq, Nat.dist_comm]

theorem row_injective (L : LatinRect k n) (i : Fin k) : Function.Injective (L.col i) :=
  fun u v h => L.row_inj i u v h

/-- The target distance `t = k(n+1)/3`. -/
def target (k n : ℕ) : ℚ := k * (n + 1) / 3

/-- The imbalance `I(L) = ∑_{u<v} |d(u,v) − k(n+1)/3|`, over `ℚ`. -/
def imbalance (L : LatinRect k n) : ℚ :=
  ∑ u, ∑ v, if u < v then |(L.dist u v : ℚ) - target k n| else 0

theorem imbalance_eq_imb3 (L : LatinRect k n) : L.imbalance = L.imb3 / 3 := by
  rw [imbalance, imb3, fsum_eq_sum, Nat.cast_sum, Finset.sum_div]
  refine Finset.sum_congr rfl fun u _ => ?_
  rw [fsum_eq_sum, Nat.cast_sum, Finset.sum_div]
  refine Finset.sum_congr rfl fun v _ => ?_
  split_ifs
  · rw [Nat.cast_natAbs, Int.cast_abs, target]
    push_cast
    rw [eq_div_iff (by norm_num : (3 : ℚ) ≠ 0)]
    rw [show (3 : ℚ) * L.dist u v - k * (n + 1) = 3 * (L.dist u v - k * (n + 1) / 3) by ring,
      abs_mul, abs_of_pos (by norm_num : (0 : ℚ) < 3)]
    ring
  · simp

theorem imbalance_nonneg (L : LatinRect k n) : 0 ≤ L.imbalance := by
  unfold imbalance
  refine Finset.sum_nonneg fun u _ => Finset.sum_nonneg fun v _ => ?_
  split_ifs <;> positivity

/-! ### The average distance -/

/-- `∑_{a<n} (n − a) = n(n+1)/2`. -/
theorem sum_range_sub (n : ℕ) : ∑ a ∈ range n, ((n : ℚ) - a) = n * (n + 1) / 2 := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [sum_range_succ]
    have : ∑ a ∈ range n, (((n + 1 : ℕ) : ℚ) - a) = ∑ a ∈ range n, (((n : ℚ) - a) + 1) := by
      refine sum_congr rfl fun a _ => ?_; push_cast; ring
    rw [this, sum_add_distrib, ih]
    simp
    ring

theorem dist_cast_of_le {a b : ℕ} (h : a ≤ b) : (Nat.dist a b : ℚ) = b - a := by
  rw [Nat.dist_eq_sub_of_le h, Nat.cast_sub h]

/-- `∑_{a,b<n} |a − b| = (n−1)n(n+1)/3`. -/
theorem sum_range_dist (n : ℕ) :
    ∑ a ∈ range n, ∑ b ∈ range n, (Nat.dist a b : ℚ) = (n - 1) * n * (n + 1) / 3 := by
  induction n with
  | zero => simp
  | succ n ih =>
    simp only [sum_range_succ]
    rw [sum_add_distrib, ih]
    have h1 : ∑ a ∈ range n, (Nat.dist a n : ℚ) = n * (n + 1) / 2 := by
      rw [← sum_range_sub]
      exact sum_congr rfl fun a ha => dist_cast_of_le (mem_range.1 ha).le
    have h2 : ∑ b ∈ range n, (Nat.dist n b : ℚ) = n * (n + 1) / 2 := by
      rw [← h1]; exact sum_congr rfl fun b _ => by rw [Nat.dist_comm]
    rw [h1, h2, Nat.dist_self]
    push_cast
    ring

theorem sum_fin_dist (n : ℕ) :
    ∑ a : Fin n, ∑ b : Fin n, (Nat.dist a b : ℚ) = (n - 1) * n * (n + 1) / 3 := by
  rw [← sum_range_dist, ← Fin.sum_univ_eq_sum_range (fun a => ∑ b ∈ range n, (Nat.dist a b : ℚ)) n]
  exact sum_congr rfl fun a _ => Fin.sum_univ_eq_sum_range (fun b => (Nat.dist a b : ℚ)) n

/-- The distances sum to `k(n−1)n(n+1)/3` over ordered pairs: each row is a permutation, so it
contributes `∑_{a,b} |a − b|`. -/
theorem sum_dist (L : LatinRect k n) :
    ∑ u, ∑ v, (L.dist u v : ℚ) = k * ((n - 1) * n * (n + 1) / 3) := by
  have hswap : ∑ u, ∑ v, (L.dist u v : ℚ)
      = ∑ i, ∑ u, ∑ v, (Nat.dist (L.c i u) (L.c i v) : ℚ) := by
    simp_rw [dist_eq, Nat.cast_sum]
    calc _ = ∑ u, ∑ i, ∑ v, (Nat.dist (L.c i u) (L.c i v) : ℚ) :=
          sum_congr rfl fun u _ => Finset.sum_comm
      _ = _ := Finset.sum_comm
  rw [hswap]
  have hrow : ∀ i : Fin k, ∑ u : Fin n, ∑ v : Fin n, (Nat.dist (L.c i u) (L.c i v) : ℚ)
      = (n - 1) * n * (n + 1) / 3 := by
    intro i
    have hb : Function.Bijective (L.col i) := (L.row_injective i).bijective_of_finite
    rw [← sum_fin_dist]
    refine Fintype.sum_bijective _ hb _ _ fun u => ?_
    exact Fintype.sum_bijective _ hb _ _ fun v => rfl
  rw [sum_congr rfl fun i _ => hrow i, sum_const, card_univ, Fintype.card_fin, nsmul_eq_mul]

/-! ### Equation (1): imbalance comes from the pairs that are too close -/

/-- For a symmetric `g`, `2·∑_{u<v} g(u,v) = ∑_{u≠v} g(u,v)`. -/
theorem two_mul_sum_lt {m : ℕ} (g : Fin m → Fin m → ℚ) (hg : ∀ u v, g u v = g v u) :
    2 * ∑ u, ∑ v, (if u < v then g u v else 0) = ∑ u, ∑ v, if u ≠ v then g u v else 0 := by
  have h : ∑ u, ∑ v, (if u < v then g u v else 0) = ∑ u, ∑ v, (if v < u then g u v else 0) := by
    rw [Finset.sum_comm]
    exact sum_congr rfl fun u _ => sum_congr rfl fun v _ => by rw [hg v u]
  rw [two_mul]
  nth_rewrite 2 [h]
  rw [← sum_add_distrib]
  refine sum_congr rfl fun u _ => ?_
  rw [← sum_add_distrib]
  refine sum_congr rfl fun v _ => ?_
  rcases lt_trichotomy u v with huv | rfl | huv
  · simp [huv, huv.ne, not_lt.2 huv.le]
  · simp
  · simp [huv, huv.ne', not_lt.2 huv.le]

/-- The deviations `d(u,v) − t` sum to zero: `t` is the average distance. -/
theorem sum_dev (L : LatinRect k n) :
    ∑ u, ∑ v, (if u ≠ v then (L.dist u v : ℚ) - target k n else 0) = 0 := by
  have e : ∀ u v, (if u ≠ v then (L.dist u v : ℚ) - target k n else 0)
      = ((L.dist u v : ℚ) - target k n) - if u = v then (L.dist u v : ℚ) - target k n else 0 := by
    intro u v; by_cases h : u = v <;> simp [h]
  simp_rw [e, sum_sub_distrib, Finset.sum_ite_eq, mem_univ, ite_true, dist_self]
  rw [sum_dist]
  simp only [sum_const, card_univ, Fintype.card_fin, nsmul_eq_mul, target]
  push_cast
  ring

theorem abs_eq_add_two_mul_max (x : ℚ) : |x| = x + 2 * max (-x) 0 := by
  rcases le_total 0 x with h | h
  · rw [abs_of_nonneg h, max_eq_right (by linarith)]; ring
  · rw [abs_of_nonpos h, max_eq_left (by linarith)]; ring

/-- `I(L) = ∑_{u≠v} (t − d(u,v))⁺`, summing over ordered pairs. -/
theorem imbalance_eq_sum_pos (L : LatinRect k n) :
    L.imbalance = ∑ u, ∑ v, if u ≠ v then max (target k n - L.dist u v) 0 else 0 := by
  have h2 : 2 * L.imbalance = ∑ u, ∑ v, if u ≠ v then |(L.dist u v : ℚ) - target k n| else 0 :=
    two_mul_sum_lt _ fun u v => by rw [dist_comm]
  have h3 : ∀ u v, (if u ≠ v then |(L.dist u v : ℚ) - target k n| else 0)
      = (if u ≠ v then (L.dist u v : ℚ) - target k n else 0)
        + 2 * (if u ≠ v then max (target k n - L.dist u v) 0 else 0) := by
    intro u v
    split_ifs
    · rw [abs_eq_add_two_mul_max, neg_sub]
    · simp
  simp_rw [h3, sum_add_distrib, ← mul_sum] at h2
  rw [sum_dev] at h2
  linarith

/-- **Equation (1) of the paper**: `I(L) = 2·∑_{u<v} (t − d(u,v))⁺`. -/
theorem imbalance_eq_two_mul_sum_pos (L : LatinRect k n) :
    L.imbalance = 2 * ∑ u, ∑ v, if u < v then max (target k n - L.dist u v) 0 else 0 := by
  rw [two_mul_sum_lt _ fun u v => by rw [dist_comm], imbalance_eq_sum_pos]

/-! ### The pigeonhole bound (`thm:cubic` in the paper) -/

theorem nat_dist_lt_of_div_eq {a b s : ℕ} (hs : 0 < s) (h : a / s = b / s) :
    Nat.dist a b < s := by
  have ha := Nat.div_add_mod a s
  have hb := Nat.div_add_mod b s
  have ha' := Nat.mod_lt a hs
  have hb' := Nat.mod_lt b hs
  rw [h] at ha
  unfold Nat.dist
  generalize s * (b / s) = q at ha hb
  omega

/-- **Pigeonhole bound (`thm:cubic`).** Cut every axis of `[n]^k` into `M` intervals of `s`
consecutive values (`n ≤ M·s`, e.g. `M = ⌈n/s⌉`), giving `B = M^k` boxes. Then
`I(L) ≥ n·(n/B − 1)·(t − k(s−1))` whenever `k(s−1) ≤ t`. -/
theorem cubic_lower_bound (L : LatinRect k n) (s M : ℕ) (hs : 0 < s) (hM : n ≤ M * s)
    (ht : (k : ℚ) * (s - 1) ≤ target k n) :
    (n : ℚ) * (n / (M : ℚ) ^ k - 1) * (target k n - k * (s - 1)) ≤ L.imbalance := by
  rcases Nat.eq_zero_or_pos n with rfl | hn
  · simpa using L.imbalance_nonneg
  have hMpos : 0 < M := Nat.pos_of_ne_zero fun h => by simp [h] at hM; omega
  -- the box of a symbol
  have hbox : ∀ i u, L.c i u / s < M := fun i u =>
    (Nat.div_lt_iff_lt_mul hs).2 (lt_of_lt_of_le (L.col i u).isLt hM)
  let β : Fin n → (Fin k → Fin M) := fun u i => ⟨L.c i u / s, hbox i u⟩
  -- two symbols in the same box are close
  have hclose : ∀ u v, β u = β v → (L.dist u v : ℚ) ≤ k * (s - 1) := by
    intro u v h
    have hle : L.dist u v ≤ k * (s - 1) := by
      rw [dist_eq]
      calc ∑ i, Nat.dist (L.c i u) (L.c i v) ≤ ∑ _i : Fin k, (s - 1) := by
            refine sum_le_sum fun i _ => ?_
            have h' : L.c i u / s = L.c i v / s := congrArg Fin.val (congrFun h i)
            have := nat_dist_lt_of_div_eq hs h'
            omega
        _ = k * (s - 1) := by simp
    calc (L.dist u v : ℚ) ≤ ((k * (s - 1) : ℕ) : ℚ) := by exact_mod_cast hle
      _ = k * (s - 1) := by rw [Nat.cast_mul, Nat.cast_sub (by omega : 1 ≤ s), Nat.cast_one]
  -- box occupancies
  let m : (Fin k → Fin M) → ℚ := fun b => ∑ u, if β u = b then 1 else 0
  have hsum : ∑ b, m b = n := by
    simp only [m]
    rw [Finset.sum_comm]
    simp
  have hsq : ∑ b, m b ^ 2 = ∑ u, ∑ v, if β u = β v then (1 : ℚ) else 0 := by
    simp only [m, sq, Finset.sum_mul_sum]
    rw [Finset.sum_comm]
    refine sum_congr rfl fun u _ => ?_
    rw [Finset.sum_comm]
    refine sum_congr rfl fun v _ => ?_
    simp only [ite_mul, one_mul, zero_mul]
    rw [Finset.sum_ite_eq]
    simp [eq_comm]
  -- Cauchy–Schwarz: ∑ m_b² ≥ n²/B
  have hcs : (n : ℚ) ^ 2 ≤ (M : ℚ) ^ k * ∑ b, m b ^ 2 := by
    have := sq_sum_le_card_mul_sum_sq (s := (univ : Finset (Fin k → Fin M))) (f := m)
    rw [hsum, card_univ, Fintype.card_fun, Fintype.card_fin, Fintype.card_fin] at this
    exact_mod_cast this
  have hBpos : (0 : ℚ) < (M : ℚ) ^ k := by positivity
  -- ordered pairs u ≠ v sharing a box
  let P : ℚ := ∑ u, ∑ v, if u ≠ v ∧ β u = β v then 1 else 0
  have hP : P = ∑ b, m b ^ 2 - n := by
    rw [hsq]
    have e : ∀ u v, (if β u = β v then (1 : ℚ) else 0)
        = (if u ≠ v ∧ β u = β v then 1 else 0) + if u = v then 1 else 0 := by
      intro u v; by_cases h : u = v <;> simp [h]
    simp_rw [e, sum_add_distrib, Finset.sum_ite_eq, mem_univ, ite_true]
    simp [P]
  have hPlow : (n : ℚ) ^ 2 / (M : ℚ) ^ k - n ≤ P := by
    rw [hP]
    have : (n : ℚ) ^ 2 / (M : ℚ) ^ k ≤ ∑ b, m b ^ 2 := by rw [div_le_iff₀' hBpos]; exact hcs
    linarith
  -- each close pair contributes at least t − k(s−1)
  have hpt : ∀ u v, (if u ≠ v ∧ β u = β v then target k n - k * (s - 1) else 0)
      ≤ (if u ≠ v then max (target k n - L.dist u v) 0 else 0) := by
    intro u v
    by_cases h1 : u = v
    · simp [h1]
    · by_cases h2 : β u = β v
      · simp only [ne_eq, h1, h2, not_false_eq_true, and_self, ↓reduceIte]
        exact le_max_of_le_left (by linarith [hclose u v h2])
      · simp only [ne_eq, h1, h2, not_false_eq_true, and_false, ↓reduceIte]
        exact le_max_right _ _
  have hI : (target k n - k * (s - 1)) * P ≤ L.imbalance := by
    rw [imbalance_eq_sum_pos]
    calc (target k n - k * (s - 1)) * P
        = ∑ u, ∑ v, (if u ≠ v ∧ β u = β v then target k n - k * (s - 1) else 0) := by
          simp only [P, mul_sum, mul_ite, mul_one, mul_zero]
      _ ≤ _ := sum_le_sum fun u _ => sum_le_sum fun v _ => hpt u v
  have hA : 0 ≤ target k n - k * (s - 1) := by linarith
  calc (n : ℚ) * (n / (M : ℚ) ^ k - 1) * (target k n - k * (s - 1))
      = (target k n - k * (s - 1)) * ((n : ℚ) ^ 2 / (M : ℚ) ^ k - n) := by ring
    _ ≤ (target k n - k * (s - 1)) * P := mul_le_mul_of_nonneg_left hPlow hA
    _ ≤ L.imbalance := hI

/-! ### Consequences: the cubic law -/

/-- The constant `k·m^{-k}·(1/3 − 1/m)` obtained from `M = m` boxes per axis. -/
def lowerConst (k m : ℕ) : ℚ := k / (m : ℚ) ^ k * (1 / 3 - 1 / m)

/-- **Explicit cubic lower bound.** For every `m ≥ 3`,
`I(L) ≥ k·(1/3 − 1/m)·(n³/m^k − n²)`. -/
theorem lower_bound_explicit (L : LatinRect k n) (m : ℕ) (hm : 3 ≤ m) :
    (k : ℚ) * (1 / 3 - 1 / m) * ((n : ℚ) ^ 3 / (m : ℚ) ^ k - n ^ 2) ≤ L.imbalance := by
  rcases Nat.eq_zero_or_pos n with rfl | hn
  · simpa using L.imbalance_nonneg
  set s := (n + m - 1) / m with hs_def
  have hs : 0 < s := Nat.div_pos (by omega) (by omega)
  have hM : n ≤ m * s := by
    have h1 := Nat.div_add_mod (n + m - 1) m
    have h2 := Nat.mod_lt (n + m - 1) (by omega : 0 < m)
    rw [← hs_def] at h1
    generalize m * s = q at h1 ⊢
    omega
  have hms : m * s ≤ n + m - 1 := by rw [hs_def, mul_comm]; exact Nat.div_mul_le_self _ _
  have hmq : (3 : ℚ) ≤ m := by exact_mod_cast hm
  have hnq : (1 : ℚ) ≤ n := by exact_mod_cast hn
  have hk : (0 : ℚ) ≤ k := by positivity
  -- s − 1 ≤ (n − 1)/m
  have hs1 : ((s : ℚ) - 1) * m ≤ n - 1 := by
    have : ((m * s : ℕ) : ℚ) ≤ ((n + m - 1 : ℕ) : ℚ) := by exact_mod_cast hms
    push_cast [Nat.cast_sub (by omega : 1 ≤ n + m)] at this
    linarith
  have hfrac : (0 : ℚ) ≤ 1 / 3 - 1 / m := by
    have : (1 : ℚ) / m ≤ 1 / 3 := one_div_le_one_div_of_le (by norm_num) hmq
    linarith
  -- t − k(s−1) ≥ k·n·(1/3 − 1/m) ≥ 0
  have hA : (k : ℚ) * n * (1 / 3 - 1 / m) ≤ target k n - k * (s - 1) := by
    have hs1' : (s : ℚ) - 1 ≤ (n - 1) / m := by rw [le_div_iff₀ (by linarith)]; exact hs1
    have : (k : ℚ) * (s - 1) ≤ k * ((n - 1) / m) := mul_le_mul_of_nonneg_left hs1' hk
    have e : (k : ℚ) * n * (1 / 3 - 1 / m) = target k n - k * ((n - 1) / m) - k / 3 - k / m := by
      rw [target]; field_simp; ring
    have : (0 : ℚ) ≤ k / m := by positivity
    linarith
  have hA0 : (0 : ℚ) ≤ k * n * (1 / 3 - 1 / m) := by positivity
  have main := cubic_lower_bound L s m hs hM (by linarith)
  have e : (k : ℚ) * (1 / 3 - 1 / m) * ((n : ℚ) ^ 3 / (m : ℚ) ^ k - n ^ 2)
      = (n * (n / (m : ℚ) ^ k - 1)) * (k * n * (1 / 3 - 1 / m)) := by ring
  rw [e]
  rcases le_total 0 ((n : ℚ) * (n / (m : ℚ) ^ k - 1)) with hX | hX
  · calc _ ≤ (n * (n / (m : ℚ) ^ k - 1)) * (target k n - k * (s - 1)) :=
          mul_le_mul_of_nonneg_left hA hX
      _ ≤ L.imbalance := main
  · exact le_trans (mul_nonpos_of_nonpos_of_nonneg hX hA0) L.imbalance_nonneg

/-- **The cubic law, lower half.** For fixed `k`, every `m ≥ 3` and every `ε > 0`, all
sufficiently large `k × n` Latin rectangles have `I ≥ (k·m^{-k}·(1/3 − 1/m) − ε)·n³`.
Hence `liminf_n min I / n³ ≥ max_m k·m^{-k}·(1/3 − 1/m) = c_k`. -/
theorem eventually_lower_bound (k m : ℕ) (hm : 3 ≤ m) {ε : ℚ} (hε : 0 < ε) :
    ∀ᶠ n in Filter.atTop, ∀ L : LatinRect k n, (lowerConst k m - ε) * (n : ℚ) ^ 3 ≤ L.imbalance := by
  refine Filter.eventually_atTop.2 ⟨⌈(k : ℚ) / (3 * ε)⌉₊, fun n hn L => ?_⟩
  have hn' : (k : ℚ) / (3 * ε) ≤ n := Nat.ceil_le.1 hn
  have hkn : (k : ℚ) / 3 ≤ ε * n := by
    rw [div_le_iff₀ (by positivity)] at hn'; nlinarith
  have hmq : (3 : ℚ) ≤ m := by exact_mod_cast hm
  have hfrac : (0 : ℚ) ≤ 1 / 3 - 1 / m := by
    have : (1 : ℚ) / m ≤ 1 / 3 := one_div_le_one_div_of_le (by norm_num) hmq
    linarith
  have hfrac' : (1 / 3 - 1 / m : ℚ) ≤ 1 / 3 := by
    have : (0 : ℚ) ≤ 1 / m := by positivity
    linarith
  have hk : (0 : ℚ) ≤ k := by positivity
  have h := lower_bound_explicit L m hm
  have hsmall : (k : ℚ) * (1 / 3 - 1 / m) * n ^ 2 ≤ ε * n ^ 3 := by
    have h1 : (k : ℚ) * (1 / 3 - 1 / m) ≤ k / 3 := by nlinarith
    have hn2 : (0 : ℚ) ≤ (n : ℚ) ^ 2 := by positivity
    calc (k : ℚ) * (1 / 3 - 1 / m) * n ^ 2 ≤ (k / 3) * n ^ 2 := mul_le_mul_of_nonneg_right h1 hn2
      _ ≤ (ε * n) * n ^ 2 := mul_le_mul_of_nonneg_right hkn hn2
      _ = ε * n ^ 3 := by ring
  have e : (k : ℚ) * (1 / 3 - 1 / m) * ((n : ℚ) ^ 3 / (m : ℚ) ^ k - n ^ 2)
      = lowerConst k m * n ^ 3 - k * (1 / 3 - 1 / m) * n ^ 2 := by rw [lowerConst]; ring
  rw [e] at h
  linarith

/-- **The cubic law, upper half.** `I(L) ≤ k·n³/3`. -/
theorem imbalance_le (L : LatinRect k n) : L.imbalance ≤ k * (n : ℚ) ^ 3 / 3 := by
  have hk : (0 : ℚ) ≤ k := by positivity
  have hn : (0 : ℚ) ≤ n := by positivity
  have hpt : ∀ u v : Fin n, (if u ≠ v then |(L.dist u v : ℚ) - target k n| else 0)
      ≤ 2 * k * n / 3 := by
    intro u v
    split_ifs with huv
    · have hn1 : (1 : ℚ) ≤ n := by exact_mod_cast u.pos
      have hlo : (k : ℚ) ≤ L.dist u v := by
        have : k ≤ L.dist u v := by
          rw [dist_eq]
          calc k = ∑ _i : Fin k, 1 := by simp
            _ ≤ _ := sum_le_sum fun i _ => Nat.dist_pos_of_ne fun h =>
                huv (L.row_injective i (Fin.ext h))
        exact_mod_cast this
      have hhi : (L.dist u v : ℚ) ≤ k * (n - 1) := by
        have : L.dist u v ≤ k * (n - 1) := by
          rw [dist_eq]
          calc ∑ i, Nat.dist (L.c i u) (L.c i v) ≤ ∑ _i : Fin k, (n - 1) := by
                refine sum_le_sum fun i _ => ?_
                have h1 : L.c i u < n := (L.col i u).isLt
                have h2 : L.c i v < n := (L.col i v).isLt
                unfold Nat.dist; omega
            _ = k * (n - 1) := by simp
        calc (L.dist u v : ℚ) ≤ ((k * (n - 1) : ℕ) : ℚ) := by exact_mod_cast this
          _ = k * (n - 1) := by
            rw [Nat.cast_mul, Nat.cast_sub (by exact_mod_cast hn1 : 1 ≤ n), Nat.cast_one]
      rw [abs_le, target]
      constructor <;> nlinarith
    · positivity
  have h2 : 2 * L.imbalance = ∑ u, ∑ v, if u ≠ v then |(L.dist u v : ℚ) - target k n| else 0 :=
    two_mul_sum_lt _ fun u v => by rw [dist_comm]
  have hsum : ∑ u : Fin n, ∑ v : Fin n, (if u ≠ v then |(L.dist u v : ℚ) - target k n| else 0)
      ≤ ∑ _u : Fin n, ∑ _v : Fin n, 2 * k * (n : ℚ) / 3 :=
    sum_le_sum fun u _ => sum_le_sum fun v _ => hpt u v
  simp only [sum_const, card_univ, Fintype.card_fin, nsmul_eq_mul] at hsum
  nlinarith

/-! ### The constants `c_k` (remark after `thm:cubic`) -/

theorem lowerConst_two_five : lowerConst 2 5 = 4 / 375 := by norm_num [lowerConst]

/-- For `k = 2` the best choice is `m = 5`, giving `c₂ = 4/375`. -/
theorem lowerConst_two_le (m : ℕ) : lowerConst 2 m ≤ 4 / 375 := by
  rcases Nat.lt_or_ge m 5 with hm | hm
  · interval_cases m <;> norm_num [lowerConst]
  · have hx : (5 : ℚ) ≤ m := by exact_mod_cast hm
    have e : lowerConst 2 m = 2 * (m - 3) / (3 * (m : ℚ) ^ 3) := by
      rw [lowerConst]; field_simp; ring
    rw [e, div_le_div_iff₀ (by positivity) (by norm_num)]
    nlinarith [mul_nonneg (by linarith : (0 : ℚ) ≤ m - 5)
      (by nlinarith : (0 : ℚ) ≤ 2 * m ^ 2 + 10 * m - 75)]

theorem lowerConst_four (k : ℕ) : lowerConst k 4 = k / (12 * 4 ^ k) := by
  rw [lowerConst]; field_simp; ring

/-- `4^j·(m − 3) ≤ m^j` for `j ≥ 4` and `m ≥ 4`. -/
theorem four_pow_mul_le (m : ℕ) (hm : 4 ≤ m) (j : ℕ) (hj : 4 ≤ j) :
    (4 : ℚ) ^ j * (m - 3) ≤ (m : ℚ) ^ j := by
  have hx : (4 : ℚ) ≤ m := by exact_mod_cast hm
  induction j, hj using Nat.le_induction with
  | base =>
    nlinarith [mul_nonneg (by linarith : (0 : ℚ) ≤ m - 4)
      (by nlinarith : (0 : ℚ) ≤ (m : ℚ) ^ 3 + 4 * m ^ 2 + 16 * m - 192)]
  | succ j _ ih =>
    have h4 : (0 : ℚ) ≤ (4 : ℚ) ^ j * (m - 3) := by
      have : (0 : ℚ) ≤ m - 3 := by linarith
      positivity
    calc (4 : ℚ) ^ (j + 1) * (m - 3) = 4 * ((4 : ℚ) ^ j * (m - 3)) := by ring
      _ ≤ 4 * (m : ℚ) ^ j := by linarith
      _ ≤ m * (m : ℚ) ^ j := mul_le_mul_of_nonneg_right hx (by positivity)
      _ = (m : ℚ) ^ (j + 1) := by ring

/-- For `k ≥ 3` the best choice is `m = 4`, giving `c_k = k/(12·4^k)`. -/
theorem lowerConst_le_four (k : ℕ) (hk : 3 ≤ k) (m : ℕ) : lowerConst k m ≤ lowerConst k 4 := by
  have hk0 : (0 : ℚ) ≤ k := by positivity
  have h4 : (0 : ℚ) ≤ lowerConst k 4 := by rw [lowerConst_four]; positivity
  rcases Nat.lt_or_ge m 4 with hm | hm
  · refine le_trans ?_ h4
    interval_cases m
    · simp [lowerConst, zero_pow (by omega : k ≠ 0)]
    all_goals
      rw [lowerConst]
      exact mul_nonpos_of_nonneg_of_nonpos (by positivity) (by norm_num)
  · have hx : (4 : ℚ) ≤ m := by exact_mod_cast hm
    have hkey := four_pow_mul_le m hm (k + 1) (by omega)
    have e : lowerConst k m = k * (m - 3) / (3 * (m : ℚ) ^ (k + 1)) := by
      rw [lowerConst]; field_simp; ring
    rw [e, lowerConst_four, div_le_div_iff₀ (by positivity) (by positivity)]
    have : (k : ℚ) * ((4 : ℚ) ^ (k + 1) * (m - 3)) ≤ k * (m : ℚ) ^ (k + 1) :=
      mul_le_mul_of_nonneg_left hkey hk0
    have e2 : (4 : ℚ) ^ (k + 1) = 4 * 4 ^ k := by ring
    rw [e2] at this
    nlinarith

end LatinRect

end BalancedLatin
