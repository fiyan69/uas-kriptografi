"""Paired diagnostic: same encryption, CPU clock before vs after sampler shutdown."""
import csv
import hashlib
import json
import random
import time
from pathlib import Path
from unittest.mock import patch

import benchmark
from label_dataset import METRICS, WEIGHTS, normalized

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw_dataset.csv'
EXPECTED = '30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188'


def winner(group, cpu_column):
    columns = [normalized([r[column] for r in group]) for column in ('execution_time_seconds', cpu_column, 'memory_peak_delta_bytes')]
    scores = [sum(WEIGHTS[i] * columns[i][j] for i in range(3)) for j in range(4)]
    return min(range(4), key=lambda j: (scores[j], -group[j]['throughput_mb_per_sec'], group[j]['algorithm']))


def main():
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == EXPECTED
    rows = []
    rng = random.Random(2026)
    real_clock = time.thread_time_ns
    real_join = benchmark.threading.Thread.join
    # Predeclared diagnostic thresholds: >=1 CPU percentage point OR changed round winner.
    for size in (1024, 1048576, 52428800):
        payload = benchmark.make_payload(size, 2026)
        for repeat in range(1, 4):
            order = list(benchmark.ALGORITHMS)
            rng.shuffle(order)
            for algorithm in order:
                clocks = []
                after_join = []

                def clock():
                    value = real_clock()
                    clocks.append(value)
                    return value

                def join(thread, *args, **kwargs):
                    result = real_join(thread, *args, **kwargs)
                    after_join.append(real_clock())
                    return result

                with patch.object(benchmark.time, 'thread_time_ns', clock), patch.object(benchmark.threading.Thread, 'join', join):
                    elapsed, cpu, memory, throughput = benchmark.benchmark_once(algorithm, payload)
                assert len(clocks) == 2 and len(after_join) == 1
                cpu_ns = clocks[1] - clocks[0]
                wall_ns = cpu_ns * 100 / cpu
                cleanup_ns = after_join[0] - clocks[1]
                added_cpu = cleanup_ns / wall_ns * 100
                rows.append(dict(file_size_bytes=size, round_id=repeat, algorithm=algorithm,
                                 execution_time_seconds=elapsed, process_cpu_usage_percent=cpu,
                                 old_interval_cpu_estimate_percent=cpu + added_cpu,
                                 cleanup_cpu_ns=cleanup_ns, cpu_added_percentage_points=added_cpu,
                                 memory_peak_delta_bytes=memory, throughput_mb_per_sec=throughput))
    flips = []
    for size in (1024, 1048576, 52428800):
        for repeat in range(1, 4):
            group = [r for r in rows if r['file_size_bytes'] == size and r['round_id'] == repeat]
            before = group[winner(group, 'old_interval_cpu_estimate_percent')]['algorithm']
            after = group[winner(group, 'process_cpu_usage_percent')]['algorithm']
            if before != after:
                flips.append(dict(file_size_bytes=size, round_id=repeat, old=before, corrected=after))
    out = ROOT / 'diagnostik_interval_cpu.csv'
    with out.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(rows=len(rows), rounds=9, material_threshold_cpu_percentage_points=1.0,
                   max_added_cpu_percentage_points=max(r['cpu_added_percentage_points'] for r in rows),
                   label_flips=flips, materially_affected=bool(flips) or any(r['cpu_added_percentage_points'] >= 1 for r in rows),
                   limitation='Small paired instrumentation diagnostic, no warmup; cannot reconstruct historical cleanup duration or certify absence of historical label changes.',
                   raw_sha256=hashlib.sha256(RAW.read_bytes()).hexdigest())
    assert summary['raw_sha256'] == EXPECTED
    (ROOT / 'diagnostik_interval_cpu.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
