import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class LabelingSmokeTest(unittest.TestCase):
    def test_labeler_assigns_best_algorithm_within_each_round(self):
        script = Path(__file__).resolve().parents[1] / "label_dataset.py"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "raw.csv"
            output = Path(directory) / "labeled.csv"
            fields = ["file_size_bytes", "round_id", "algorithm", "execution_time_seconds", "process_cpu_usage_percent", "memory_peak_delta_bytes", "throughput_mb_per_sec"]
            rows = [
                ["1024", "1", "AES-128-CTR", "1", "10", "100", "1"],
                ["1024", "1", "AES-256-CTR", "2", "20", "200", "0.5"],
                ["1024", "1", "ChaCha20", "3", "30", "300", "0.33"],
                ["1024", "1", "3DES-CTR", "4", "40", "400", "0.25"],
            ]
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(fields)
                writer.writerows(rows)
            result = subprocess.run([sys.executable, str(script), str(source), str(output)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline="", encoding="utf-8") as f:
                labeled = list(csv.DictReader(f))
        self.assertEqual(len(labeled), 4)
        self.assertEqual({r["optimal_algorithm"] for r in labeled}, {"AES-128-CTR"})
        self.assertTrue(all(float(r["selection_score"]) >= 0 for r in labeled))


if __name__ == "__main__":
    unittest.main()
