"""One-command reproduction of the complete demonstration pipeline."""
from data.generate_synthetic import generate
from ml.feature_engineering import build_features
from ml.propensity_models import train as train_propensity
from ml.transaction_classifier import train as train_transactions
from ml.evaluate import render
from ml.common import *

def main():
    generate()
    import pandas as pd
    schema={}
    for path in (DATA/'synthetic').glob('*.csv'):
        frame=pd.read_csv(path,nrows=100)
        schema[path.stem]={'columns':{c:str(t) for c,t in frame.dtypes.items()},'customer_key':'customer_id','primary_key':'transaction_id' if path.stem=='transactions' else ['customer_id','product_type','start_date'] if path.stem=='customer_products' else 'customer_id','provenance':'synthetic_simulated_outcome' if path.stem=='product_takeup_labels' else 'synthetic_snapshot_or_estimate'}
    save_json(DATA/'schemas/relational_schema.json',schema)
    build_features().to_csv(DATA/'processed/customer_360.csv',index=False)
    save_json(DATA/'schemas/feature_schema.json',{'version':VERSION,'numeric':NUMERIC,'categorical':CATEGORICAL,'features':FEATURES,'missing':'null; numeric median and categorical most-frequent imputation fitted on training only','additional_fields':['customer_id','data_timestamp'],'targets_forbidden':list(TARGETS.values())})
    from ml.eligibility import CATALOGUE
    save_json(DATA/'schemas/product_catalogue.json',CATALOGUE)
    train_propensity(); train_transactions(); render()
    from ml.inference import predict_customer, load_models
    load_models.cache_clear()
    save_json(REPORTS/'sample_response.json',predict_customer('C000025'))
if __name__=='__main__': main()
