#!/usr/bin/env python3
"""Check verify.py against every rectangle printed in the two prior papers, with the imbalance
those papers report. If all match, our checker computes exactly the published quantity.
Rectangles are in data/published/; the first line of each file states the source and value."""
import glob
import os
import re
from fractions import Fraction

from verify import imbalance, read_rectangle, fmt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
files = sorted(glob.glob(os.path.join(ROOT, 'data', 'published', '*.txt')))
for f in files:
    head = open(f).readline()
    reported = re.search(r'reported imbalance ([0-9.]+)', head).group(1)
    got = fmt(imbalance(read_rectangle(f)))
    ok = got == reported
    bad += not ok
    print(f"{os.path.basename(f):28s} reported {reported:>6}  computed {got:>6}  {'OK' if ok else 'MISMATCH'}")
print(f"\n{len(files)} published rectangles, {bad} mismatches.")
raise SystemExit(1 if bad else 0)
