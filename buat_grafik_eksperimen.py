"""Render figures directly from canonical measured CSV and stored evaluation; no retraining."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'grafik_hasil_eksperimen'
ALGORITHMS = ['AES-128-CTR', 'AES-256-CTR', 'ChaCha20', '3DES-CTR']
COLORS = ['#0072B2', '#E69F00', '#009E73', '#CC79A7']
MODELS = ['static_if_else_baseline', 'decision_tree', 'random_forest', 'logistic_regression']
MODEL_NAMES = ['If-else', 'Decision Tree', 'Random Forest', 'Logistic Regression']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300})


def save(fig, name):
    fig.savefig(OUT / (name + '.png'), bbox_inches='tight', facecolor='white')
    fig.savefig(OUT / (name + '.svg'), bbox_inches='tight', facecolor='white')
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    raw_path = ROOT / 'raw_dataset_cpu_corrected.csv'
    eval_path = ROOT / 'output_cpu_corrected/evaluation_final.json'
    label_path = ROOT / 'labeled_dataset.csv'
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (raw_path, eval_path, label_path)}
    assert hashes[raw_path.name] == 'b95ddcd73a6fd19cfcfc6190e9c693b3250baf1d5f4d8f56e6a7344be9091096'
    with raw_path.open(newline='', encoding='utf-8') as f:
        raw = list(csv.DictReader(f))
    with label_path.open(newline='', encoding='utf-8') as f:
        labeled = list(csv.DictReader(f))
    report = json.loads(eval_path.read_text(encoding='utf-8'))
    assert len(raw) == len(labeled) == 720
    sizes = sorted({int(r['file_size_bytes']) for r in raw})
    size_names = ['1 KiB', '10 KiB', '100 KiB', '1 MiB', '10 MiB', '50 MiB']
    assert sizes == [1024, 10240, 102400, 1048576, 10485760, 52428800]
    groups = defaultdict(list)
    for r in raw:
        groups[(int(r['file_size_bytes']), r['algorithm'])].append(r)
    summaries = []
    metrics = [
        ('execution_time_seconds', 'Waktu enkripsi', 'Waktu per enkripsi (ms; skala log)', 1000, 'log'),
        ('throughput_mb_per_sec', 'Throughput enkripsi', 'Throughput (MiB/s; skala log)', 1, 'log'),
        ('process_cpu_usage_percent', 'Penggunaan CPU thread enkripsi', 'CPU thread (% dari satu thread)', 1, 'linear'),
        ('memory_peak_delta_bytes', 'Delta puncak memori proses', 'Delta peak RSS (MiB)', 1 / 1048576, 'linear'),
    ]
    for number, (metric, title, ylabel, factor, scale) in enumerate(metrics, 1):
        fig, ax = plt.subplots(figsize=(9, 5.2))
        for algorithm, color in zip(ALGORITHMS, COLORS):
            med, low, high = [], [], []
            for size in sizes:
                values = np.array([float(r[metric]) * factor for r in groups[(size, algorithm)]])
                assert len(values) == 30 and np.isfinite(values).all()
                q1, q2, q3 = np.percentile(values, [25, 50, 75])
                med.append(q2); low.append(q1); high.append(q3)
                summaries.append(dict(metric=metric, file_size_bytes=size, algorithm=algorithm, n=30, displayed_unit=ylabel, q1=float(q1), median=float(q2), q3=float(q3)))
            if scale == 'log':
                assert min(low) > 0
            ax.plot(range(6), med, marker='o', label=algorithm, color=color, linewidth=1.8)
            ax.fill_between(range(6), low, high, color=color, alpha=.15)
        ax.set_xticks(range(6), size_names); ax.set_yscale(scale)
        if scale == 'linear': ax.set_ylim(bottom=0)
        ax.set(xlabel='Ukuran payload (kategori berurutan)', ylabel=ylabel, title=title + '\nMedian dan rentang Q1–Q3 dari 30 putaran; data mentah')
        ax.grid(axis='y', alpha=.25); ax.legend(ncol=2, fontsize=9)
        fig.text(.02, .01, 'Area berwarna = IQR, bukan confidence interval. Satu perangkat; encrypt-only.', fontsize=8)
        fig.tight_layout(rect=(0,.04,1,1)); save(fig, f'{number:02d}_{metric}')
    with (OUT/'ringkasan_benchmark.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0])); w.writeheader(); w.writerows(summaries)

    label_groups=defaultdict(set)
    for r in labeled: label_groups[(r['run_id'],r['file_size_bytes'],r['round_id'])].add(r['optimal_algorithm'])
    assert len(label_groups)==180 and all(len(v)==1 for v in label_groups.values())
    counts=Counter(next(iter(v)) for v in label_groups.values())
    assert dict(sorted(counts.items()))==report['descriptive_full_data']['class_counts']
    fig,ax=plt.subplots(figsize=(8,4.8)); bars=ax.bar(ALGORITHMS,[counts[a] for a in ALGORITHMS],color=COLORS)
    ax.bar_label(bars,padding=4);ax.set_ylim(0,max(counts.values())*1.2)
    ax.set(ylabel='Jumlah putaran (total 180)',title='Distribusi label algoritma terbaik\nDataset deskriptif penuh setelah winsorization')
    fig.text(.02,.01,'Satu putaran = satu label; bukan 720 label independen. 3DES diuji tetapi tidak pernah menang.',fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1));save(fig,'05_distribusi_label')

    schemes=[('cv',report['cv']['pooled'],'CV 5-fold pada 144 putaran train; prediksi gabungan'),('holdout',report['holdout']['models'],'Holdout 36 putaran; terpisah dari CV'),('ukuran_baru',report['leave_one_size_out']['pooled'],'Leave-one-file-size-out; 180 prediksi gabungan')]
    metric_table=[]
    for index,(scheme,models,subtitle) in enumerate(schemes,6):
        fig,ax=plt.subplots(figsize=(9,5));x=np.arange(4);width=.34
        for offset,key,color,name in [(-width/2,'accuracy','#0072B2','Akurasi'),(width/2,'f1_macro','#E69F00','Macro-F1')]:
            vals=[models[n][key]*100 for n in MODELS]
            bars=ax.bar(x+offset,vals,width,color=color,label=name);ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=8)
        ax.set_xticks(x,MODEL_NAMES);ax.set_ylim(0,100);ax.set(ylabel='Skor (%)',title='Perbandingan model\n'+subtitle);ax.legend();ax.grid(axis='y',alpha=.2)
        fig.text(.02,.01,'Nilai pooled, bukan rata-rata F1 antar-fold. Perbandingan eksploratif; tidak menunjukkan keunggulan signifikan.',fontsize=8)
        fig.tight_layout(rect=(0,.04,1,1));save(fig,f'{index:02d}_model_{scheme}')
        fig,axes=plt.subplots(2,2,figsize=(10,9));vmax=max(max(map(max,models[n]['confusion_matrix'])) for n in MODELS)
        for ax,name,label in zip(axes.flat,MODELS,MODEL_NAMES):
            m=models[name];matrix=np.asarray(m['confusion_matrix']);labels=m['confusion_matrix_labels']
            assert matrix.sum()==(144 if scheme=='cv' else 36 if scheme=='holdout' else 180)
            ax.imshow(matrix,cmap='Blues',vmin=0,vmax=vmax)
            for i in range(len(labels)):
                for j in range(len(labels)):
                    ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>vmax*.55 else 'black')
            ax.set_xticks(range(len(labels)),labels,rotation=25,ha='right',fontsize=8);ax.set_yticks(range(len(labels)),labels,fontsize=8)
            ax.set(xlabel='Prediksi',ylabel='Label aktual',title=label)
        fig.suptitle('Confusion matrix (jumlah putaran)\n'+subtitle,fontsize=12)
        fig.text(.02,.01,'Baris = aktual; kolom = prediksi. Skala warna sama antar-model pada gambar ini. 3DES tidak ada pada label.',fontsize=8)
        fig.tight_layout(rect=(0,.04,1,.94));save(fig,f'{index+3:02d}_confusion_matrix_{scheme}')
        for name in MODELS:
            metric_table.append({'scheme':scheme,'model':name,**{key:models[name][key] for key in ('accuracy','precision_macro','recall_macro','f1_macro')}})
    with (OUT/'ringkasan_metrik_model.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(metric_table[0]));w.writeheader();w.writerows(metric_table)
    # Fold-level variability is displayed explicitly, separate from pooled model plots.
    fig,ax=plt.subplots(figsize=(9,5))
    for name,label,color in zip(MODELS,MODEL_NAMES,COLORS):
        vals=[f['models'][name]['accuracy']*100 for f in report['cv']['folds']]
        ax.plot(range(1,6),vals,marker='o',label=label,color=color)
    ax.set(xticks=range(1,6),ylim=(0,100),xlabel='Fold (hanya bagian train)',ylabel='Akurasi (%)',title='Variasi akurasi antar-fold\nUkuran test fold: 29, 29, 29, 29, 28 putaran')
    ax.legend(ncol=2);ax.grid(axis='y',alpha=.2);fig.tight_layout();save(fig,'12_variasi_akurasi_cv')
    manifest={'sources_sha256':hashes,'raw_rows':720,'independent_rounds':180,'summary_quantiles':'numpy.percentile default linear; descriptive display only, not IQR fences used for winsorization','benchmark_source':'raw measurements, no clipping','figures':sorted(p.name for p in OUT.glob('*.png')),'model_values':'directly from canonical evaluation JSON; no retraining'}
    for path in (raw_path,eval_path,label_path):assert hashlib.sha256(path.read_bytes()).hexdigest()==hashes[path.name]
    (OUT/'manifest_grafik.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    assert len(manifest['figures'])==12
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
