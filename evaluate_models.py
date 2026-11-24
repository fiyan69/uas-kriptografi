import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.tree import DecisionTreeClassifier

FEATURES = ("file_size_bytes", "system_cpu_usage_percent", "initial_ram_usage_percent")
CLASSES = ("AES-128-CTR", "AES-256-CTR", "ChaCha20", "3DES-CTR")


def load_rounds(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"file_size_bytes", "round_id", "algorithm", "optimal_algorithm", *FEATURES[1:]}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        groups = defaultdict(list)
        for row in reader:
            groups[(row["file_size_bytes"], row["round_id"])].append(row)
    samples = []
    for key, group in groups.items():
        if len(group) != 4 or {r["algorithm"] for r in group} != set(CLASSES):
            raise ValueError(f"Incomplete algorithm set in round {key}")
        labels = {r["optimal_algorithm"] for r in group}
        if len(labels) != 1 or not labels.issubset(CLASSES):
            raise ValueError(f"Inconsistent or invalid label in round {key}")
        samples.append(([
            float(group[0]["file_size_bytes"]),
            float(group[0]["system_cpu_usage_percent"]),
            float(group[0]["initial_ram_usage_percent"]),
        ], labels.pop()))
    return samples


def metrics(y_true, y_pred, classes):
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average="macro", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision),
        "recall_macro": float(recall),
        "f1_macro": float(f1),
        "confusion_matrix_labels": list(classes),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=classes).tolist(),
    }


def fit_if_else(x_train, y_train):
    sizes = sorted(set(x_train[:, 0]))
    candidates = [None, *[(left + right) / 2 for left, right in zip(sizes, sizes[1:])]]
    best = None
    for threshold in candidates:
        sides = x_train[:, 0] > threshold if threshold is not None else np.zeros(len(y_train), dtype=bool)
        mapping = {}
        predictions = []
        for side in (False, True):
            labels = y_train[sides == side]
            if len(labels):
                counts = {label: int(np.sum(labels == label)) for label in set(labels)}
                mapping[side] = min(counts, key=lambda label: (-counts[label], label))
        predictions = [mapping[bool(side)] for side in sides]
        score = accuracy_score(y_train, predictions)
        if best is None or score > best[0]:
            best = (score, threshold, mapping)
    return best[1], best[2]


def predict_if_else(x, fitted):
    threshold, mapping = fitted
    return np.asarray([mapping[bool(threshold is not None and row[0] > threshold)] for row in x])


def five_fold_cv(samples, n_splits=5):
    x = np.asarray([s[0] for s in samples], dtype=float)
    y = np.asarray([s[1] for s in samples], dtype=str)
    classes = tuple(label for label in CLASSES if np.any(y == label))
    split = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    model_names = ["static_if_else_baseline", "decision_tree", "random_forest"]
    truth = {name: [] for name in model_names}
    predictions = {name: [] for name in model_names}
    folds = []
    for fold_id, (train_i, test_i) in enumerate(split.split(x, y), 1):
        x_train, x_test, y_train, y_test = x[train_i], x[test_i], y[train_i], y[test_i]
        fitted_rule = fit_if_else(x_train, y_train)
        fold_predictions = {"static_if_else_baseline": predict_if_else(x_test, fitted_rule)}
        for name, model in make_models().items():
            if name == "majority_baseline":
                continue
            model.fit(x_train, y_train)
            fold_predictions[name] = model.predict(x_test)
        folds.append({
            "fold": fold_id,
            "train_count": len(train_i),
            "test_count": len(test_i),
            "if_else_threshold_file_size_bytes": fitted_rule[0],
            "models": {name: metrics(y_test, pred, classes) for name, pred in fold_predictions.items()},
        })
        for name, pred in fold_predictions.items():
            truth[name].extend(y_test.tolist())
            predictions[name].extend(pred.tolist())
    return {
        "method": "5-fold stratified CV, shuffle=True, random_state=42; folds at round/sample level",
        "folds": folds,
        "overall": {name: metrics(truth[name], predictions[name], classes) for name in model_names},
    }


