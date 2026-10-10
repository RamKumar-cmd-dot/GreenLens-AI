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

def validation_score_band(pid, score):
    """Return validation-cohort calibration context for the score's fixed bin.

    This is not individual confidence. Wilson intervals describe the observed
    synthetic validation adoption rate among customers in the same score band.
    """
    report_path=REPORTS/f'{pid}.json'
    if not report_path.exists(): return None
    report=json.loads(report_path.read_text())
    bins=report.get('validation',{}).get(report.get('selected',''),{}).get('calibration_bins',[])
    if not bins: return None
    bin_width=0.1
    selected=next((b for b in bins if float(b.get('lower',-1)) <= score < float(b.get('lower',-1))+bin_width),None)
    if selected is None:
        selected=max((b for b in bins if float(b.get('lower',-1))<=score),key=lambda b:b['lower'],default=None)
    if selected is None: return None
    n=int(selected['n']); rate=float(selected['observed_rate'])
    if n<=0 or not 0<=rate<=1: return None
    # Wilson score interval for the cohort's observed simulated take-up rate.
    z=1.959963984540054; den=1+z*z/n
    center=(rate+z*z/(2*n))/den
    half=z*math.sqrt((rate*(1-rate)+z*z/(4*n))/n)/den
    return {'score_band_lower':float(selected['lower']),'score_band_upper':min(1.0,float(selected['lower'])+bin_width),
        'validation_customers':n,'mean_predicted_propensity':float(selected['mean_probability']),
        'observed_simulated_takeup_rate':rate,'observed_rate_wilson_95_interval':[max(0.0,center-half),min(1.0,center+half)],
        'interpretation':'Synthetic validation-cohort reliability for this score band; not per-customer confidence or real-customer validation.'}

def predict_opportunities(customer_features):
    if not isinstance(customer_features,dict): raise ValueError('Expected one customer feature dictionary')
    f=normalize(customer_features); models=load_models(); frame=pd.DataFrame([f],columns=FEATURES); outputs=[]
    for pid in TARGETS:
        eligibility=screen(pid,f); codes,evidence=reasons(pid,f); meta=models['metadata']['products'][pid]
        propensity=float(models[pid].predict_proba(frame)[0,1]); threshold=models['thresholds'][pid]
        outputs.append({'customer_id':customer_features.get('customer_id'),'product_id':pid,'propensity':propensity,'threshold_screen':{'threshold':threshold,'above_threshold':propensity>=threshold,'status':'ABOVE_VALIDATION_SELECTED_THRESHOLD' if propensity>=threshold else 'BELOW_VALIDATION_SELECTED_THRESHOLD','selection_basis':'validation-set F1; statistical prioritization only'},'confidence':None,'reliability':{'status':'synthetic_validation_score_band_only','per_customer_confidence':'unavailable','validation_score_band':validation_score_band(pid,propensity),'probability_status':meta['probability_status'],'validation_brier':meta['validation_brier'],'validation_ece':meta['validation_ece'],'missing_feature_count':sum(missing(f.get(k)) for k in FEATURES)},'reason_codes':codes,'evidence':evidence,'data_timestamp':customer_features.get('data_timestamp'),'model_version':VERSION,'applicable_exclusions':eligibility['applicable_exclusions'],'eligibility':eligibility,'recommendation_status':'excluded' if eligibility['status']=='excluded' else 'needs_review' if eligibility['status']=='needs_review' else 'opportunity_pending_institutional_checks'})
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
