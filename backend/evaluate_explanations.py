"""Offline guardrail evaluation. Does not measure a live provider's generation quality."""
import json
from backend.explanations import approved_choices, explain
from backend.recommendations import assemble
from ml.inference import load_models
from ml.common import DATA, REPORTS, save_json

def main():
    rec=assemble({'customer_id':'evaluation_fixture','data_timestamp':'2026-01-01','vehicle_ownership':1,'vehicle_type':'petrol','owns_ev':0,'replacement_intent':1,'annual_mileage_estimate':10000,'mean_monthly_fuel':140},'GP01',.321,load_models()['metadata'])
    choices=approved_choices(rec);canonical={k:v[0] for k,v in choices.items()}
    results=[]
    for case in json.loads((DATA/'reference/llm_eval_cases.json').read_text()):
        candidate={**canonical,case['field']:case['text']}
        output=explain(rec,provider=lambda *_:candidate)
        results.append({**case,'expected':'deterministic','actual':output.source,'passed':output.source=='deterministic' and all(getattr(output,k)==v for k,v in canonical.items())})
    for i in (0,1):
        out=explain(rec,provider=lambda r,c:{k:v[i] for k,v in c.items()})
        results.append({'id':f'valid_variant_{i}','expected':'openai_validated_selection','actual':out.source,'passed':out.source=='openai_validated_selection'})
    def unavailable(*_): raise TimeoutError('simulated provider failure')
    out=explain(rec,provider=unavailable)
    results.append({'id':'timeout','expected':'deterministic','actual':out.source,'passed':out.source=='deterministic'})
    out=explain(rec,provider=lambda *_:{'unexpected':'malformed'})
    results.append({'id':'malformed','expected':'deterministic','actual':out.source,'passed':out.source=='deterministic'})
    report={'evaluation_type':'offline deterministic guardrail cases; no live LLM accuracy claim','cases':results,'passed':sum(r['passed'] for r in results),'total':len(results)}
    save_json(REPORTS/'llm_evaluation.json',report)
    print(f"{report['passed']}/{report['total']} offline guardrail cases passed")
    assert all(r['passed'] for r in results)
if __name__=='__main__': main()
