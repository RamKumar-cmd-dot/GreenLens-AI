import pytest
from backend.impact import estimate, DEFAULT_FACTORS
from backend.recommendations import assemble
from ml.inference import load_models

BASE={'customer_id':'example','data_timestamp':'2026-01-01','vehicle_ownership':1,'vehicle_type':'petrol','owns_ev':0,'replacement_intent':0,'annual_mileage_estimate':10000,'homeowner':1,'heating_technology':'gas_boiler','gas_kwh_year':10000,'paper_statements_enabled':1,'roof_suitable':1}

def test_ev_units():
    r=estimate('GP01',BASE)
    assert r.baseline_kgco2e==pytest.approx(10000*1.609344*.07*2.06916)
    assert r.scenario_kgco2e==pytest.approx(10000*1.609344*.18*.177)
    assert r.avoided_kgco2e==pytest.approx(r.baseline_kgco2e-r.scenario_kgco2e)

@pytest.mark.parametrize('pid',['GP01','GP02'])
def test_zero_and_missing_factors(pid):
    r=estimate(pid,{**BASE,'annual_mileage_estimate':0,'gas_kwh_year':0})
    assert r.baseline_kgco2e==0 and r.avoided_kgco2e==0
    assert estimate(pid,BASE,{}).impact_status=='UNAVAILABLE'
    assert estimate(pid,{**BASE,'annual_mileage_estimate':-1,'gas_kwh_year':-1}).impact_status=='UNAVAILABLE'

def test_negative_and_gas():
    assert estimate('GP01',{**BASE,'ev_kwh_per_km':5}).avoided_kgco2e<0
    assert estimate('GP02',BASE).avoided_kgco2e==pytest.approx(182.96)

def test_solar_and_paper():
    assert estimate('GP03',BASE).impact_status=='UNAVAILABLE'
    r=estimate('GP03',{**BASE,'solar_capacity_kwp':4,'solar_yield_kwh_per_kwp_year':900,'solar_self_consumption_ratio':.5,'electricity_kwh_year':1000,'solar_yield_source':'test fixture, not deployment data','solar_location':'fixture'})
    assert r.generation_kwh==3600 and r.avoided_kgco2e==177
    r=estimate('GP04',BASE)
    assert r.avoided_pages==48 and r.avoided_kgco2e is None

@pytest.mark.parametrize('pid,changes,status',[('GP01',{'owns_ev':1,'vehicle_type':'electric'},'EXCLUDED'),('GP02',{'homeowner':0},'EXCLUDED'),('GP03',{'homeowner':None},'INSUFFICIENT_DATA'),('GP04',{'paper_statements_enabled':0},'EXCLUDED'),('GP01',{'vehicle_type':None},'INSUFFICIENT_DATA')])
def test_screening(pid,changes,status):
    r=assemble({**BASE,**changes},pid,.9,load_models()['metadata'])
    assert r.status==status and r.propensity==.9
    assert r.impact.impact_status=='UNAVAILABLE'

def test_no_vehicle_and_conflicting_vehicle_need_review():
    for changes in [{'vehicle_ownership':0,'vehicle_type':'none'},{'vehicle_ownership':0,'vehicle_type':'petrol'}]:
        r=assemble({**BASE,**changes},'GP01',.9,load_models()['metadata'])
        assert r.status=='NEEDS_REVIEW' and r.impact.impact_status=='UNAVAILABLE'
