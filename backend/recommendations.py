from ml.common import FEATURES, TARGETS, VERSION
from ml.eligibility import CATALOGUE, screen, missing
from ml.inference import load_models, reasons, normalize, validation_score_band
from backend.schemas import Recommendation, Impact
from backend.impact import estimate
from backend.eligibility import assess

def assemble(features, pid, score, metadata, threshold=None):
    if threshold is None:
        threshold = load_models()['thresholds'][pid]
    features = {**features, **normalize(features)}
    status, rule = assess(pid, features)
    # Keep use-case screening distinct from credit approval and model probability.
    issues = rule['missing_or_conflicting']
    codes, evidence = reasons(pid, features)
    action = {'EXCLUDED':'Review the exclusion; no application is suggested.', 'INSUFFICIENT_DATA':'Confirm the missing information with your relationship team.', 'NEEDS_REVIEW':'Resolve conflicting information before considering this product.', 'POTENTIAL_OPPORTUNITY':'Explore the illustrative scenario with your relationship team; institutional checks still apply.'}[status]
    return Recommendation(customer_id=features['customer_id'], product_id=pid, product_name=CATALOGUE[pid]['name'], propensity=score,
        threshold_screen={'threshold':threshold,'above_threshold':score>=threshold,'status':'ABOVE_VALIDATION_SELECTED_THRESHOLD' if score>=threshold else 'BELOW_VALIDATION_SELECTED_THRESHOLD','selection_basis':'validation-set F1; statistical prioritization only'},
        reliability={**metadata['products'][pid], 'status':'synthetic_validation_score_band_only', 'per_customer_confidence':'unavailable', 'validation_score_band':validation_score_band(pid,score), 'missing_feature_count':sum(missing(features.get(k)) for k in FEATURES)},
        status=status, applicable_exclusions=rule['applicable_exclusions'], missing_or_conflicting=issues, reason_codes=codes, evidence=evidence,
        data_timestamp=features['data_timestamp'],model_version=VERSION, impact=estimate(pid,features) if status=='POTENTIAL_OPPORTUNITY' else Impact(impact_status='UNAVAILABLE',reason='Use-case screening excludes this scenario or requires more information'), recommended_action=action)

class Recommendations:
    def __init__(self, store):
        self.store = store
        self.models = load_models()
        self.features = store.all_features()
        self.by_customer = {}
        scores = {pid:self.models[pid].predict_proba(self.features[FEATURES])[:,1] for pid in TARGETS}
        for i, row in self.features.iterrows():
            f = row.to_dict()
            self.by_customer[f['customer_id']] = [assemble(f,pid,float(scores[pid][i]),self.models['metadata'],self.models['thresholds'][pid]) for pid in TARGETS]

    def customer(self, cid):
        if cid not in self.by_customer:
            raise KeyError(cid)
        return {'customer_id':cid,'opportunities':self.by_customer[cid]}

    def scenario(self, cid, changes):
        allowed={'vehicle_ownership','vehicle_type','owns_ev','replacement_intent','homeowner','roof_suitable','paper_statements_enabled','electricity_kwh_year','gas_kwh_year','annual_mileage_estimate','digital_logins_month','digital_transaction_ratio'}
        unknown=set(changes)-allowed
        if unknown: raise ValueError(f'Unsupported scenario fields: {sorted(unknown)}')
        if cid not in self.by_customer: raise KeyError(cid)
        f=self.features.loc[self.features.customer_id==cid].iloc[0].to_dict()
        f.update(changes)
        f={**f,**normalize(f)}
        import pandas as pd
        row=pd.DataFrame([f],columns=FEATURES)
        predictions=[]
        for pid in TARGETS:
            score=float(self.models[pid].predict_proba(row)[0,1])
            predictions.append(assemble(f,pid,score,self.models['metadata'],self.models['thresholds'][pid]))
        return {'customer_id':cid,'opportunities':predictions,'scenario_changes':changes,'synthetic':True}
