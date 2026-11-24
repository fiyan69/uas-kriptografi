import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BenchmarkSmokeTest(unittest.TestCase):
    def test_smoke_benchmark_writes_valid_rows(self):
        script = Path(__file__).resolve().parents[1] / "benchmark.py"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.csv"
            result = subprocess.run(
                [sys.executable, str(script), "--output", str(output), "--sizes", "64", "--repeats", "1", "--warmups", "0"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["algorithm"] for row in rows}, {"AES-128-CTR", "AES-256-CTR", "ChaCha20", "3DES-CTR"})
        self.assertTrue(all(int(row["file_size_bytes"]) == 64 for row in rows))
        self.assertTrue(all(float(row["execution_time_seconds"]) > 0 for row in rows))
        self.assertTrue(all(float(row["throughput_mb_per_sec"]) > 0 for row in rows))
    def test_rows_record_actual_cpu_without_condition_claim(self):
        script = Path(__file__).resolve().parents[1] / "benchmark.py"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.csv"
            result = subprocess.run(
                [sys.executable, str(script), "--output", str(output), "--sizes", "64", "--repeats", "1", "--warmups", "0"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual({row["system_condition"] for row in rows}, {"measured_cpu"})
        self.assertTrue(all(float(row["system_cpu_usage_percent"]) >= 0 for row in rows))


if __name__ == "__main__":
    unittest.main()
