#!/usr/bin/env python3
"""Regression checks for incomplete, corrupt and mislabelled research artifacts.
Runs in temporary copies; never changes committed experiment data.
"""
import contextlib
import csv
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import collect
import timing
import verify

ROOT = Path(verify.ROOT)


class ArtifactChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ('results', 'data'):
            shutil.copytree(ROOT / name, self.root / name,
                            ignore=shutil.ignore_patterns('timing_runs'))
        self.patches = [patch.object(m, 'ROOT', str(self.root))
                        for m in (collect, timing, verify)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return verify.main([])

    def rewrite_timing(self, mutate):
        p = self.root / 'results/timing.csv'
        with p.open() as f:
            rows = list(csv.DictReader(f))
        fields = list(rows[0])
        mutate(rows)
        with p.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)

    def test_complete_artifacts_and_deterministic_collection(self):
        self.assertEqual(self.verify(), 0)
        self.assertEqual(len(collect.load_runs()), 137)
        self.assertEqual(len(timing.load_timing_results()), 185)
        original = (self.root / 'results/results.csv').read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            collect.main()
        self.assertEqual(original, (self.root / 'results/results.csv').read_bytes())
        witnesses = {p.name: p.read_bytes() for p in (self.root / 'results/rectangles').glob('*.txt')}
        with contextlib.redirect_stdout(io.StringIO()):
            collect.main()
        self.assertEqual(witnesses, {p.name: p.read_bytes() for p in (self.root / 'results/rectangles').glob('*.txt')})
        self.assertEqual(self.verify(), 0)

    def test_empty_rectangles_rejected(self):
        for p in (self.root / 'results/rectangles').glob('*.txt'):
            p.unlink()
        with self.assertRaises(ValueError): self.verify()

    def test_missing_rectangle_rejected(self):
        (self.root / 'results/rectangles/k2_n8.txt').unlink()
        with self.assertRaises(ValueError): self.verify()

    def test_mislabelled_dimensions_rejected(self):
        d = self.root / 'results/rectangles'
        (d / 'k2_n8.txt').write_bytes((d / 'k3_n8.txt').read_bytes())
        with self.assertRaises(ValueError): self.verify()

    def test_duplicate_csv_rejected(self):
        p = self.root / 'results/results.csv'
        p.write_text(p.read_text() + p.read_text().splitlines()[1] + '\n')
        with self.assertRaises(ValueError): self.verify()

    def test_empty_matrix_rejected(self):
        with self.assertRaises(ValueError): verify.imbalance([])

    def test_missing_raw_rejected_before_writing(self):
        original = (self.root / 'results/results.csv').read_bytes()
        next((self.root / 'results/raw').glob('*.txt')).unlink()
        with self.assertRaises(ValueError): collect.main()
        self.assertEqual(original, (self.root / 'results/results.csv').read_bytes())

    def test_unfinished_raw_rejected(self):
        next((self.root / 'results/raw').glob('*.txt')).write_text('NONE\n')
        with self.assertRaises(ValueError): collect.load_runs()

    def test_wrong_raw_dimensions_rejected(self):
        d = self.root / 'results/raw'
        (d / 'r_2_8_s1.txt').write_bytes((d / 'r_3_8_s1.txt').read_bytes())
        with self.assertRaises(ValueError): collect.load_runs()

    def test_missing_timing_rejected(self):
        self.rewrite_timing(lambda rows: rows.pop())
        with self.assertRaises(ValueError): timing.load_timing_results()

    def test_duplicate_timing_rejected(self):
        self.rewrite_timing(lambda rows: rows.append(rows[0].copy()))
        with self.assertRaises(ValueError): timing.load_timing_results()

    def test_failed_target_rejected(self):
        self.rewrite_timing(lambda rows: rows[0].update(reached='0', seconds=''))
        with self.assertRaises(ValueError): timing.load_timing_results()

    def test_failed_process_retains_logs(self):
        from subprocess import CompletedProcess
        with patch.object(timing.subprocess, 'run', return_value=CompletedProcess([], 2, 'NONE\n', 'failure')):
            with self.assertRaises(RuntimeError):
                timing.run(('test', 3, 5, 18, '', 1), self.root)
        self.assertEqual((self.root / 'test_3_5_1.stderr').read_text(), 'failure')


if __name__ == '__main__':
    unittest.main(verbosity=2)
