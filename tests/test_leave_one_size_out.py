import unittest

from evaluate_models import leave_one_size_out


class LeaveOneSizeOutTest(unittest.TestCase):
    def test_each_size_is_tested_only_against_other_sizes(self):
        samples = []
        for size in (100, 1000):
            for i in range(6):
                label = "AES-128-CTR" if i < 3 else "ChaCha20"
                samples.append(([size, float(i), 40.0], label))
        result = leave_one_size_out(samples)
        self.assertEqual(set(result["folds"]), {"100", "1000"})
        for fold in result["folds"].values():
            self.assertEqual(fold["test_count"], 6)
            self.assertEqual(fold["train_count"], 6)
            self.assertEqual(set(fold["test_sizes"]), {fold["held_out_size"]})
            self.assertNotIn(fold["held_out_size"], fold["train_sizes"])
        self.assertEqual(result["overall"]["majority_baseline"]["accuracy"], 0.5)


if __name__ == "__main__":
    unittest.main()
