"""Read-only artifact audit: no fitting or retraining. Run after ml.run_pipeline."""
import json
import joblib
import numpy as np
import pandas as pd
from ml.common import DATA, MODELS, REPORTS, FEATURES, NUMERIC, TARGETS, CATEGORIES, AS_OF, save_json
from ml.evaluate import binary_metrics
from ml.inference import load_models, predict_opportunities


def main():
    customers = pd.read_csv(DATA / 'synthetic/customers.csv')
    ids = set(customers.customer_id)
    assert customers.customer_id.is_unique and customers.customer_id.notna().all()
    tables = {}
    for name in ['transactions', 'customer_assets', 'customer_behaviour', 'customer_products', 'product_takeup_labels']:
        frame = pd.read_csv(DATA / f'synthetic/{name}.csv')
        assert frame.customer_id.notna().all() and set(frame.customer_id) <= ids
        if name not in ['transactions', 'customer_products']:
            assert frame.customer_id.is_unique and set(frame.customer_id) == ids
        tables[name] = frame
    tx = tables['transactions']
    assert tx.transaction_id.is_unique
    assert tx.sustainability_category.notna().all() and set(tx.sustainability_category) == set(CATEGORIES)
    assert np.isfinite(tx.amount_gbp).all() and tx.amount_gbp.gt(0).all()
    dates = pd.to_datetime(tx.transaction_date)
    assert dates.lt(pd.Timestamp(AS_OF)).all()
    labels = tables['product_takeup_labels'].set_index('customer_id')
    assert labels[list(TARGETS.values())].isin([0, 1]).all().all()
    features = pd.read_csv(DATA / 'processed/customer_360.csv').set_index('customer_id')
    assert features.index.is_unique and set(features.index) == ids
    assert not set(TARGETS.values()) & set(features.columns)
    assert not set(TARGETS.values()) & set(FEATURES)
    splits = json.loads((DATA / 'processed/splits.json').read_text())
    groups = {k: set(v) for k, v in splits.items()}
    assert all(len(groups[k]) == len(splits[k]) for k in groups)
    assert set.union(*groups.values()) == ids
    assert not (groups['train'] & groups['validation'] or groups['train'] & groups['test'] or groups['validation'] & groups['test'])
    models = load_models()
    report = {'customers': len(customers), 'transactions': len(tx), 'split_counts': {k: len(v) for k, v in groups.items()}, 'overlapping_customers': 0, 'orphan_records': 0, 'target_columns_in_features': [], 'products': {}}
    train_medians = features.loc[splits['train'], NUMERIC].median().to_numpy()
    for pid, target in TARGETS.items():
        model = models[pid]
        assert list(model.feature_names_in_) == FEATURES
        # Verify serialized imputer statistics against training customers alone.
        imputer = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['impute']
        np.testing.assert_allclose(imputer.statistics_, train_medians)
        scores = model.predict_proba(features[FEATURES])[:, 1]
        assert np.isfinite(scores).all() and ((scores >= 0) & (scores <= 1)).all()
        reloaded = joblib.load(MODELS / f'{pid}.joblib')
        np.testing.assert_allclose(scores, reloaded.predict_proba(features[FEATURES])[:, 1], rtol=0, atol=0)
        saved = json.loads((REPORTS / f'{pid}.json').read_text())
        verified = {}
        for split in ['validation', 'test']:
            subset = features.loc[splits[split], FEATURES]
            predicted = model.predict_proba(subset)[:, 1]
            actual = labels.loc[splits[split], target]
            metrics = binary_metrics(actual, predicted)
            assert metrics == saved[split][saved['selected']]
            verified[split] = metrics
        heldout = pd.read_csv(REPORTS / f'{pid}_test_predictions.csv').set_index('customer_id')
        assert heldout.index.is_unique and set(heldout.index) == groups['test']
        np.testing.assert_allclose(heldout.loc[splits['test'], 'propensity'], model.predict_proba(features.loc[splits['test'], FEATURES])[:, 1])
        np.testing.assert_array_equal(heldout.loc[splits['test'], 'actual'], labels.loc[splits['test'], target])
        report['products'][pid] = {'selected': saved['selected'], 'scored_customers': len(scores), 'min_propensity': float(scores.min()), 'max_propensity': float(scores.max()), 'reload_identical': True, 'training_imputer_verified': True, **verified}
    for payload in [{}, {k: None for k in FEATURES}, {'region': 'unknown_region'}]:
        result = predict_opportunities(payload)
        json.dumps(result, allow_nan=False)
        assert {p['product_id'] for p in result['opportunities']} == set(TARGETS)
        assert all(0 <= p['propensity'] <= 1 and p['recommendation_status'] == 'needs_review' for p in result['opportunities'])
    report['missing_data_cases_passed'] = 3
    report['leakage_scope'] = 'No target fields, disjoint customer partitions, pre-cutoff transactions, training-only fitted numeric imputation; asset/behaviour snapshots rely on the documented synthetic pre-cutoff assumption.'
    save_json(REPORTS / 'artifact_audit.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'products'}, indent=2))
    print('All four saved pipelines reproduce their recorded validation/test metrics; no models fitted.')


if __name__ == '__main__':
    main()
