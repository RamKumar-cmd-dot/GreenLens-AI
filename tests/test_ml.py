import json
import joblib
import numpy as np
import pandas as pd
import pytest
from ml.common import *
from ml.inference import *
from ml.eligibility import screen
from ml.propensity_models import pipeline
from ml.evaluate_merchant_holdout import merchant_split

def test_inference_and_reload():
    result=predict_customer('C000000'); assert {p['product_id'] for p in result['opportunities']}==set(TARGETS)
    assert all(0<=p['propensity']<=1 and p['confidence'] is None for p in result['opportunities'])
    assert all(0<=p['threshold_screen']['threshold']<=1 for p in result['opportunities'])
    assert all(p['reliability']['validation_score_band']['validation_customers']>0 for p in result['opportunities'])
    assert all(p['reliability']['per_customer_confidence']=='unavailable' for p in result['opportunities'])
    assert all(p['threshold_screen']['above_threshold']==(p['propensity']>=p['threshold_screen']['threshold']) for p in result['opportunities'])
    json.dumps(result,allow_nan=False)
    load_models.cache_clear(); reloaded=predict_customer('C000000')
    assert {k:v for k,v in result.items() if k!='opportunities'}=={k:v for k,v in reloaded.items() if k!='opportunities'}
    for first,second in zip(result['opportunities'],reloaded['opportunities']):
        assert {k:v for k,v in first.items() if k!='propensity'}=={k:v for k,v in second.items() if k!='propensity'}
        assert first['propensity']==pytest.approx(second['propensity'],rel=1e-10,abs=1e-12)

def test_threshold_screen_is_separate_from_use_case_screen():
    result=predict_opportunities({'customer_id':'synthetic-test','paper_statements_enabled':0})
    gp04=next(p for p in result['opportunities'] if p['product_id']=='GP04')
    assert gp04['eligibility']['status']=='excluded'
    assert gp04['recommendation_status']=='excluded'
    assert gp04['threshold_screen']['status'] in {'ABOVE_VALIDATION_SELECTED_THRESHOLD','BELOW_VALIDATION_SELECTED_THRESHOLD'}
    assert gp04['propensity']>=0 and gp04['propensity']<=1

def test_missing_unknown():
    result=predict_opportunities({'region':'unseen_region'}); json.dumps(result,allow_nan=False)
    assert all(p['recommendation_status']=='needs_review' for p in result['opportunities'])
    assert classify_transaction({'merchant_name':'zzzzzzzz'})['category']=='Other'
    with pytest.raises(ValueError): predict_opportunities({'homeowner':2})

def test_exclusions_and_evidence():
    assert screen('GP04',{'paper_statements_enabled':0})['status']=='excluded'
    assert screen('GP02',{'homeowner':0})['status']=='excluded'
    assert screen('GP03',{})['status']=='needs_review'
    assert screen('GP01',{'owns_ev':1,'replacement_intent':0})['status']=='excluded'
    assert screen('GP01',{'owns_ev':1,'replacement_intent':1,'vehicle_type':'petrol','vehicle_ownership':1})['status']=='needs_review'
    for p in predict_customer('C000000')['opportunities']:
        if 'HIGH_FUEL_SPEND' in p['reason_codes']: assert p['evidence']['mean_monthly_fuel']>=100

def test_training_reproducible(tmp_path):
    df=pd.read_csv(DATA/'processed/customer_360.csv').head(150)
    y=pd.read_csv(DATA/'synthetic/product_takeup_labels.csv').head(150).ev_finance_takeup
    for kind in ['logistic','random_forest']:
        a=pipeline(kind).fit(df[FEATURES],y); b=pipeline(kind).fit(df[FEATURES],y)
        assert np.allclose(a.predict_proba(df[FEATURES]),b.predict_proba(df[FEATURES]),rtol=0,atol=1e-14)
        joblib.dump(a,tmp_path/'model'); assert np.allclose(a.predict_proba(df[FEATURES]),joblib.load(tmp_path/'model').predict_proba(df[FEATURES]))

def test_merchant_holdout_has_no_merchant_overlap_and_preserves_all_categories():
    tx=pd.read_csv(DATA/'synthetic/transactions.csv')
    train_idx,test_idx=merchant_split(tx)
    train=tx.loc[train_idx]; test=tx.loc[test_idx]
    assert set(train.merchant_name).isdisjoint(test.merchant_name)
    assert set(train.sustainability_category)==set(CATEGORIES)
    assert set(test.sustainability_category)==set(CATEGORIES)

def test_london_inspection_and_interval_summary(tmp_path,monkeypatch):
    import sys
    import data.process_london_energy as mod
    rows=pd.DataFrame({'meter':['example']*49,'time':list(pd.date_range('2013-01-01',periods=48,freq='30min'))+[pd.Timestamp('2013-01-02')],'reading':[.5]*49})
    path=tmp_path/'fixture.csv'; rows.to_csv(path,index=False)
    monkeypatch.setattr(mod,'DATA',tmp_path); (tmp_path/'processed').mkdir()
    monkeypatch.setattr(sys,'argv',['process',str(path),'--id-column','meter','--timestamp-column','time','--reading-column','reading','--timestamp-format','%Y-%m-%d %H:%M:%S','--unit','kWh_per_interval','--interval-minutes','30','--source-url','test-fixture'])
    mod.main(); summary=pd.read_csv(tmp_path/'processed/london_household_summary.csv')
    assert summary.iloc[0].complete_days==1
    assert summary.iloc[0].mean_complete_daily_kwh==24
