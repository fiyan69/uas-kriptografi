import unittest

from evaluate_models_leakage_safe import fit_fences, transform


class FoldLocalFenceTest(unittest.TestCase):
    def make_rows(self, values):
        rows = []
        for i, value in enumerate(values):
            rows.append({
                "file_size_bytes": "1024", "algorithm": "AES-128-CTR",
                "execution_time_seconds": str(value), "process_cpu_usage_percent": "5",
                "memory_peak_delta_bytes": "1",
            })
        return rows

    def test_test_extreme_does_not_change_training_fences(self):
        train = self.make_rows([1, 2, 3, 4, 5, 6, 7, 8])
        test = self.make_rows([10000])
        fences = fit_fences(train)
        processed = transform(test, fences)
        self.assertEqual(processed[0]["execution_time_seconds"], fences[0][("1024", "AES-128-CTR", "execution_time_seconds")][1])
        self.assertIn("execution_time_seconds", processed[0]["outlier_metrics"])
        self.assertLess(processed[0]["execution_time_seconds"], 10000)


if __name__ == "__main__":
    unittest.main()
