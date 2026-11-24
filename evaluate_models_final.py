from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ALGORITHMS = ("AES-128-CTR", "AES-256-CTR", "ChaCha20", "3DES-CTR")
METRICS = ("execution_time_seconds", "process_cpu_usage_percent", "memory_peak_delta_bytes")
FEATURES = ("file_size_bytes", "system_cpu_usage_percent", "initial_ram_usage_percent")
WEIGHTS = (0.7, 0.2, 0.1)
SEED = 42
EXPECTED_RAW_SHA256 = "30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188"


def _num(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise ValueError(f"non-finite {key}")
    return value


def raw_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_raw(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = set(reader.fieldnames or ())
    required = {"run_id", "round_id", "trial", "file_size_bytes", "algorithm", "throughput_mb_per_sec", *FEATURES, *METRICS}
    missing = required - fields
    if missing or not rows:
        raise ValueError(f"missing/empty input: {sorted(missing)}")
    groups = defaultdict(list)
    for row in rows:
        if row["algorithm"] not in ALGORITHMS:
            raise ValueError(f"unexpected algorithm {row['algorithm']}")
        for key in METRICS + ("file_size_bytes", "trial", "throughput_mb_per_sec", *FEATURES[1:]):
            if _num(row, key) < 0:
                raise ValueError(f"negative {key}")
        groups[(row["run_id"], row["file_size_bytes"], row["round_id"])].append(row)
    if any(len(g) != 4 or {r["algorithm"] for r in g} != set(ALGORITHMS) for g in groups.values()):
        raise ValueError("each run_id/file_size/round group must contain exactly four algorithms")
    return rows, list(reader.fieldnames)


def iqr_fence(values):
    values = sorted(values)
    mid = len(values) // 2
    q1 = median(values[:mid])
    q3 = median(values[(len(values) + 1) // 2:])
    span = q3 - q1
    return q1 - 1.5 * span, q3 + 1.5 * span


def fit_fences(rows):
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for metric in METRICS:
            grouped[(row["file_size_bytes"], row["algorithm"])][metric].append(_num(row, metric))
    # Each stratum normally has 30 observations; no algorithm-wide fallback is permitted.
    return {
        (size, algo, metric): iqr_fence(values)
        for (size, algo), metrics in grouped.items()
        for metric, values in metrics.items()
        if len(values) >= 4
    }


def transform(rows, bounds):
    out = []
    for source in rows:
        row = dict(source)
        flags = []
        unseen = False
        for metric in METRICS:
            key = (row["file_size_bytes"], row["algorithm"], metric)
            value = _num(row, metric)
            if key not in bounds:
                unseen = True
                continue  # approved policy: unseen size/algorithm strata remain raw
            lo, hi = bounds[key]
            if value < lo or value > hi:
                flags.append(metric)
            row[metric] = min(hi, max(lo, value))
        row["outlier_metrics"] = ";".join(flags)
        row["unseen_stratum"] = "true" if unseen else "false"
        # Throughput is always derived from the processed time, never independently clipped.
        row["throughput_mb_per_sec"] = str(_num(row, "file_size_bytes") / 1048576.0 / _num(row, "execution_time_seconds"))
        out.append(row)
    return out


def make_samples(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["run_id"], row["file_size_bytes"], row["round_id"])].append(row)
    samples = []
    for key, group in sorted(groups.items(), key=lambda item: tuple(str(x) for x in item[0])):
        group = sorted(group, key=lambda r: int(r["trial"]))
        if len(group) != 4 or {r["algorithm"] for r in group} != set(ALGORITHMS):
            raise ValueError(f"incomplete group {key}")
        vals = {metric: [_num(r, metric) for r in group] for metric in METRICS}
        normalized = {}
        for metric in METRICS:
            lo, hi = min(vals[metric]), max(vals[metric])
            normalized[metric] = [0.0 if hi == lo else (x - lo) / (hi - lo) for x in vals[metric]]
        scores = [sum(weight * normalized[metric][i] for weight, metric in zip(WEIGHTS, METRICS)) for i in range(4)]
        winner = min(range(4), key=lambda i: (scores[i], -_num(group[i], "throughput_mb_per_sec"), group[i]["algorithm"]))
        first = group[0]  # prospective feature: first trial observation only
        samples.append({
            "id": list(key), "x": [_num(first, feature) for feature in FEATURES],
            "y": group[winner]["algorithm"], "scores": {r["algorithm"]: scores[i] for i, r in enumerate(group)},
        })
    return samples


def metric_report(y, pred):
    labels = [c for c in ALGORITHMS if c in set(y) | set(pred)]
    p, r, f, _ = precision_recall_fscore_support(y, pred, labels=labels, average="macro", zero_division=0)
    return {"accuracy": float(accuracy_score(y, pred)), "precision_macro": float(p), "recall_macro": float(r), "f1_macro": float(f),
            "confusion_matrix_labels": labels, "confusion_matrix": confusion_matrix(y, pred, labels=labels).tolist(),
            "actual_classes": sorted(set(y)), "predicted_classes": sorted(set(pred)),
            "absent_expected_classes_in_truth": [c for c in ALGORITHMS if c not in set(y)]}


def fit_rule(x, y):
    sizes = sorted(set(x[:, 0]))
    candidates = [None] + [(a + b) / 2 for a, b in zip(sizes, sizes[1:])]
    best = None
    for threshold in candidates:
        branch = np.zeros(len(y), dtype=bool) if threshold is None else x[:, 0] > threshold
        mapping = {}
        for side in (False, True):
            vals = y[branch == side]
            if len(vals):
                counts = Counter(vals)
                mapping[str(side)] = min(counts, key=lambda c: (-counts[c], c))
        pred = np.array([mapping[str(bool(v))] for v in branch])
        score = float(accuracy_score(y, pred))
        candidate = (score, threshold, mapping)
        if best is None or (score, -(threshold if threshold is not None else -math.inf), str(mapping)) > (best[0], -(best[1] if best[1] is not None else -math.inf), str(best[2])):
            best = candidate
    return {"threshold": best[1], "branch_class": best[2], "train_accuracy": best[0]}


def predict_rule(x, rule):
    threshold = rule["threshold"]
    return np.array([rule["branch_class"][str(bool(threshold is not None and row[0] > threshold))] for row in x])


def model_defs():
    return {
        "decision_tree": DecisionTreeClassifier(max_depth=4, random_state=SEED),
        "random_forest": RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=2, random_state=SEED, n_jobs=1),
        "logistic_regression": Pipeline([("scaler", StandardScaler()), ("classifier", LogisticRegression(max_iter=2000, random_state=SEED))]),
    }


def evaluate_split(raw_rows, train_ids, test_ids, split_name):
    train_rows = [r for r in raw_rows if tuple((r["run_id"], r["file_size_bytes"], r["round_id"])) in train_ids]
    test_rows = [r for r in raw_rows if tuple((r["run_id"], r["file_size_bytes"], r["round_id"])) in test_ids]
    bounds = fit_fences(train_rows)
    train_samples = make_samples(transform(train_rows, bounds))
    test_samples = make_samples(transform(test_rows, bounds))
    x, y = np.array([s["x"] for s in train_samples]), np.array([s["y"] for s in train_samples])
    xt, yt = np.array([s["x"] for s in test_samples]), np.array([s["y"] for s in test_samples])
    rule = fit_rule(x, y)
    models = {"static_if_else_baseline": (None, predict_rule(xt, rule))}
    for name, model in model_defs().items():
        model.fit(x, y)
        models[name] = (model, model.predict(xt))
    predictions = {name: pred.tolist() for name, (_, pred) in models.items()}
    reports = {name: metric_report(yt.tolist(), pred.tolist()) for name, (_, pred) in models.items()}
    transformed_train = transform(train_rows, bounds)
    transformed_test = transform(test_rows, bounds)
    def evidence(source_rows, processed_rows, samples):
        by_id = {tuple(s["id"]): s for s in samples}
        result = []
        for raw, processed in zip(source_rows, processed_rows):
            key = (raw["run_id"], raw["file_size_bytes"], raw["round_id"])
            sample = by_id[key]
            result.append({"id": list(key), "trial": raw["trial"], "algorithm": raw["algorithm"],
                           "before": {m: _num(raw, m) for m in (*METRICS, "throughput_mb_per_sec")},
                           "after": {m: _num(processed, m) for m in (*METRICS, "throughput_mb_per_sec")},
                           "outlier_metrics": processed["outlier_metrics"], "unseen_stratum": processed["unseen_stratum"],
                           "selection_score": sample["scores"][raw["algorithm"]], "optimal_algorithm": sample["y"]})
        return result
    scaler = models["logistic_regression"][0].named_steps["scaler"]
    return {"split": split_name, "measurement_evidence": {"train": evidence(train_rows, transformed_train, train_samples), "test": evidence(test_rows, transformed_test, test_samples)},
            "train_class_counts": dict(Counter(y.tolist())), "test_class_counts": dict(Counter(yt.tolist())),
            "logistic_scaler": {"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(), "sample_count": int(scaler.n_samples_seen_)},
            "train_ids": [list(x) for x in sorted(train_ids)], "test_ids": [list(x) for x in sorted(test_ids)],
            "train_count": len(train_samples), "test_count": len(test_samples), "train_row_count": len(train_rows), "test_row_count": len(test_rows),
            "bounds": {"|".join(map(str, k)): list(v) for k, v in sorted(bounds.items())}, "baseline_rule": rule,
            "test_flagged_rows": sum(bool(r["outlier_metrics"]) for r in transformed_test),
            "test_unseen_stratum_rows": sum(r["unseen_stratum"] == "true" for r in transformed_test),
            "truth": yt.tolist(), "predictions": predictions, "models": reports}


def pooled_reports(folds):
    out = {}
    for name in folds[0]["predictions"]:
        truth, pred = [], []
        for fold in folds:
            truth += fold["truth"]
            pred += fold["predictions"][name]
        out[name] = metric_report(truth, pred)
    return out


def mean_std(folds):
    out = {}
    for name in folds[0]["models"]:
        values = {metric: [f["models"][name][metric] for f in folds] for metric in ("accuracy", "precision_macro", "recall_macro", "f1_macro")}
        out[name] = {metric: {"mean": float(np.mean(v)), "std": float(np.std(v, ddof=0))} for metric, v in values.items()}
    return out


def write_csv(rows, path, extra_fields):
    fields = list(rows[0])
    for field in extra_fields:
        if field not in fields: fields.append(field)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="raw_dataset.csv")
    parser.add_argument("output_dir", nargs="?", default="output_final")
    parser.add_argument("--expected-sha256", default=EXPECTED_RAW_SHA256)
    args = parser.parse_args()
    input_path, output_dir = Path(args.input), Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, fields = load_raw(input_path)
    raw_hash = raw_sha256(input_path)
    if raw_hash != args.expected_sha256:
        raise ValueError(f"raw SHA256 mismatch: {raw_hash}")
    all_ids = sorted({(r["run_id"], r["file_size_bytes"], r["round_id"]) for r in rows})
    train_idx, test_idx = train_test_split(np.arange(len(all_ids)), test_size=0.2, random_state=SEED, shuffle=True)
    holdout_train = {all_ids[i] for i in train_idx}; holdout_test = {all_ids[i] for i in test_idx}
    holdout = evaluate_split(rows, holdout_train, holdout_test, "holdout_80_20_seed42")
    cv_folds = []
    cv_truth_ids = []
    for fold_no, (ti, vi) in enumerate(KFold(5, shuffle=True, random_state=SEED).split(sorted(holdout_train)), 1):
        cv_train = {sorted(holdout_train)[i] for i in ti}; cv_test = {sorted(holdout_train)[i] for i in vi}
        cv_folds.append(evaluate_split(rows, cv_train, cv_test, f"cv_fold_{fold_no}"))
        cv_truth_ids.extend(cv_test)
    cv = {"method": "5-fold CV only within 80% training partition", "folds": cv_folds, "pooled": pooled_reports(cv_folds), "mean_std": mean_std(cv_folds)}
    loso_folds = []
    for size in sorted({r["file_size_bytes"] for r in rows}, key=int):
        test_ids = {x for x in all_ids if x[1] == size}; train_ids = set(all_ids) - test_ids
        loso_folds.append(evaluate_split(rows, train_ids, test_ids, f"leave_size_{size}"))
    loso = {"method": "leave-one-file-size-out; unseen size remains raw and flagged", "folds": loso_folds, "pooled": pooled_reports(loso_folds)}
    full_processed = transform(rows, fit_fences(rows))
    full_samples = make_samples(full_processed)
    label_by_id = {tuple(s["id"]): s for s in full_samples}
    descriptive_rows = []
    for row in full_processed:
        sample = label_by_id[(row["run_id"], row["file_size_bytes"], row["round_id"])]
        row = dict(row); row["selection_score"] = str(sample["scores"][row["algorithm"]]); row["optimal_algorithm"] = sample["y"]
        descriptive_rows.append(row)
    write_csv(descriptive_rows, output_dir / "descriptive_preprocessed.csv", ["outlier_metrics", "unseen_stratum", "selection_score", "optimal_algorithm"])
    write_csv(descriptive_rows, output_dir / "labeled_dataset_final.csv", ["outlier_metrics", "unseen_stratum", "selection_score", "optimal_algorithm"])
    report = {"protocol": {"seed": SEED, "data_source_status": "corrected_cpu_benchmark_evaluated" if raw_hash != EXPECTED_RAW_SHA256 else "historical_raw_provisional_pending_cpu_measurement_decision", "raw_sha256": raw_hash, "raw_rows": len(rows), "round_groups": len(all_ids), "train_rounds": len(holdout_train), "holdout_rounds": len(holdout_test), "cv_rounds": len(holdout_train), "cv_folds": 5, "cv_rounds_per_fold_test": [len(f["test_ids"]) for f in cv_folds], "features": list(FEATURES), "label_weights": dict(zip(METRICS, WEIGHTS)), "feature_policy": "first trial observation sorted by trial", "unseen_size_policy": "raw metrics retained, no cross-size IQR fallback, flagged", "holdout_previously_inspected": True, "absent_3DES_disclosure": "3DES-CTR may be absent from truth; no synthetic labels"},
              "descriptive_full_data": {"class_counts": dict(sorted(Counter(s["y"] for s in full_samples).items())), "flagged_rows": sum(bool(r["outlier_metrics"]) for r in full_processed)}, "holdout": holdout, "cv": cv, "leave_one_size_out": loso}
    (output_dir / "evaluation_final.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"raw_sha256": raw_hash, "raw_rows": len(rows), "round_groups": len(all_ids), "holdout": holdout["models"], "cv_pooled": cv["pooled"], "output_dir": str(output_dir)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
