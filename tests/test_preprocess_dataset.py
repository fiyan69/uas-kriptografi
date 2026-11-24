import csv
import tempfile
import unittest
from pathlib import Path

from preprocess_dataset import METRICS, preprocess


class PreprocessTest(unittest.TestCase):
    def test_winsorizes_outlier_and_keeps_row_count_and_source(self):
        rows = []
        for i in range(10):
            row = {"file_size_bytes": "1024", "algorithm": "AES-128-CTR"}
            for metric in METRICS:
                row[metric] = str(1000 if i == 9 else i + 1)
            rows.append(row)
        processed = preprocess(rows)
        self.assertEqual(len(processed), len(rows))
        self.assertEqual(rows[-1][METRICS[0]], "1000")
        self.assertNotEqual(processed[-1][METRICS[0]], "1000")
        self.assertIn(METRICS[0], processed[-1]["outlier_metrics"])

    def test_invalid_measurement_rejected(self):
        row = {"file_size_bytes": "1024", "algorithm": "AES-128-CTR"}
        row.update({metric: "1" for metric in METRICS})
        row[METRICS[0]] = "nan"
        with self.assertRaises(ValueError):
            preprocess([row])


if __name__ == "__main__":
    unittest.main()
