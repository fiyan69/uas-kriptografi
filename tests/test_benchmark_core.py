import multiprocessing
import unittest

from benchmark import ALGORITHMS, benchmark_once, make_payload


class BenchmarkCoreTest(unittest.TestCase):
    def test_payload_is_repeatable_and_exact_length(self):
        self.assertEqual(make_payload(128, 77), make_payload(128, 77))
        self.assertEqual(len(make_payload(128, 77)), 128)

    def test_each_cipher_encrypts_full_payload(self):
        payload = make_payload(128, 4)
        for algorithm in ALGORITHMS:
            elapsed, cpu, memory, throughput = benchmark_once(algorithm, payload)
            self.assertGreater(elapsed, 0)
            self.assertGreaterEqual(cpu, 0)
            self.assertGreaterEqual(memory, 0)
            self.assertGreater(throughput, 0)


if __name__ == "__main__":
    unittest.main()