def make_models():
    return {
        "majority_baseline": DummyClassifier(strategy="most_frequent"),
        "decision_tree": DecisionTreeClassifier(max_depth=4, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=2, random_state=42, n_jobs=1),
    }


def leave_one_size_out(samples):
    sizes = sorted({int(sample[0][0]) for sample in samples})
    folds = {}
    all_y, all_predictions = {name: [] for name in make_models()}, {name: [] for name in make_models()}
    for held_out in sizes:
        train = [sample for sample in samples if int(sample[0][0]) != held_out]
        test = [sample for sample in samples if int(sample[0][0]) == held_out]
        x_train = np.asarray([s[0] for s in train], dtype=float)
        y_train = np.asarray([s[1] for s in train], dtype=str)
        x_test = np.asarray([s[0] for s in test], dtype=float)
        y_test = np.asarray([s[1] for s in test], dtype=str)
        if not len(train) or not len(test) or len(set(y_train)) < 2:
            raise ValueError(f"Insufficient training classes when holding out size {held_out}")
        classes = tuple(label for label in CLASSES if np.any(y_test == label))
        fold = {"held_out_size": str(held_out), "train_count": len(train), "test_count": len(test), "train_sizes": sorted({str(int(s[0][0])) for s in train}), "test_sizes": sorted({str(int(s[0][0])) for s in test}), "models": {}}
        for name, model in make_models().items():
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            fold["models"][name] = metrics(y_test, pred, classes)
            all_y[name].extend(y_test.tolist())
            all_predictions[name].extend(pred.tolist())
        folds[str(held_out)] = fold
    overall_classes = tuple(label for label in CLASSES if any(y == label for values in all_y.values() for y in values))
    overall = {name: metrics(all_y[name], all_predictions[name], overall_classes) for name in all_y}
    return {"method": "leave-one-file-size-out cross-validation", "folds": folds, "overall": overall}


def main():
    parser = argparse.ArgumentParser(description="Evaluate round-level encryption labels with stratified holdout and majority baseline.")
    parser.add_argument("input", nargs="?", default="labeled_dataset.csv")
    parser.add_argument("output", nargs="?", default="model_evaluation.json")
    args = parser.parse_args()
    samples = load_rounds(args.input)
    x = np.asarray([item[0] for item in samples], dtype=float)
    y = np.asarray([item[1] for item in samples], dtype=str)
    counts = {label: int(np.sum(y == label)) for label in CLASSES if np.any(y == label)}
    if len(samples) < 10 or len(counts) < 2 or min(counts.values()) < 2:
        parser.error("Need at least 10 round samples and at least 2 samples per represented class")
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    models = {
        "decision_tree": DecisionTreeClassifier(max_depth=4, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=2, random_state=42, n_jobs=1),
    }
    test_classes = tuple(label for label in CLASSES if np.any(y_test == label))
    results = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        results[name] = metrics(y_test, model.predict(x_test), test_classes)
    static_rule = fit_if_else(x_train, y_train)
    results["static_if_else_baseline"] = metrics(y_test, predict_if_else(x_test, static_rule), test_classes)
    report = {
        "input": str(Path(args.input)),
        "sample_unit": "one sample per file-size and round; four algorithm rows aggregated",
        "sample_count": int(len(samples)),
        "train_count": int(len(y_train)),
        "test_count": int(len(y_test)),
        "feature_columns": list(FEATURES),
        "label_column": "optimal_algorithm",
        "class_counts": counts,
        "split": {"method": "stratified 80/20 holdout", "random_state": 42},
        "models": results,
        "five_fold_cv": five_fold_cv(samples),
        "unseen_file_size_generalization": leave_one_size_out(samples),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved report: {out}")


if __name__ == "__main__":
    main()
