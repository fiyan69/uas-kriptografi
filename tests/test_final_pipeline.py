import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from evaluate_models_final import (
    ALGORITHMS, FEATURES, METRICS, fit_fences, load_raw, make_samples,
    metric_report, raw_sha256, transform,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_dataset.csv"
SCRIPT = ROOT / "evaluate_models_final.py"


class FinalPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, _ = load_raw(RAW)

    def test_raw_hash_and_complete_groups(self):
        self.assertEqual(raw_sha256(RAW), "30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188")
        samples = make_samples(self.rows)
        self.assertEqual(len(self.rows), 720)
        self.assertEqual(len(samples), 180)
        self.assertTrue(all(len(set((r["algorithm"] for r in self.rows if r["round_id"] == s["id"][2]))) == 4 for s in samples))

    def test_train_only_bounds_and_test_mutation(self):
        train = self.rows[:576]
        test = copy.deepcopy(self.rows[576:])
        bounds = fit_fences(train)
        original = copy.deepcopy(bounds)
        for row in test:
            row["execution_time_seconds"] = "999999"
            row["memory_peak_delta_bytes"] = "999999"
        transform(test, bounds)
        self.assertEqual(bounds, original)

    def test_processed_throughput_consistency(self):
        processed = transform(self.rows, fit_fences(self.rows))
        for row in processed:
            expected = float(row["file_size_bytes"]) / 1048576.0 / float(row["execution_time_seconds"])
            self.assertAlmostEqual(float(row["throughput_mb_per_sec"]), expected, places=12)

    def test_metrics_recompute_with_union_classes(self):
        report = metric_report(["AES-128-CTR"], ["3DES-CTR"])
        self.assertEqual(report["confusion_matrix_labels"], ["AES-128-CTR", "3DES-CTR"])
        self.assertEqual(sum(map(sum, report["confusion_matrix"])), 1)
        self.assertIn("3DES-CTR", report["predicted_classes"])

    def test_end_to_end_reproducible_and_protocol(self):
        with tempfile.TemporaryDirectory() as directory:
            out1, out2 = Path(directory) / "a", Path(directory) / "b"
            for out in (out1, out2):
                result = subprocess.run([sys.executable, str(SCRIPT), str(RAW), str(out)], capture_output=True, text=True, timeout=180)
                self.assertEqual(result.returncode, 0, result.stderr)
            report1 = (out1 / "evaluation_final.json").read_bytes()
            report2 = (out2 / "evaluation_final.json").read_bytes()
            self.assertEqual(hashlib.sha256(report1).digest(), hashlib.sha256(report2).digest())
            data = json.loads(report1)
            self.assertEqual(data["protocol"]["data_source_status"], "historical_raw_provisional_pending_cpu_measurement_decision")
            self.assertEqual(data["protocol"]["cv_rounds"], 144)
            self.assertEqual(data["protocol"]["holdout_rounds"], 36)
            self.assertEqual(len(data["cv"]["folds"]), 5)
            self.assertEqual(set(data["holdout"]["models"]), {"static_if_else_baseline", "decision_tree", "random_forest", "logistic_regression"})
            self.assertTrue((out1 / "descriptive_preprocessed.csv").exists())
            self.assertTrue((out1 / "labeled_dataset_final.csv").exists())


if __name__ == "__main__":
    unittest.main()
