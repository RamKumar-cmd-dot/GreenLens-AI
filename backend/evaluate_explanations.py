"""Offline LLM guardrail conformance evaluation; not a live model quality test."""
import json
from backend.explanations import approved_choices, explain
from backend.recommendations import assemble
from ml.inference import load_models
from ml.common import DATA, REPORTS, save_json

def fixture(pid='GP01', **changes):
    base={'customer_id':'evaluation_fixture','data_timestamp':'2026-01-01','vehicle_ownership':1,'vehicle_type':'petrol','owns_ev':0,'replacement_intent':1,'annual_mileage_estimate':10000,'mean_monthly_fuel':140,'homeowner':1,'roof_suitable':1,'electricity_kwh_year':3000,'paper_statements_enabled':1}
    base.update(changes)
    return assemble(base,pid,.321,load_models()['metadata'])

def main():
    rec=fixture(); choices=approved_choices(rec); canonical={k:v[0] for k,v in choices.items()}
    results=[]
    def add(case_id, category, output, expected=None, source='deterministic'):
        fields={key:getattr(output,key) for key in choices}
        required=all(isinstance(fields[k],str) and fields[k].strip() for k in choices)
        canonical_match=fields==expected if expected is not None else fields==canonical
        numbers=lambda s: sorted(__import__('re').findall(r'(?<![A-Za-z])[£$]?\d+(?:\.\d+)?',s))
        numeric_safe=all(numbers(fields[k])==numbers(canonical[k]) for k in choices)
        results.append({'id':case_id,'category':category,'source':output.source,'passed':required and canonical_match and numeric_safe,
            'dimensions':{'groundedness':canonical_match,'factual_accuracy':canonical_match,'completeness':required,'numerical_consistency':numeric_safe,
                'missing_conflicting_information':category!='scenario' or expected is not None}})

    for case in json.loads((DATA/'reference/llm_eval_cases.json').read_text()):
        candidate={**canonical,case['field']:case['text']}
        output=explain(rec,provider=lambda *_:candidate)
        add(case['id'],'unsupported_output',output)
    for i in (0,1):
        output=explain(rec,provider=lambda r,c:{k:v[i] for k,v in c.items()})
        expected={k:v[i] for k,v in choices.items()}
        add(f'valid_variant_{i}','approved_variant',output,expected)
    for case_id,provider in [('timeout',lambda *_:(_ for _ in ()).throw(TimeoutError())),('malformed',lambda *_:{'unexpected':'value'})]:
        add(case_id,'provider_failure',explain(rec,provider=provider))

    scenarios=[
        ('missing_vehicle','GP01',{'vehicle_type':None,'vehicle_ownership':None,'owns_ev':None,'replacement_intent':None}),
        ('conflicting_vehicle','GP01',{'vehicle_ownership':0,'vehicle_type':'petrol'}),
        ('excluded_paperless','GP04',{'paper_statements_enabled':0}),
        ('solar_impact_unavailable','GP03',{'region':'North West','homeowner':1,'roof_suitable':1,'electricity_kwh_year':3000}),
    ]
    for case_id,pid,changes in scenarios:
        scenario=fixture(pid,**changes); output=explain(scenario)
        choices_s=approved_choices(scenario); expected={k:v[0] for k,v in choices_s.items()}
        fields={key:getattr(output,key) for key in expected}
        complete=all(isinstance(v,str) and v.strip() for v in fields.values())
        text=' '.join(fields.values()).lower()
        state=scenario.status.lower().replace('_',' ')
        status_present=state in text
        canonical=fields==expected
        numeric_safe=all(sorted(__import__('re').findall(r'(?<![A-Za-z])[£$]?\d+(?:\.\d+)?',fields[k]))==sorted(__import__('re').findall(r'(?<![A-Za-z])[£$]?\d+(?:\.\d+)?',expected[k])) for k in expected)
        results.append({'id':case_id,'category':'scenario','source':output.source,'passed':complete and status_present and canonical and numeric_safe,
            'dimensions':{'groundedness':canonical,'factual_accuracy':canonical,'completeness':complete,'numerical_consistency':numeric_safe,'missing_conflicting_information':status_present}})

    dimensions={key:{'passed':sum(bool(r['dimensions'][key]) for r in results if key!='missing_conflicting_information' or r['category']=='scenario'),
        'total':sum(key!='missing_conflicting_information' or r['category']=='scenario' for r in results)}
        for key in ['groundedness','factual_accuracy','completeness','numerical_consistency','missing_conflicting_information']}
    report={'evaluation_type':'offline deterministic guardrail conformance; no live LLM or semantic-quality claim','cases':results,'dimensions':dimensions,'passed':sum(r['passed'] for r in results),'total':len(results)}
    save_json(REPORTS/'llm_evaluation.json',report)
    print(f"{report['passed']}/{report['total']} guardrail cases passed; dimension scores: {dimensions}")
    assert all(r['passed'] for r in results)
if __name__=='__main__': main()
