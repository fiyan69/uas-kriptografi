import argparse
import csv
import os
import platform
import random
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
from Crypto.Cipher import AES, ChaCha20, DES3


ALGORITHMS = ("AES-128-CTR", "AES-256-CTR", "ChaCha20", "3DES-CTR")
DEFAULT_SIZES = (1024, 10_240, 102_400, 1_048_576, 10_485_760, 52_428_800)
FIELDS = (
    "timestamp_utc", "run_id", "round_id", "trial", "file_size_bytes", "algorithm", "system_condition",
    "initial_ram_usage_percent", "system_cpu_usage_percent", "execution_time_seconds",
    "process_cpu_usage_percent", "memory_peak_delta_bytes", "throughput_mb_per_sec",
    "python_version", "platform", "pycryptodome_version", "psutil_version",
)


def make_cipher(algorithm, key, nonce):
    if algorithm.startswith("AES-"):
        return AES.new(key, AES.MODE_CTR, nonce=nonce)
    if algorithm == "ChaCha20":
        return ChaCha20.new(key=key, nonce=nonce)
    return DES3.new(key, DES3.MODE_CTR, nonce=nonce)


def benchmark_once(algorithm, payload):
    key_size = {"AES-128-CTR": 16, "AES-256-CTR": 32, "ChaCha20": 32, "3DES-CTR": 24}[algorithm]
    key = os.urandom(key_size)
    nonce_size = {"AES-128-CTR": 8, "AES-256-CTR": 8, "ChaCha20": 8, "3DES-CTR": 4}[algorithm]
    nonce = os.urandom(nonce_size)
    cipher = make_cipher(algorithm, key, nonce)
    proc = psutil.Process()
    baseline_rss = proc.memory_info().rss
    peak_rss = [baseline_rss]
    stop = threading.Event()

    def sample_memory():
        while not stop.is_set():
            try:
                peak_rss[0] = max(peak_rss[0], proc.memory_info().rss)
            except psutil.Error:
                pass
            stop.wait(0.01)

    sampler = threading.Thread(target=sample_memory, daemon=True)
    sampler.start()
    start_cpu = time.thread_time_ns()
    start = time.perf_counter_ns()
    try:
        iterations = 0
        while iterations == 0 or time.perf_counter_ns() - start < 1_000_000_000:
            ciphertext = cipher.encrypt(payload)
            iterations += 1
        wall_ns = time.perf_counter_ns() - start
        cpu_ns = time.thread_time_ns() - start_cpu
    finally:
        stop.set()
        sampler.join()
    wall_time = wall_ns / 1_000_000_000 / iterations
    cpu_percent = 100 * cpu_ns / wall_ns if wall_ns > 0 else 0.0
    mem_delta = max(0, peak_rss[0] - baseline_rss)
    throughput = len(ciphertext) / (1024 * 1024) / wall_time if wall_time > 0 else 0.0
    if len(ciphertext) != len(payload):
        raise RuntimeError(f"Unexpected ciphertext length for {algorithm}")
    return wall_time, cpu_percent, mem_delta, throughput


def make_payload(size, seed):
    # Streaming deterministic generation avoids holding a second full payload in RAM.
    import hashlib
    chunks = []
    remaining = size
    counter = 0
    while remaining:
        chunk = hashlib.shake_256(f"{seed}:{counter}".encode()).digest(min(1024 * 1024, remaining))
        chunks.append(chunk)
        remaining -= len(chunk)
        counter += 1
    return b"".join(chunks)


def main():
    parser = argparse.ArgumentParser(description="Encrypt-only cryptographic benchmark; writes raw measurements to CSV.")
    parser.add_argument("--output", default="raw_dataset.csv")
    parser.add_argument("--sizes", nargs="+", type=int, default=DEFAULT_SIZES, help="Payload sizes in bytes")
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if any(size <= 0 for size in args.sizes) or args.repeats < 1 or args.warmups < 0:
        parser.error("sizes and repeats must be positive; warmups cannot be negative")

    from Crypto import __version__ as crypto_version
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rng = random.Random(args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output.exists() or output.stat().st_size == 0

    with output.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        trial = 0
        for size in args.sizes:
            payload = make_payload(size, args.seed)
            for _ in range(args.warmups):
                for algorithm in ALGORITHMS:
                    benchmark_once(algorithm, payload)
            for repeat in range(args.repeats):
                algorithms = list(ALGORITHMS)
                rng.shuffle(algorithms)
                for algorithm in algorithms:
                    trial += 1
                    system_cpu = psutil.cpu_percent(interval=1.0)
                    ram_before = psutil.virtual_memory().percent
                    elapsed, cpu, memory, throughput = benchmark_once(algorithm, payload)
                    writer.writerow({
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "run_id": run_id,
                        "round_id": repeat + 1,
                        "trial": trial,
                        "file_size_bytes": size,
                        "algorithm": algorithm,
                        "system_condition": "measured_cpu",
                        "initial_ram_usage_percent": ram_before,
                        "system_cpu_usage_percent": system_cpu,
                        "execution_time_seconds": elapsed,
                        "process_cpu_usage_percent": cpu,
                        "memory_peak_delta_bytes": memory,
                        "throughput_mb_per_sec": throughput,
                        "python_version": platform.python_version(),
                        "platform": platform.platform(),
                        "pycryptodome_version": crypto_version,
                        "psutil_version": psutil.__version__,
                    })
                    csvfile.flush()
            print(f"Finished: {size} bytes", file=sys.stderr)


if __name__ == "__main__":
    main()
