import pandas as pd
import numpy as np
from ml.common import DATA, AS_OF, CATEGORIES

def build_features(source=DATA/'synthetic', as_of=AS_OF):
    read=lambda name:pd.read_csv(source/f'{name}.csv')
    frame=read('customers')
    for table in ['customer_assets','customer_behaviour']: frame=frame.merge(read(table),on='customer_id',validate='one_to_one')
    tx=read('transactions'); dates=pd.to_datetime(tx.transaction_date); cutoff=pd.Timestamp(as_of); start=cutoff-pd.DateOffset(months=12)
    tx=tx.loc[(dates>=start)&(dates<cutoff)].copy(); tx['month']=pd.to_datetime(tx.transaction_date).dt.to_period('M')
    for cat in CATEGORIES[:5]:
        name='mean_monthly_'+cat.lower().replace(' ','_'); frame[name]=frame.customer_id.map(tx.loc[tx.sustainability_category==cat].groupby('customer_id').amount_gbp.sum()/12).fillna(0)
    fuel=tx[tx.sustainability_category=='Fuel']; recent=fuel[pd.to_datetime(fuel.transaction_date)>=cutoff-pd.DateOffset(months=3)].groupby('customer_id').amount_gbp.sum()/3
    early=fuel[pd.to_datetime(fuel.transaction_date)<start+pd.DateOffset(months=3)].groupby('customer_id').amount_gbp.sum()/3
    frame['fuel_trend']=frame.customer_id.map(recent.subtract(early,fill_value=0)).fillna(0)
    products=read('customer_products'); active=(pd.to_datetime(products.start_date)<cutoff)&(products.end_date.isna()|(pd.to_datetime(products.end_date)>=cutoff))&(products.product_status=='active')
    for product in ['mortgage','vehicle_loan']: frame['existing_'+product]=frame.customer_id.isin(products.loc[active&(products.product_type==product),'customer_id']).astype(int)
    frame['data_timestamp']=as_of
    return frame
if __name__=='__main__':
    frame=build_features(); frame.to_csv(DATA/'processed/customer_360.csv',index=False); print(f'Customer 360: {frame.shape}')
