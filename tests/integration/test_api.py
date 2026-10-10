import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

@pytest.fixture(scope='module')
def client(tmp_path_factory):
    with TestClient(create_app(tmp_path_factory.mktemp('api')/'demo.sqlite')) as c:
        yield c

def test_milestone_a(client):
    assert client.get('/health').json()['models_available']
    page=client.get('/customers?limit=2').json()
    assert page['total']==5000 and len(page['items'])==2
    customer=client.get('/customers/C000025').json()
    assert customer['features']['homeowner']==1 and customer['synthetic']
    assert client.get('/customers/unknown').status_code==404
    assert client.get('/customers?limit=0').status_code==422
    tx=client.get('/customers/C000025/transactions?category=Fuel&limit=3').json()
    assert len(tx['items'])==3 and all(t['sustainability_category']=='Fuel' for t in tx['items'])
    result=client.get('/customers/C000025/opportunities').json()['opportunities']
    assert {r['product_id'] for r in result}=={'GP01','GP02','GP03','GP04'}
    assert all(0<=r['propensity']<=1 for r in result)
    assert all(0<=r['threshold_screen']['threshold']<=1 for r in result)
    assert all(r['threshold_screen']['above_threshold']==(r['propensity']>=r['threshold_screen']['threshold']) for r in result)
    scenario=client.post('/customers/C000025/scenario',json={'changes':{'vehicle_ownership':1,'vehicle_type':'electric','owns_ev':1,'replacement_intent':0}})
    assert scenario.status_code==200 and scenario.json()['synthetic']
    assert len(scenario.json()['opportunities'])==4
    assert next(r for r in scenario.json()['opportunities'] if r['product_id']=='GP01')['status']=='EXCLUDED'
    assert client.post('/customers/C000025/scenario',json={'changes':{'ev_finance_takeup':1}}).status_code==422

def test_business_and_insights(client,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    s=client.get('/business/summary').json()
    assert s['total_customers']==5000
    assert s['portfolio_energy_kwh_year']>0 and 0<=s['paperless_adoption_rate']<=1
    assert s['mobile_app_active_customers']>0 and s['mean_monthly_digital_logins']>0
    assert s['unique_customers_with_opportunities']<=5000
    for p in s['products']:
        assert sum(p['status_counts'].values())==5000
        assert sum(p['propensity_histogram'])==5000
        page=client.get('/business/opportunities',params={'product_id':p['product_id']}).json()
        assert page['total']==p['potential_customers']
        assert all(r['status']=='POTENTIAL_OPPORTUNITY' for r in page['items'])
        screened=client.get('/business/opportunities',params={'product_id':p['product_id'],'above_threshold':'true'}).json()
        assert screened['total']==p['priority_threshold_matches']
        assert all(r['threshold_screen']['above_threshold'] for r in screened['items'])
    segments=client.get('/business/segments').json()['items']
    assert sum(x['customers'] for x in segments)==5000
    assert sum(x['potential_customers'] for x in segments)==s['unique_customers_with_opportunities']
    trends=client.get('/business/trends').json()
    assert len(trends['items'])>0 and {x['category'] for x in trends['items']}<=set(['Fuel','Electricity','Gas','Public Transport','Home Improvement','Automotive','Utilities','Other'])
    assert {x['month'] for x in trends['items']}=={f'2025-{i:02}' for i in range(1,13)}
    insights=client.get('/customers/C000025/insights').json()
    assert len(insights['explanations'])==4 and len(insights['monthly_spending'])>0
    assert all(e['source']=='deterministic' for e in insights['explanations'])
    assert client.get('/customers/unknown/insights').status_code==404
    assert client.get('/business/opportunities?product_id=bad').status_code==422

def test_unavailable_models(client):
    service=client.app.state.service
    client.app.state.service=None
    try:
        assert client.get('/health').json()['status']=='degraded'
        assert client.get('/customers/C000025/opportunities').status_code==503
        assert client.get('/business/summary').status_code==503
        assert client.get('/customers/C000025').status_code==200
    finally:
        client.app.state.service=service

def test_transaction_inference(client):
    result=client.post('/transactions/classify',json={'merchant_name':'Shell','merchant_description':'pay at pump'}).json()
    assert result['category']=='Fuel' and 0<=result['confidence']<=1
    assert client.post('/transactions/classify',json={'merchant_name':'zzzzzzzz'}).json()['needs_review']
