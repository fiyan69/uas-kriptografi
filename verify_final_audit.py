import copy
import csv
import json
import hashlib
from collections import Counter
from pathlib import Path

import numpy as np
from evaluate_models_final import load_raw, evaluate_split, metric_report, make_samples

ROOT = Path(__file__).resolve().parent
RAW_HASH = 'b95ddcd73a6fd19cfcfc6190e9c693b3250baf1d5f4d8f56e6a7344be9091096'
OLD_HASH = '30ec8cc8859c4c2cadc58502e56fb1781f3467262e02d040ed900300f9c25188'


def main():
    report_path = ROOT / 'output_cpu_corrected/evaluation_final.json'
    j = json.loads(report_path.read_text(encoding='utf-8'))
    rows, _ = load_raw(ROOT / 'raw_dataset_cpu_corrected.csv')
    assert hashlib.sha256((ROOT / 'raw_dataset_cpu_corrected.csv').read_bytes()).hexdigest() == RAW_HASH
    assert hashlib.sha256((ROOT / 'raw_dataset.csv').read_bytes()).hexdigest() == OLD_HASH
    assert len(rows) == 720
    train_ids = {tuple(x) for x in j['holdout']['train_ids']}
    holdout_ids = {tuple(x) for x in j['holdout']['test_ids']}
    seen = []
    for f in j['cv']['folds']:
        a, b = {tuple(x) for x in f['train_ids']}, {tuple(x) for x in f['test_ids']}
        assert not a & b and not (a | b) & holdout_ids and (a | b) == train_ids
        seen.extend(b)
    assert set(seen) == train_ids and len(seen) == len(train_ids) == 144
    for f in [j['holdout'], *j['cv']['folds'], *j['leave_one_size_out']['folds']]:
        for n, pred in f['predictions'].items():
            assert metric_report(f['truth'], pred) == f['models'][n]
        for partition in ('train', 'test'):
            evidence = f['measurement_evidence'][partition]
            assert len(evidence) == f[partition + '_count'] * 4
            grouped = Counter(tuple(x['id']) for x in evidence)
            assert all(count == 4 for count in grouped.values())
            reconstructed = []
            for e in evidence:
                reconstructed.append({'run_id': e['id'][0], 'file_size_bytes': e['id'][1], 'round_id': e['id'][2], 'trial': e['trial'], 'algorithm': e['algorithm'], 'system_cpu_usage_percent': '0', 'initial_ram_usage_percent': '0', **e['after']})
            labels = {tuple(s['id']): s for s in make_samples(reconstructed)}
            for e in evidence:
                s = labels[tuple(e['id'])]
                assert s['y'] == e['optimal_algorithm']
                assert abs(s['scores'][e['algorithm']] - e['selection_score']) < 1e-12
            for e in evidence:
                expected = int(e['id'][1]) / 1048576 / e['after']['execution_time_seconds']
                assert np.isclose(expected, e['after']['throughput_mb_per_sec'], rtol=1e-12)
        assert f['logistic_scaler']['sample_count'] == f['train_count']
    for f in j['leave_one_size_out']['folds']:
        for e in f['measurement_evidence']['test']:
            assert e['unseen_stratum'] == 'true'
            for metric in ('execution_time_seconds', 'process_cpu_usage_percent', 'memory_peak_delta_bytes'):
                assert e['before'][metric] == e['after'][metric]
    f = j['cv']['folds'][0]
    ti, vi = {tuple(x) for x in f['train_ids']}, {tuple(x) for x in f['test_ids']}
    changed = copy.deepcopy(rows)
    for r in changed:
        if (r['run_id'],r['file_size_bytes'],r['round_id']) in vi:
            r['execution_time_seconds'] = '999999'
            r['system_cpu_usage_percent'] = '99'
    changed_fit = evaluate_split(changed, ti, vi, f['split'])
    for name in ('bounds', 'baseline_rule', 'logistic_scaler'):
        assert changed_fit[name] == f[name], name
    assert report_path.read_bytes() == (ROOT / 'output_cpu_corrected_recheck/evaluation_final.json').read_bytes()
    summary = dict(status='PASS', raw_rows=720, rounds=180, cv_rounds=144, holdout_rounds=36,
                   checks=['raw hashes preserved','complete grouped partitions','CV excludes holdout','each train round tested once','metrics reproduced from predictions','throughput consistent','unseen strata raw','test mutation leaves bounds scaler rule unchanged','two-run report byte identical'])
    (ROOT / 'output_cpu_corrected/audit_checks.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
