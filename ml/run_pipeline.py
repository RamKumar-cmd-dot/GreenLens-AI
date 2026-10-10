"""Safe pipeline entry point: no arguments verify the existing cohort and saved models."""
import argparse
from ml.common import DATA, MODELS, REPORTS


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--regenerate-data', action='store_true', help='Regenerate the synthetic relational tables')
    parser.add_argument('--london-summary', help='Optional inspected summary used only to inform synthetic energy demand')
    parser.add_argument('--rebuild-features', action='store_true', help='Rebuild Customer 360 from current synthetic tables')
    parser.add_argument('--retrain-models', action='store_true', help='Fit and replace propensity/classification models and metrics')
    parser.add_argument('--refresh-metrics', action='store_true', help='Recompute the standard evaluation reports')
    parser.add_argument('--confirm-overwrite', action='store_true', help='Required to replace existing synthetic data or saved models')
    args = parser.parse_args(argv)

    data_exists = (DATA / 'synthetic/customers.csv').exists()
    models_exist = all((MODELS / f'{pid}.joblib').exists() for pid in ('GP01', 'GP02', 'GP03', 'GP04'))
    if args.regenerate_data and data_exists and not args.confirm_overwrite:
        parser.error('Existing cohort found; pass --confirm-overwrite explicitly to regenerate it')
    if args.regenerate_data and not args.retrain_models:
        parser.error('A new cohort requires --retrain-models so models and evaluation stay aligned')
    if args.rebuild_features and not args.retrain_models:
        parser.error('Rebuilding Customer 360 requires --retrain-models to keep artifacts aligned')
    if args.retrain_models and models_exist and not args.confirm_overwrite:
        parser.error('Saved model artifacts found; pass --confirm-overwrite explicitly to retrain and replace them')
    if args.london_summary and not args.regenerate_data:
        parser.error('--london-summary only applies with --regenerate-data')
    if args.rebuild_features and not (args.regenerate_data or data_exists):
        parser.error('Cannot build features without the synthetic relational tables')
    if args.retrain_models and not (args.rebuild_features or (DATA / 'processed/customer_360.csv').exists()):
        parser.error('Cannot train models without Customer 360 features')

    if args.regenerate_data:
        from data.generate_synthetic import generate
        generate(london_summary=args.london_summary, overwrite=True)
        args.rebuild_features = True
    if args.rebuild_features:
        from ml.feature_engineering import build_features
        build_features().to_csv(DATA / 'processed/customer_360.csv', index=False)
    if args.retrain_models:
        from ml.propensity_models import train as train_propensity
        from ml.transaction_classifier import train as train_transactions
        train_propensity()
        train_transactions()
        from ml.tune_thresholds import main as tune_validation_thresholds
        tune_validation_thresholds()
        from ml.evaluate_thresholds import main as evaluate_thresholds_once
        evaluate_thresholds_once()
        args.refresh_metrics = True
    if args.refresh_metrics:
        from ml.evaluate import render
        render()
    if args.regenerate_data or args.rebuild_features:
        from ml.inference import load_models, predict_customer
        load_models.cache_clear()
        from ml.common import save_json
        save_json(REPORTS / 'sample_response.json', predict_customer('C000025'))

    from ml.verify_artifacts import main as verify
    verify()


if __name__ == '__main__':
    main()
