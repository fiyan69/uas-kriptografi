import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

ALGORITHMS = {"AES-128-CTR", "AES-256-CTR", "ChaCha20", "3DES-CTR"}
METRICS = ("execution_time_seconds", "process_cpu_usage_percent", "memory_peak_delta_bytes")
WEIGHTS = (0.7, 0.2, 0.1)


def normalized(values):
    low, high = min(values), max(values)
    return [0.0 if high == low else (value - low) / (high - low) for value in values]


def main():
    parser = argparse.ArgumentParser(description="Label raw benchmark rows by best weighted performance per file-size round.")
    parser.add_argument("input", nargs="?", default="raw_dataset.csv")
    parser.add_argument("output", nargs="?", default="labeled_dataset.csv")
    args = parser.parse_args()
    src, dst = Path(args.input), Path(args.output)
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            parser.error("input CSV has no header")
        required = {"file_size_bytes", "round_id", "algorithm", *METRICS, "throughput_mb_per_sec"}
        missing = required - set(reader.fieldnames)
        if missing:
            parser.error(f"missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    groups = defaultdict(list)
    for row in rows:
        try:
            values = [float(row[column]) for column in (*METRICS, "throughput_mb_per_sec")]
            if not all(math.isfinite(v) for v in values) or any(v < 0 for v in values):
                raise ValueError("metrics must be finite and nonnegative")
            size, round_id = int(row["file_size_bytes"]), int(row["round_id"])
            algorithm = row["algorithm"]
            if size <= 0 or round_id <= 0 or algorithm not in ALGORITHMS:
                raise ValueError("invalid size, round, or algorithm")
        except (ValueError, TypeError) as exc:
            parser.error(f"invalid row: {exc}")
        groups[(size, round_id)].append(row)

    labels = {}
    for key, group in groups.items():
        if len(group) != len(ALGORITHMS) or {r["algorithm"] for r in group} != ALGORITHMS:
            parser.error(f"group {key} must contain exactly one row for each of the four algorithms")
        if len({r["algorithm"] for r in group}) != len(group):
            parser.error(f"duplicate algorithm in group {key}")
        columns = [[float(r[m]) for r in group] for m in METRICS]
        norm = [normalized(column) for column in columns]
        scores = [sum(WEIGHTS[i] * norm[i][j] for i in range(3)) for j in range(len(group))]
        best = min(range(len(group)), key=lambda j: (scores[j], -float(group[j]["throughput_mb_per_sec"]), group[j]["algorithm"]))
        labels[key] = (group[best]["algorithm"], {r["algorithm"]: scores[j] for j, r in enumerate(group)})

    dst.parent.mkdir(parents=True, exist_ok=True)
    fields = list(reader.fieldnames) + ["selection_score", "optimal_algorithm"]
    with dst.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            label, scores = labels[(int(row["file_size_bytes"]), int(row["round_id"]))]
            row["selection_score"] = scores[row["algorithm"]]
            row["optimal_algorithm"] = label
            writer.writerow(row)
    print(f"Labeled {len(rows)} rows across {len(groups)} size/round groups -> {dst}")


if __name__ == "__main__":
    main()
