import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ModelEvaluationSmokeTest(unittest.TestCase):
    def test_evaluation_emits_metrics_for_baseline_and_two_models(self):
        script = Path(__file__).resolve().parents[1] / "evaluate_models_leakage_safe.py"
        dataset = Path(__file__).resolve().parents[1] / "raw_dataset.csv"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.json"
            preprocessed = Path(directory) / "preprocessed.csv"
            result = subprocess.run([sys.executable, str(script), str(dataset), str(output), "--preprocessed", str(preprocessed)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(set(report["holdout_80_20"]["models"]), {"static_if_else_baseline", "decision_tree", "random_forest"})
        self.assertEqual(set(report["five_fold_cv"]["overall"]), {"static_if_else_baseline", "decision_tree", "random_forest"})
        for metrics in report["holdout_80_20"]["models"].values():
            self.assertIn("accuracy", metrics)
            self.assertIn("precision_macro", metrics)
            self.assertIn("recall_macro", metrics)
            self.assertIn("f1_macro", metrics)
            self.assertTrue(metrics["confusion_matrix"])
        self.assertEqual(report["round_groups"], 180)


if __name__ == "__main__":
    unittest.main()
