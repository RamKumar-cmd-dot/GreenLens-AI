"""Secondary diagnostic split holding out merchant names from model fitting."""
import json
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from ml.common import DATA, REPORTS, SEED, CATEGORIES, save_json
from ml.transaction_classifier import baseline, text_of

HELD_OUT_MERCHANTS=['Amazon','BP','British Gas','Halfords','Homebase','Thames Water','TfL']

def merchant_split(frame):
    mask=frame.merchant_name.isin(HELD_OUT_MERCHANTS)
    return frame.index[~mask],frame.index[mask]

def main():
    frame=pd.read_csv(DATA/'synthetic/transactions.csv')
    train_idx,test_idx=merchant_split(frame)
    train=frame.loc[train_idx]; test=frame.loc[test_idx]
    if set(train.merchant_name)&set(test.merchant_name): raise AssertionError('Merchant groups overlap')
    missing=set(CATEGORIES)-set(train.sustainability_category)
    if missing: raise ValueError(f'Merchant-held-out training data lacks categories: {sorted(missing)}')
    bounded=train.sample(n=min(60000,len(train)),random_state=SEED)
    model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)),('model',LogisticRegression(max_iter=500,random_state=SEED))])
    model.fit(text_of(bounded),bounded.sustainability_category)
    text=text_of(test)
    results={'evaluation':'Fixed, predeclared merchant-name holdout chosen to retain every label in both partitions; no held-out merchant appears in training. This secondary synthetic diagnostic is not real-merchant generalization. Model is diagnostic only and does not replace the saved primary pipeline.',
        'seed':SEED,'held_out_merchants':HELD_OUT_MERCHANTS,'train_transactions':len(train),'test_transactions':len(test),'train_merchants':int(train.merchant_name.nunique()),'test_merchants':int(test.merchant_name.nunique()),'merchant_overlap':sorted(set(train.merchant_name)&set(test.merchant_name)),'categories':CATEGORIES,'models':{}}
    for name,pred in [('tfidf_logistic',model.predict(text)),('rule_baseline',text.map(baseline))]:
        results['models'][name]={'classification_report':classification_report(test.sustainability_category,pred,labels=CATEGORIES,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(test.sustainability_category,pred,labels=CATEGORIES).tolist()}
    save_json(REPORTS/'transaction_merchant_holdout.json',results)
    (REPORTS/'transaction_merchant_holdout.md').write_text('# Merchant-held-out transaction diagnostic\n\n'+results['evaluation']+'\n\n'+ '\n'.join(f"- {name}: macro F1 {r['classification_report']['macro avg']['f1-score']:.4f}; {r['classification_report']['weighted avg']['support']:.0f} test rows" for name,r in results['models'].items())+'\n')
    print(f"Merchant holdout: {len(train)} train / {len(test)} test rows; macro F1 {results['models']['tfidf_logistic']['classification_report']['macro avg']['f1-score']:.4f}")
if __name__=='__main__': main()
