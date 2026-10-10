"""Create a clearly labelled LCL coverage/energy profile without claiming complete days."""
import json
import numpy as np
import pandas as pd

SOURCE = 'data/processed/lcl_household_features.csv'
OUTPUT = 'data/processed/london_summary_profile.csv'


def main():
    frame = pd.read_csv(SOURCE)
    required = {'LCLid', 'electricity_kwh_year', 'readings_count'}
    if not required <= set(frame.columns):
        raise ValueError(f'{SOURCE} must contain {sorted(required)}; found {list(frame.columns)}')
    frame['coverage_days_proxy'] = frame['readings_count'] // 48
    frame['mean_annualized_daily_kwh'] = frame['electricity_kwh_year'] / 365
    valid = frame[
        (frame['coverage_days_proxy'] >= 7)
        & np.isfinite(frame['mean_annualized_daily_kwh'])
        & (frame['mean_annualized_daily_kwh'] > 0)
    ].copy()
    valid[['LCLid', 'coverage_days_proxy', 'mean_annualized_daily_kwh']].to_csv(OUTPUT, index=False)
    metadata = {
        'source_file': SOURCE,
        'output_file': OUTPUT,
        'source_dataset': 'Low Carbon London historical half-hour electricity readings',
        'units': {'mean_annualized_daily_kwh': 'kWh/day'},
        'coverage_days_proxy': 'floor(readings_count / 48); not a count of calendar days with 48 distinct valid readings',
        'mean_annualized_daily_kwh': 'electricity_kwh_year / 365; derived from mean observed half-hour reading annualized by process_lcl.py, not a verified daily profile',
        'limitations': 'Historical meter averages inform only variability in synthetic demand; no meter identity is linked to a synthetic banking customer. Missing intervals, duplicate timestamps, DST and complete-day coverage were not verified by the aggregate source file.'
    }
    with open('data/processed/london_summary_profile_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f'Wrote {len(valid)} meter profiles to {OUTPUT}')
    print(valid['mean_annualized_daily_kwh'].describe().to_string())
    print('Coverage measure is a reading-count proxy, not verified complete calendar days.')


if __name__ == '__main__':
    main()
