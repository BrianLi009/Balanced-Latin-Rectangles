# Validation of the revised artifact

Reference checkout: `ee17187b5e7b023c67e9fb998f0113f4348cea12`.
The revision preserves all committed final rectangles, numerical results, budget results,
and historical timing measurements. The paper and metadata now scope their claims to
CP 2025 Table 1 and distinguish first improvement from final solution quality.

## Checks

- All 51 final rectangles and all 137 raw quality outputs pass exact Latin-property,
  dimension, and objective checks; collection reproduces the numerical result CSV.
- All 14 printed fixtures from CP 2023 and CP 2025 reproduce the stated objectives.
- Thirteen pipeline regression tests cover incomplete/empty data, duplicate rows,
  dimension mismatches, incomplete timing data and retained logs on process failure.
- The revised C solver compiles with GCC `-O3 -Wall -Wextra` without warnings.
  All 20 CP 2023 target checks (four targets, seeds 101–105) pass, along with seven
  argument/initial-target boundary checks.
- Regenerated LaTeX numbers and table preserve every reported result. The rebuilt
  PDF and updated timing figures are checked separately from numerical validation.

## Independent timing rerun

`fresh-timing.zip` retains a separate full rerun performed during the audit, before
editing the solver. It includes all 185 stdout witnesses and stderr logs, result and
environment JSON, the exact original solver source, and the audit scripts. It uses
Linux x86_64/GCC 13.3.0 with eight workers and a 300 CPU-second cap. This is not the
historical Apple M3 experiment. To use the bundled audit scripts, place them in an
`audit/` directory at the root of a checkout of the reference commit and run
`python3 audit/rerun_timing.py`.

| Targets | Runs reached | Pooled median CPU seconds | Maximum CPU seconds |
|---|---:|---:|---:|
| Strict improvement over CP 2025 reference | 165 / 165 | 0.211 | 279.679 |
| Reach or improve CP 2023 SAT target | 20 / 20 | 0.073 | 0.146 |

All 185 terminal objective values agree with the original timing CSV. This independently
supports target reachability for the tested seeds; it does not authenticate original
historical times. Historical stdout/stderr and build metadata were not archived.
Future runs of the revised `code/timing.py` retain witnesses, logs and source/binary
hashes. None of these finite checks proves global correctness or optimality.

## Remaining experimental limits

Direct comparison with the 2017 local search, controlled hardware comparisons, and
penalty/neighborhood ablations remain undone. The paper now identifies them explicitly.
The quality experiment uses a different seed for each budget; it does not isolate a
causal budget effect. Access for reviewers must be arranged if the repository is private.
