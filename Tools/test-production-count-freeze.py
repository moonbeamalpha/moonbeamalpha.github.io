#!/usr/bin/env python3
"""Protect published counts until an approved app release is authorized."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = json.loads((ROOT / 'Tools/production-count-freeze-20261012.json').read_text())


class ProductionCountFreeze(unittest.TestCase):
    def test_production_snapshot_and_images_are_unchanged(self):
        for name, expected in BASELINE['protectedSHA256'].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_all_exam_and_aggregate_counts_match_live_baseline(self):
        snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
        self.assertEqual(snapshot['exams'], BASELINE['examCounts'])
        self.assertEqual(snapshot['totals'], BASELINE['totals'])
        self.assertEqual(snapshot['cert_path_count'], BASELINE['certPathCount'])
        for name in ['llms.txt', 'llms-full.txt']:
            counts = {code: int(n.replace(',', '')) for code, n in re.findall(
                r'- \[([A-Z]+-\d+)[^\n]*?: ([\d,]+) in-app practice questions',
                (ROOT / name).read_text())}
            self.assertEqual(counts, BASELINE['examCounts'], name)
            self.assertIn(BASELINE['totals']['questionCountLabel'] + ' practice questions',
                          (ROOT / name).read_text())


if __name__ == '__main__':
    unittest.main()
