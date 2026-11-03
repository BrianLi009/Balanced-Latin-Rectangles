#!/bin/sh
# Reproduce every run behind results/ (one single-threaded run per cell and budget).
#   seed 1:  60 s, all cells  k = 2..n-1, n = 8..13
#   seed 2: 300 s, all cells
#   seed 3: 600 s, cells with k >= 4 and n >= 9
# JOBS runs in parallel (default 8). Total wall time with 8 jobs is about 1.5 hours.
set -e
cd "$(dirname "$0")"
JOBS=${JOBS:-8}
cc -O3 -o sa sa.c -lm
mkdir -p ../results/raw

cells() {  # $1 = minimum k, $2 = minimum n
  for n in 8 9 10 11 12 13; do
    [ "$n" -ge "$2" ] || continue
    k=$1; while [ "$k" -le $((n - 1)) ]; do echo "$k $n"; k=$((k + 1)); done
  done
}

run() {  # $1 = seconds, $2 = seed, stdin = "k n" lines
  xargs -P "$JOBS" -L 1 sh -c './sa $0 $1 '"$1"' '"$2"' > ../results/raw/r_$0_$1_s'"$2"'.txt'
}

cells 2 8 | run 60 1
cells 2 8 | run 300 2
cells 4 9 | run 600 3

python3 collect.py
python3 verify.py
python3 test_checker.py
python3 timing.py      # about 5 minutes with 8 jobs
