"""Backend entrypoints. Never use model scores as eligibility or credit approval."""
import json
import math
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from ml.common import *
from ml.eligibility import screen, missing

@lru_cache(maxsize=1)
def load_models():
    meta=json.loads((MODELS/'metadata.json').read_text())
    if meta['features']!=FEATURES: raise ValueError('Model feature schema mismatch')
    threshold_path=REPORTS/'selected_thresholds.json'
    thresholds=json.loads(threshold_path.read_text())
    if set(thresholds)!=set(TARGETS): raise ValueError('Selected threshold product schema mismatch')
    for pid, entry in thresholds.items():
        value=entry.get('threshold') if isinstance(entry,dict) else None
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError(f'Invalid selected threshold for {pid}')
    return {'metadata':meta,'thresholds':{pid:float(v['threshold']) for pid,v in thresholds.items()},**{pid:joblib.load(MODELS/f'{pid}.joblib') for pid in TARGETS},'transaction':joblib.load(MODELS/'transaction_classifier.joblib')}

def normalize(raw):
    f={k:raw.get(k) for k in FEATURES}
    for k in NUMERIC:
        if missing(f[k]): f[k]=np.nan
        else:
            try: f[k]=float(f[k])
            except (ValueError,TypeError): raise ValueError(f'{k} must be numeric or null')
            if not np.isfinite(f[k]): f[k]=np.nan
    for k in CATEGORICAL: f[k]=np.nan if missing(f[k]) else str(f[k])
    for k in ['homeowner','vehicle_ownership','owns_ev','mobile_app_active','paper_statements_enabled','existing_mortgage','existing_vehicle_loan','roof_suitable','replacement_intent']:
        if not missing(f[k]) and f[k] not in (0,1): raise ValueError(f'{k} must be 0, 1, or null')
    if not missing(f['digital_transaction_ratio']) and not 0<=f['digital_transaction_ratio']<=1: raise ValueError('digital_transaction_ratio must be in [0,1]')
    return f

def reasons(pid,f):
    rules={'GP01':[('HIGH_FUEL_SPEND','mean_monthly_fuel',lambda v:v>=100),('EXISTING_PETROL_VEHICLE','vehicle_type',lambda v:v=='petrol'),('HIGH_ANNUAL_MILEAGE','annual_mileage_estimate',lambda v:v>=10000)],'GP02':[('HOME_OWNER','homeowner',lambda v:v==1),('HIGH_GAS_DEMAND','gas_kwh_year',lambda v:v>=12000)],'GP03':[('HOME_OWNER','homeowner',lambda v:v==1),('HIGH_ELECTRICITY_DEMAND','electricity_kwh_year',lambda v:v>=4000)],'GP04':[('PAPER_STATEMENTS_ENABLED','paper_statements_enabled',lambda v:v==1),('HIGH_DIGITAL_ENGAGEMENT','digital_logins_month',lambda v:v>=15)]}[pid]
    selected=[(code,k,f[k]) for code,k,fn in rules if not missing(f[k]) and fn(f[k])]
    return [r[0] for r in selected],{k:v for _,k,v in selected}

def predict_opportunities(customer_features):
    if not isinstance(customer_features,dict): raise ValueError('Expected one customer feature dictionary')
    f=normalize(customer_features); models=load_models(); frame=pd.DataFrame([f],columns=FEATURES); outputs=[]
    for pid in TARGETS:
        eligibility=screen(pid,f); codes,evidence=reasons(pid,f); meta=models['metadata']['products'][pid]
        propensity=float(models[pid].predict_proba(frame)[0,1]); threshold=models['thresholds'][pid]
        outputs.append({'customer_id':customer_features.get('customer_id'),'product_id':pid,'propensity':propensity,'threshold_screen':{'threshold':threshold,'above_threshold':propensity>=threshold,'status':'ABOVE_VALIDATION_SELECTED_THRESHOLD' if propensity>=threshold else 'BELOW_VALIDATION_SELECTED_THRESHOLD','selection_basis':'validation-set F1; statistical prioritization only'},'confidence':None,'reliability':{'status':'synthetic_only_unvalidated_for_real_customers','per_customer_confidence':'unavailable','probability_status':meta['probability_status'],'validation_brier':meta['validation_brier'],'validation_ece':meta['validation_ece'],'missing_feature_count':sum(missing(v) for v in f.values())},'reason_codes':codes,'evidence':evidence,'data_timestamp':customer_features.get('data_timestamp'),'model_version':VERSION,'applicable_exclusions':eligibility['applicable_exclusions'],'eligibility':eligibility,'recommendation_status':'excluded' if eligibility['status']=='excluded' else 'needs_review' if eligibility['status']=='needs_review' else 'opportunity_pending_institutional_checks'})
    return {'customer_id':customer_features.get('customer_id'),'opportunities':outputs,'carbon_inputs':{'annual_mileage_estimate':None if missing(f['annual_mileage_estimate']) else f['annual_mileage_estimate'],'electricity_kwh_year':None if missing(f['electricity_kwh_year']) else f['electricity_kwh_year'],'gas_kwh_year':None if missing(f['gas_kwh_year']) else f['gas_kwh_year'],'vehicle_type':None if missing(f['vehicle_type']) else f['vehicle_type'],'source':'synthetic estimates','period':'annual','emissions_calculated':False}}

def predict_customer(customer_id):
    df=pd.read_csv(DATA/'processed/customer_360.csv'); rows=df[df.customer_id==customer_id]
    if rows.empty: raise KeyError(f'Unknown customer_id: {customer_id}')
    return predict_opportunities(rows.iloc[0].to_dict())

def classify_transaction(transaction):
    from ml.transaction_classifier import text_of
    if not isinstance(transaction,dict): raise ValueError('Expected transaction dictionary')
    row={k:transaction.get(k) or '' for k in ['merchant_name','merchant_description']}
    if any(not isinstance(v,str) for v in row.values()): raise ValueError('Merchant fields must be strings')
    pipe=load_models()['transaction']; text=text_of(pd.DataFrame([row])); vector=pipe.named_steps['tfidf'].transform(text)
    if vector.nnz==0: return {'category':'Other','confidence':None,'needs_review':True,'reason':'no_known_vocabulary'}
    probs=pipe.predict_proba(text)[0]; top=int(probs.argmax()); uncertain=bool(probs[top]<.6)
    return {'category':str(pipe.classes_[top]),'confidence':float(probs[top]),'confidence_kind':'uncalibrated_class_probability','needs_review':uncertain}

if __name__=='__main__':
    save_json(REPORTS/'sample_response.json',predict_customer('C000025')); print('Saved complete four-product sample response')
