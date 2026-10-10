from collections import Counter
import numpy as np
from ml.common import AS_OF, VERSION, TARGETS
from ml.eligibility import CATALOGUE

def summary(service):
    all_rows=[r for rows in service.by_customer.values() for r in rows]
    products=[]
    for pid in TARGETS:
        rows=[r for r in all_rows if r.product_id==pid]
        potential=[r for r in rows if r.status=='POTENTIAL_OPPORTUNITY']
        carbon=[r.impact.avoided_kgco2e for r in potential if r.impact.avoided_kgco2e is not None]
        pages=[r.impact.avoided_pages for r in potential if r.impact.avoided_pages is not None]
        threshold=service.models['thresholds'][pid]
        products.append({'product_id':pid,'product_name':CATALOGUE[pid]['name'],'potential_customers':len(potential),'status_counts':dict(Counter(r.status for r in rows)),
            'propensity_histogram':np.histogram([r.propensity for r in rows],bins=[0,.2,.4,.6,.8,1.0000001])[0].tolist(),
            'priority_threshold':threshold,'priority_threshold_matches':sum(r.propensity>=threshold for r in potential),'calculable_impact_customers':sum(r.impact.impact_status=='ESTIMATED' for r in potential),
            'conditional_avoided_kgco2e':sum(carbon) if carbon else None,'conditional_avoided_pages':sum(pages) if pages else None})
    return {'total_customers':len(service.by_customer),'unique_customers_with_opportunities':len({r.customer_id for r in all_rows if r.status=='POTENTIAL_OPPORTUNITY'}),'products':products,'data_timestamp':AS_OF,'model_version':VERSION,'caveat':'Priority thresholds were selected on validation data for statistical prioritization only. Matches are use-case screens, not financial approvals. Product matches overlap. Impact totals assume every calculable match adopts its scenario, are not probability-weighted or forecasts, and must not be added across overlapping products.'}

def segments(service):
    rows=[]
    for (region,age),g in service.features.groupby(['region','age_band'],dropna=False):
        rows.append({'region':str(region),'age_band':str(age),'customers':len(g),'potential_customers':sum(any(r.status=='POTENTIAL_OPPORTUNITY' for r in service.by_customer[cid]) for cid in g.customer_id)})
    return {'items':rows}

def opportunities(service, product_id, status, offset, limit, region=None, above_threshold=None):
    allowed=set(service.features.loc[service.features.region==region,'customer_id']) if region else None
    rows=[r for cid,rs in service.by_customer.items() if allowed is None or cid in allowed for r in rs if (not product_id or r.product_id==product_id) and r.status==status and (above_threshold is None or r.threshold_screen['above_threshold']==above_threshold)]
    # Relevance and impact coverage precede propensity; exclusions are never ranked as offers.
    rows.sort(key=lambda r:(r.impact.impact_status=='ESTIMATED',bool(r.reason_codes),r.propensity),reverse=True)
    return {'total':len(rows),'offset':offset,'limit':limit,'items':rows[offset:offset+limit]}
