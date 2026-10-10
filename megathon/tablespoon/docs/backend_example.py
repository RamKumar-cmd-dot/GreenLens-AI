"""Copy this adapter into the backend; FastAPI is intentionally not an ML dependency.

Response values are native JSON types. Keep backend authorization, institutional
eligibility, carbon computation, and explanation generation in separate services.
"""
from ml.inference import load_models, predict_customer, predict_opportunities, classify_transaction

# In the FastAPI lifespan/startup hook: load_models()
# GET /customers/{customer_id}/opportunities -> predict_customer(customer_id)
# POST /opportunities -> predict_opportunities(validated_customer_360.model_dump())
# POST /transactions/classify -> classify_transaction(transaction.model_dump())
# Catch ValueError as 422; KeyError as 404. Run CPU inference off async event loop.
# Backend must authenticate/authorize customer access before calling these helpers.
