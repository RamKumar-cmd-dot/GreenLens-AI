import re
import json
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from ml.common import *

def text_of(df):
    return (df.merchant_name.fillna('')+' '+df.merchant_description.fillna('')).str.replace(r'\b\d+\b','',regex=True)
def baseline(text):
    s=text.lower()
    rules=[('Automotive',r'\b(mot|tyre|car wash|service and)\b'),('Utilities',r'\b(dual|water|broadband|mobile plan)\b'),('Fuel',r'\b(petrol|forecourt|pump|motor fuel)\b'),('Electricity',r'\b(electric|electricity|power meter)\b'),('Gas',r'\b(gas supply|gas meter|natural gas)\b'),('Public Transport',r'\b(journey|rail|bus)\b'),('Home Improvement',r'\b(insulation|building|renovation)\b')]
    return next((c for c,p in rules if re.search(p,s)),'Other')
def train():
    df=pd.read_csv(DATA/'synthetic/transactions.csv'); splits=json.loads((DATA/'processed/splits.json').read_text())
    # Bounded training sample, still strictly partitioned by customer.
    tr=df[df.customer_id.isin(splits['train'])].sample(n=min(60000,len(df[df.customer_id.isin(splits['train'])])),random_state=SEED)
    pipe=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)),('model',LogisticRegression(max_iter=500,random_state=SEED))]).fit(text_of(tr),tr.sustainability_category)
    report={'categories':CATEGORIES,'train_transactions':len(tr),'limitation':'Known synthetic merchant vocabulary; does not establish unseen-merchant generalization.'}
    for split in ['validation','test']:
        s=df[df.customer_id.isin(splits[split])]; txt=text_of(s); report[split]={}
        for name,pred in [('tfidf_logistic',pipe.predict(txt)),('rule_baseline',txt.map(baseline))]: report[split][name]={'classification_report':classification_report(s.sustainability_category,pred,labels=CATEGORIES,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(s.sustainability_category,pred,labels=CATEGORIES).tolist()}
    test=df[df.customer_id.isin(splits['test'])].copy()
    test['predicted_category']=pipe.predict(text_of(test))
    test[['transaction_id','customer_id','sustainability_category','predicted_category']].to_csv(REPORTS/'transaction_test_predictions.csv',index=False)
    joblib.dump(pipe,MODELS/'transaction_classifier.joblib'); save_json(REPORTS/'transaction_metrics.json',report)
    (REPORTS/'transaction_evaluation.md').write_text('# Transaction evaluation\n\n'+ '\n'.join(f"{s}, {m}: macro F1 = {report[s][m]['classification_report']['macro avg']['f1-score']:.4f}" for s in ['validation','test'] for m in ['tfidf_logistic','rule_baseline'])+'\n\nSee transaction_metrics.json for per-category metrics and confusion matrices. Merchant templates are shared across customer partitions.\n')
    print('Saved transaction classifier')
if __name__=='__main__': train()
