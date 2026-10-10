"""Inspect first; explicitly map verified source columns in a second invocation."""
import argparse
import hashlib
import json
import zipfile
from contextlib import contextmanager
from pathlib import Path
import pandas as pd
from ml.common import DATA, save_json
@contextmanager
def source(path,member):
    if path.suffix.lower()=='.zip':
        with zipfile.ZipFile(path) as z:
            if member is None: raise ValueError('Provide --member from ZIP inventory: '+str(z.namelist()[:180]))
            with z.open(member) as f: yield f
    else:
        with path.open('rb') as f: yield f

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('path',type=Path); p.add_argument('--member'); p.add_argument('--id-column'); p.add_argument('--timestamp-column'); p.add_argument('--reading-column'); p.add_argument('--timestamp-format'); p.add_argument('--unit',choices=['kWh_per_interval']); p.add_argument('--interval-minutes',type=int); p.add_argument('--max-rows',type=int,default=1000000); p.add_argument('--source-url'); a=p.parse_args()
    with source(a.path,a.member) as f: sample=pd.read_csv(f,nrows=1000)
    inspection={'path':str(a.path),'member':a.member,'columns':list(sample.columns),'dtypes':sample.dtypes.astype(str).to_dict(),'sample_missing_counts':sample.isna().sum().to_dict(),'sample_rows':sample.head(5).astype(object).where(sample.head(5).notna(),None).to_dict('records')}
    save_json(DATA/'processed/london_inspection.json',inspection); print(json.dumps(inspection,default=str,indent=2))
    if not all([a.id_column,a.timestamp_column,a.reading_column,a.timestamp_format,a.unit,a.interval_minutes,a.source_url]):
        print('Inspection only. Verify source documentation and supply all mapping, format, interval, unit and source URL flags to summarize.'); return
    if a.interval_minutes<=0 or 1440%a.interval_minutes: raise ValueError('Interval must evenly divide one day')
    accumulated=[]; count=0; invalid=0
    with source(a.path,a.member) as f:
        for chunk in pd.read_csv(f,chunksize=50000,nrows=a.max_rows):
            count+=len(chunk); t=pd.to_datetime(chunk[a.timestamp_column],format=a.timestamp_format,errors='coerce'); v=pd.to_numeric(chunk[a.reading_column],errors='coerce')
            valid=t.notna()&v.notna()&(v>=0)&chunk[a.id_column].notna(); invalid+=int((~valid).sum())
            accumulated.append(pd.DataFrame({'meter_id':chunk.loc[valid,a.id_column].astype(str),'timestamp':t[valid],'kwh':v[valid]}))
    # Explicit bounded sample, not full archive ingestion. Max rows bounds memory.
    rows=pd.concat(accumulated,ignore_index=True); duplicates=int(rows.duplicated(['meter_id','timestamp'],keep=False).sum())
    rows=rows.drop_duplicates(['meter_id','timestamp'],keep=False); rows['day']=rows.timestamp.dt.date
    daily=rows.groupby(['meter_id','day']).agg(readings=('kwh','size'),observed_kwh=('kwh','sum'),first=('timestamp','min'),last=('timestamp','max')).reset_index()
    expected=1440//a.interval_minutes
    spacing=rows.sort_values(['meter_id','day','timestamp']).groupby(['meter_id','day']).timestamp.diff().dt.total_seconds()
    rows_sorted=rows.sort_values(['meter_id','day','timestamp']).copy(); rows_sorted['bad_interval']=spacing.notna()&(spacing!=a.interval_minutes*60)
    bad=rows_sorted.groupby(['meter_id','day']).bad_interval.any().reset_index()
    daily=daily.merge(bad,on=['meter_id','day']); daily['complete_day']=(daily.readings==expected)&(~daily.bad_interval)
    daily['daily_kwh']=daily.observed_kwh.where(daily.complete_day)
    summary=daily.groupby('meter_id').agg(observed_days=('day','size'),complete_days=('complete_day','sum'),mean_complete_daily_kwh=('daily_kwh','mean'),observed_kwh=('observed_kwh','sum'))
    summary.to_csv(DATA/'processed/london_household_summary.csv')
    save_json(DATA/'processed/london_metadata.json',{'source_url':a.source_url,'path':str(a.path),'member':a.member,'historical_period':'November 2011-February 2014 (source description; verify sample dates)','sample_start':str(rows.timestamp.min()),'sample_end':str(rows.timestamp.max()),'rows_read':count,'invalid_rows':invalid,'duplicate_rows_removed':duplicates,'unit':a.unit,'interval_minutes':a.interval_minutes,'max_rows':a.max_rows,'limitations':'Bounded file-prefix sample may be unrepresentative. No banking identities or labels. No annualization of partial days. DST days may be omitted. Historical demand only; never current customer observations.'})
if __name__=='__main__': main()
