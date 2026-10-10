import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import Health, Customer, CustomerPage, TransactionPage, OpportunityResponse, Insights, BusinessSummary, Segments, BusinessOpportunities, Status
from backend import business
from backend.explanations import explain
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from ml.inference import classify_transaction
from backend.schemas import ClassifyRequest, ClassifyResponse
from backend.store import Store
from backend.recommendations import Recommendations
from ml.common import ROOT, CATEGORIES, VERSION

log = logging.getLogger(__name__)

def create_app(db_path=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.store = Store(db_path or os.getenv('GREENLENS_DB', str(ROOT/'data/processed/greenlens.sqlite')))
        app.state.data_available = False
        app.state.service = None
        try:
            app.state.store.initialize()
            app.state.data_available = True
            app.state.service = Recommendations(app.state.store)
        except Exception:
            log.exception('Startup dependency unavailable; serving health and explicit 503 responses')
        yield
    app = FastAPI(title='GreenLens AI', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','), allow_methods=['GET','POST'], allow_headers=['Content-Type'])

    def store():
        if not app.state.data_available: raise HTTPException(503,'Customer data unavailable')
        return app.state.store
    def service():
        if app.state.service is None: raise HTTPException(503,'Saved models unavailable')
        return app.state.service
    def lookup(fn, *args, **kwargs):
        try: return fn(*args, **kwargs)
        except KeyError: raise HTTPException(404,'Unknown customer')
        except ValueError as exc: raise HTTPException(422,str(exc))

    @app.get('/health', response_model=Health)
    def health():
        return {'status':'ok' if app.state.service else 'degraded','models_available':app.state.service is not None,'data_available':app.state.data_available,'model_version':VERSION}
    @app.get('/customers', response_model=CustomerPage)
    def customers(offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),region:str|None=None,q:str|None=Query(None,max_length=64)):
        return store().customers(offset,limit,region,q)
    @app.get('/customers/{customer_id}', response_model=Customer)
    def customer(customer_id:str): return lookup(store().customer,customer_id)
    @app.get('/customers/{customer_id}/transactions', response_model=TransactionPage)
    def transactions(customer_id:str,offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),category:str|None=None):
        if category is not None and category not in CATEGORIES: raise HTTPException(422,'Unknown sustainability category')
        return lookup(store().transactions,customer_id,offset,limit,category)
    @app.get('/customers/{customer_id}/opportunities', response_model=OpportunityResponse)
    def opportunities(customer_id:str): return lookup(service().customer,customer_id)
    @lru_cache(maxsize=256)
    def explanations(customer_id):
        with ThreadPoolExecutor(max_workers=4) as executor:
            return list(executor.map(explain,lookup(service().customer,customer_id)['opportunities']))
    @app.get('/customers/{customer_id}/insights',response_model=Insights)
    def insights(customer_id:str):
        lookup(store().customer,customer_id)
        return {'customer_id':customer_id,'explanations':explanations(customer_id),'monthly_spending':store().spending(customer_id)}
    @app.get('/business/summary',response_model=BusinessSummary)
    def business_summary(): return business.summary(service())
    @app.get('/business/segments',response_model=Segments)
    def business_segments(): return business.segments(service())
    @app.get('/business/opportunities',response_model=BusinessOpportunities)
    def business_opportunities(product_id:str|None=None,status:Status='POTENTIAL_OPPORTUNITY',offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),region:str|None=None):
        if product_id and product_id not in ['GP01','GP02','GP03','GP04']: raise HTTPException(422,'Unknown product')
        return business.opportunities(service(),product_id,status,offset,limit,region)
    @app.post('/transactions/classify',response_model=ClassifyResponse)
    def classify(body:ClassifyRequest):
        service()
        return lookup(classify_transaction,body.model_dump())
    return app

app = create_app()
