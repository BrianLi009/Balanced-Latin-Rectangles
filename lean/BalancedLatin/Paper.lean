import BalancedLatin.Certificates
import BalancedLatin.Cubic
import BalancedLatin.Faithfulness

/-!
# Index: statements of the paper and where they are proved

| paper                                   | Lean                                                  |
|-----------------------------------------|-------------------------------------------------------|
| definitions of `d`, `I` (Section 2)     | `LatinRect`, `LatinRect.dist`, `LatinRect.imbalance`  |
| `LatinRect` = Latin arrays of the paper | `arrayEquiv`, `ofArray_col`                           |
| `LatinRect k n` is inhabited for k ≤ n  | `nonempty_of_le`                                      |
| spec agrees with CP 2023/2025 values    | `Certificates.exists_pub_*` (14 published rectangles) |
| `3I` is an integer                      | `LatinRect.imbalance_eq_imb3`                         |
| `t` is the average distance             | `LatinRect.sum_dist`, `LatinRect.sum_dev`             |
| Equation (1): `I = 2∑_{u<v}(t − d)⁺`    | `LatinRect.imbalance_eq_two_mul_sum_pos`              |
| pigeonhole theorem (`thm:cubic`)        | `LatinRect.cubic_lower_bound_ceil` (as stated), `LatinRect.cubic_lower_bound` (general) |
| cubic law, `liminf ≥ c_k`               | `LatinRect.eventually_lower_bound`                    |
| cubic law, `limsup ≤ k/3`               | `LatinRect.imbalance_le`                              |
| Remark (constants `c₂`, `c_k`)          | `lowerConst_two_le`, `lowerConst_le_four`, ...        |
| Tables 1 and 3, Figure 1 (rectangles)   | `Certificates.exists_k*_n*` (kernel-checked)          |

The certificates use only `BalancedLatin.Defs`, which imports nothing but Lean core.
Below, a few of them are restated with the imbalance over `ℚ`.
-/

namespace BalancedLatin.Paper
open BalancedLatin LatinRect Certificates

theorem imbalance_of_imb3 {k n : ℕ} {L : LatinRect k n} {x : ℕ} (h : L.imb3 = x) :
    L.imbalance = x / 3 := by rw [imbalance_eq_imb3, h]

/-- Figure 1 and `thm:3x9` (upper bound): a `3 × 9` rectangle of imbalance `56`. -/
theorem three_by_nine : ∃ L : LatinRect 3 9, L.imbalance = 56 :=
  ⟨rect_k3_n9, by rw [imbalance_of_imb3 imb3_k3_n9]; norm_num⟩

/-- The largest improvement of Table 1: `12 × 13`, `274 → 166`. -/
theorem twelve_by_thirteen : ∃ L : LatinRect 12 13, L.imbalance = 166 :=
  ⟨rect_k12_n13, by rw [imbalance_of_imb3 imb3_k12_n13]; norm_num⟩

/-- Table 3: a `2 × 16` rectangle of imbalance `422` (the MIP upper bound was `427⅓`). -/
theorem two_by_sixteen : ∃ L : LatinRect 2 16, L.imbalance = 422 :=
  ⟨rect_k2_n16, by rw [imbalance_of_imb3 imb3_k2_n16]; norm_num⟩

end BalancedLatin.Paper
