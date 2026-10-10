"""Use-case screening only. The bank must supply authoritative credit/product rules."""
import math
CATALOGUE={'GP01':{'name':'EV Finance','purpose':'Finance an EV purchase or replacement'},'GP02':{'name':'Green Home Loan','purpose':'Finance owner-authorized home energy improvements'},'GP03':{'name':'Solar Finance','purpose':'Finance suitable owner-authorized rooftop solar'},'GP04':{'name':'Paperless Banking','purpose':'Switch existing paper statements to digital delivery'}}
def missing(v): return v is None or (isinstance(v,float) and math.isnan(v))
def screen(pid,f):
    exclusions=[]; unknown=[]
    required={'GP01':['vehicle_ownership','owns_ev','vehicle_type','replacement_intent'],'GP02':['homeowner'],'GP03':['homeowner','roof_suitable'],'GP04':['paper_statements_enabled']}[pid]
    unknown=[k for k in required if missing(f.get(k))]
    if pid in ['GP02','GP03'] and f.get('homeowner')==0: exclusions.append('NOT_HOME_OWNER')
    if pid=='GP03' and f.get('roof_suitable')==0: exclusions.append('ROOF_UNSUITABLE')
    if pid=='GP01':
        if f.get('owns_ev')==1 and f.get('replacement_intent')==0: exclusions.append('EXISTING_EV_NO_REPLACEMENT')
        if (f.get('owns_ev')==1 and f.get('vehicle_type') in ['petrol','diesel','none']) or (f.get('owns_ev')==0 and f.get('vehicle_type')=='electric'): unknown.append('CONFLICTING_VEHICLE_DATA')
    if pid=='GP04' and f.get('paper_statements_enabled')==0: exclusions.append('ALREADY_PAPERLESS')
    return {'status':'excluded' if exclusions else 'needs_review' if unknown else 'use_case_match','applicable_exclusions':exclusions,'missing_or_conflicting':unknown,'financial_eligibility':'not_assessed','institutional_rules_required':True}
