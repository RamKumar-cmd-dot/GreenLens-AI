"""Check a running API and save non-secret demo outputs; never trains models."""
import os
import httpx
from ml.common import REPORTS, save_json

def main():
    base=os.getenv('GREENLENS_API_URL','http://127.0.0.1:8000')
    checked=[]
    with httpx.Client(base_url=base,timeout=50) as client:
        paths=['/health','/customers?limit=2','/customers/C000034','/customers/C000034/transactions?limit=2','/customers/C000034/opportunities','/customers/C000034/insights','/business/summary','/business/segments','/business/trends','/business/opportunities?product_id=GP01&limit=2']
        responses={}
        for path in paths:
            response=client.get(path);response.raise_for_status();responses[path]=response.json();checked.append({'path':path,'status':response.status_code})
        assert responses['/health']['models_available']
        result=responses['/customers/C000034/opportunities']
        assert len(result['opportunities'])==4
        assert result['opportunities'][0]['impact']['avoided_kgco2e']>0
        excluded=client.get('/customers/C000048/opportunities').json()
        assert any(x['status']=='EXCLUDED' for x in excluded['opportunities'])
        scenario=client.post('/customers/C000034/scenario',json={'changes':{'paper_statements_enabled':0}})
        scenario.raise_for_status();assert len(scenario.json()['opportunities'])==4
        assert next(x for x in scenario.json()['opportunities'] if x['product_id']=='GP04')['status']=='EXCLUDED'
        r=client.post('/transactions/classify',json={'merchant_name':'Shell','merchant_description':'pay at pump'})
        r.raise_for_status();assert r.json()['category']=='Fuel'
        assert client.get('/customers/not-found').status_code==404
        assert client.get('/customers?limit=-1').status_code==422
    save_json(REPORTS/'integrated_demo_response.json',result)
    save_json(REPORTS/'live_smoke.json',{'checks':checked,'ev_exclusion_verified':True,'scenario_rerun_verified':True,'transaction_classifier_verified':True,'explanation_sources':[e['source'] for e in responses['/customers/C000034/insights']['explanations']],'explanation_fallback_reasons':[e['fallback_reason'] for e in responses['/customers/C000034/insights']['explanations']],'business_summary':responses['/business/summary']})
    print(f'{len(checked)} GET endpoints passed; exclusion, scenario, classification, 404 and 422 verified')
if __name__=='__main__':main()
