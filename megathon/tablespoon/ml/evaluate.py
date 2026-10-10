"""Metrics are computed from predictions, never estimated or hard coded."""
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, brier_score_loss, confusion_matrix
from ml.common import REPORTS

def binary_metrics(y,p):
    y=np.asarray(y); p=np.asarray(p); pred=p>=.5
    bins=[]
    for lo in np.arange(0,1,.1):
        mask=(p>=lo)&(p<lo+.1 if lo<.9 else p<=1)
        if mask.any(): bins.append({'lower':float(lo),'n':int(mask.sum()),'mean_probability':float(p[mask].mean()),'observed_rate':float(y[mask].mean())})
    return {'n':len(y),'positives':int(y.sum()),'negatives':int(len(y)-y.sum()),'roc_auc':float(roc_auc_score(y,p)) if len(set(y))==2 else None,'average_precision':float(average_precision_score(y,p)) if y.sum() else None,'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'f1':float(f1_score(y,pred,zero_division=0)),'brier':float(brier_score_loss(y,p)),'threshold':.5,'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist(),'calibration_bins':bins,'ece':float(sum(b['n']*abs(b['mean_probability']-b['observed_rate']) for b in bins)/len(y))}

def render():
    import json
    lines=['# Executed evaluation','All results concern simulated outcomes only. Threshold = 0.5. No real-world validity is established.','', '| Product | Split | Model | ROC-AUC | AP | Brier | Precision | Recall | F1 |','|---|---|---|---|---|---|---|---|---|']
    for file in sorted(REPORTS.glob('GP*.json')):
        r=json.loads(file.read_text())
        for split in ['validation','test']:
            for name,m in r[split].items(): lines.append('| '+' | '.join([file.stem,split,name]+[f'{m[k]:.4f}' if m[k] is not None else 'undefined' for k in ['roc_auc','average_precision','brier','precision','recall','f1']])+' |')
    (REPORTS/'evaluation.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
if __name__=='__main__': render()
