import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import KFold, train_test_split
from sklearn.tree import DecisionTreeClassifier

METRICS = ("execution_time_seconds", "process_cpu_usage_percent", "memory_peak_delta_bytes")
WEIGHTS = (0.7, 0.2, 0.1)
CLASSES = ("AES-128-CTR", "AES-256-CTR", "ChaCha20", "3DES-CTR")
FEATURES = ("file_size_bytes", "system_cpu_usage_percent", "initial_ram_usage_percent")
ALGORITHMS = set(CLASSES)


def iqr_fence(values):
    values = sorted(values)
    q1, q3 = statistics.median(values[:len(values)//2]), statistics.median(values[(len(values)+1)//2:])
    span = q3-q1
    return q1-1.5*span, q3+1.5*span


def fit_fences(rows):
    strata, by_algo = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for row in rows:
        for metric in METRICS:
            value = float(row[metric])
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {metric}: {row[metric]}")
            strata[(row['file_size_bytes'],row['algorithm'])][metric].append(value)
            by_algo[row['algorithm']][metric].append(value)
    fences={(s,a,m):iqr_fence(v) for (s,a),cols in strata.items() for m,v in cols.items() if len(v)>=4}
    fallback={(a,m):iqr_fence(v) for a,cols in by_algo.items() for m,v in cols.items()}
    return fences, fallback


def transform(rows, fitted, fallback_unseen=True):
    fences,fallback=fitted; out=[]
    for source in rows:
        row=dict(source); tags=[]
        for metric in METRICS:
            key=(row['file_size_bytes'],row['algorithm'],metric)
            lo,hi=fences.get(key,fallback[(row['algorithm'],metric)])
            value=float(row[metric])
            if value<lo or value>hi: tags.append(metric)
            row[metric]=min(hi,max(lo,value))
        row['outlier_metrics']=';'.join(tags);out.append(row)
    return out


def make_samples(rows):
    groups=defaultdict(list)
    for row in rows: groups[(row['file_size_bytes'],row['round_id'])].append(row)
    samples=[]
    for key,g in groups.items():
        if len(g)!=4 or {r['algorithm'] for r in g}!=ALGORITHMS: raise ValueError(f'Incomplete round {key}')
        g.sort(key=lambda r:int(r['trial']));norm=[]
        for metric in METRICS:
            values=[float(r[metric]) for r in g];lo,hi=min(values),max(values)
            norm.append([0. if hi==lo else (x-lo)/(hi-lo) for x in values])
        scores=[sum(WEIGHTS[i]*norm[i][j] for i in range(3)) for j in range(4)]
        winner=min(range(4),key=lambda j:(scores[j],-float(g[j]['throughput_mb_per_sec']),g[j]['algorithm']))
        samples.append({'x':[float(g[0][name]) for name in FEATURES],'y':g[winner]['algorithm']})
    return samples


def score_report(y,pred):
    labels=tuple(c for c in CLASSES if c in set(y))
    p,r,f,_=precision_recall_fscore_support(y,pred,labels=labels,average='macro',zero_division=0)
    return {'accuracy':float(accuracy_score(y,pred)),'precision_macro':float(p),'recall_macro':float(r),'f1_macro':float(f),'confusion_matrix_labels':list(labels),'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist()}


def fit_rule(x,y):
    sizes=sorted(set(x[:,0]));best=None
    for threshold in [None,*[(a+b)/2 for a,b in zip(sizes,sizes[1:])]]:
        sides=x[:,0]>threshold if threshold is not None else np.zeros(len(y),dtype=bool); mapping={}
        for side in (False,True):
            subset=y[sides==side]
            if len(subset):
                counts=Counter(subset);mapping[side]=min(counts,key=lambda c:(-counts[c],c))
        pred=[mapping[bool(s)] for s in sides];acc=accuracy_score(y,pred)
        if best is None or acc>best[0]:best=(acc,threshold,mapping)
    return best[1],best[2]


def predict_rule(x,rule):
    threshold,mapping=rule
    return np.asarray([mapping[bool(threshold is not None and row[0]>threshold)] for row in x])


def models():
    return {'decision_tree':DecisionTreeClassifier(max_depth=4,random_state=42),'random_forest':RandomForestClassifier(n_estimators=200,max_depth=5,min_samples_leaf=2,random_state=42,n_jobs=1)}


def keys(rows): return list(dict.fromkeys((r['file_size_bytes'],r['round_id']) for r in rows))


def load_raw(path):
    with open(path,newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f);rows=list(reader);fields=set(reader.fieldnames or ())
    required={'file_size_bytes','round_id','trial','algorithm','throughput_mb_per_sec',*FEATURES[1:],*METRICS}
    if not rows or required-fields: raise ValueError(f'Empty input or missing columns: {sorted(required-fields)}')
    return rows


def evaluate(rows,train_keys,test_keys):
    train=[r for r in rows if (r['file_size_bytes'],r['round_id']) in train_keys]
    test=[r for r in rows if (r['file_size_bytes'],r['round_id']) in test_keys]
    fitted=fit_fences(train)
    a,b=make_samples(transform(train,fitted)),make_samples(transform(test,fitted))
    x=np.asarray([s['x'] for s in a]);y=np.asarray([s['y'] for s in a]);xt=np.asarray([s['x'] for s in b]);yt=np.asarray([s['y'] for s in b])
    pred={'static_if_else_baseline':predict_rule(xt,fit_rule(x,y))}
    for name,model in models().items():model.fit(x,y);pred[name]=model.predict(xt)
    result={n:score_report(yt.tolist(),p.tolist()) for n,p in pred.items()}
    tagged=sum(bool(r['outlier_metrics']) for r in transform(test,fitted))
    return result,yt.tolist(),{n:p.tolist() for n,p in pred.items()},len(a),len(b),tagged


def holdout(rows):
    allkeys=keys(rows);ti,vi=train_test_split(np.arange(len(allkeys)),test_size=.2,random_state=42)
    result,_,_,nt,nv,tag=evaluate(rows,{allkeys[i] for i in ti},{allkeys[i] for i in vi})
    return {'method':'80/20 round-group holdout, random_state=42; train-fitted IQR','train_count':nt,'test_count':nv,'test_rows_flagged':tag,'models':result}


def cv(rows):
    allkeys=keys(rows);folds=[];truth=defaultdict(list);preds=defaultdict(list)
    for i,(ti,vi) in enumerate(KFold(5,shuffle=True,random_state=42).split(allkeys),1):
        result,y,p,nt,nv,tag=evaluate(rows,{allkeys[j] for j in ti},{allkeys[j] for j in vi})
        folds.append({'fold':i,'train_count':nt,'test_count':nv,'test_rows_flagged':tag,'models':result})
        for name in result:truth[name].extend(y);preds[name].extend(p[name])
    return {'method':'5-fold KFold on complete round groups; training-only IQR fitting','folds':folds,'overall':{n:score_report(truth[n],preds[n]) for n in truth}}


def leave_size(rows):
    allkeys=keys(rows);folds=[];truth=defaultdict(list);preds=defaultdict(list)
    for size in sorted({int(k[0]) for k in allkeys}):
        vi={k for k in allkeys if int(k[0])==size};ti=set(allkeys)-vi
        result,y,p,nt,nv,tag=evaluate(rows,ti,vi)
        folds.append({'held_out_size':size,'train_count':nt,'test_count':nv,'test_rows_flagged':tag,'models':result})
        for name in result:truth[name].extend(y);preds[name].extend(p[name])
    return {'method':'leave-one-file-size-out; training-only algorithm-level fallback for unseen size','folds':folds,'overall':{n:score_report(truth[n],preds[n]) for n in truth}}


def write_descriptive(rows,path):
    transformed=transform(rows,fit_fences(rows));fields=list(rows[0])+['outlier_metrics']
    with open(path,'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in transformed:writer.writerow({**row,**{m:format(row[m],'.12g') for m in METRICS}})
    return transformed


def main():
    parser=argparse.ArgumentParser(description='Leakage-safe IQR preprocessing, relabeling and ML evaluation')
    parser.add_argument('input',nargs='?',default='raw_dataset.csv');parser.add_argument('output',nargs='?',default='model_evaluation.json');parser.add_argument('--preprocessed',default='preprocessed_dataset.csv');args=parser.parse_args()
    raw=load_raw(args.input);processed=write_descriptive(raw,args.preprocessed);samples=make_samples(processed)
    report={'input':args.input,'raw_rows':len(raw),'round_groups':len(samples),'feature_columns':list(FEATURES),'label_formula':'per-round normalized execution time 70%, thread CPU 20%, memory delta 10%; tie by throughput','preprocessing':'Fences fit only on training rows in each split, per size x algorithm; same bounds applied to test before recomputing labels. Unseen file size uses algorithm-wide training-only bounds. Full-data preprocessed CSV is descriptive only.','full_data_descriptive_class_counts':dict(Counter(s['y'] for s in samples)),'full_data_descriptive_flagged_rows':sum(bool(r['outlier_metrics']) for r in processed),'holdout_80_20':holdout(raw),'five_fold_cv':cv(raw),'unseen_file_size_generalization':leave_size(raw)}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));print(f'Saved report: {out}')

if __name__=='__main__':main()
