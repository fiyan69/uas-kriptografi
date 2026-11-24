import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

METRICS = (
    "execution_time_seconds",
    "process_cpu_usage_percent",
    "memory_peak_delta_bytes",
    "throughput_mb_per_sec",
)


def fences(values):
    ordered = sorted(values)
    q1 = statistics.median(ordered[: len(ordered) // 2])
    q3 = statistics.median(ordered[(len(ordered) + 1) // 2 :])
    spread = q3 - q1
    return q1 - 1.5 * spread, q3 + 1.5 * spread


def preprocess(rows):
    if not rows:
        raise ValueError("Input dataset is empty")
    fields = set(rows[0])
    required = {"file_size_bytes", "algorithm", *METRICS}
    missing = required - fields
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    groups = defaultdict(list)
    for row in rows:
        for metric in METRICS:
            value = float(row[metric])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {metric} value: {row[metric]}")
        groups[(row["file_size_bytes"], row["algorithm"])].append(row)
    output = []
    for (_, _), group in groups.items():
        if len(group) < 4:
            raise ValueError("Each file-size/algorithm group needs at least 4 measurements")
        bounds = {metric: fences([float(row[metric]) for row in group]) for metric in METRICS}
        for row in group:
            updated = dict(row)
            flags = []
            for metric, (low, high) in bounds.items():
                value = float(row[metric])
                if value < low or value > high:
                    flags.append(metric)
                updated[metric] = str(min(high, max(low, value)))
            updated["outlier_metrics"] = ";".join(flags)
            output.append(updated)
    return output


def main():
    parser = argparse.ArgumentParser(description="IQR winsorization; preserves source and flags modified observations.")
    parser.add_argument("input", nargs="?", default="raw_dataset.csv")
    parser.add_argument("output", nargs="?", default="preprocessed_dataset.csv")
    args = parser.parse_args()
    src, dst = Path(args.input), Path(args.output)
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)
    clean = preprocess(rows)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields + ["outlier_metrics"])
        writer.writeheader()
        writer.writerows(clean)
    print(f"Preprocessed {len(rows)} rows -> {dst}; winsorized values flagged in outlier_metrics; source unchanged")


if __name__ == "__main__":
    main()
