from typing import Literal
from pydantic import BaseModel, Field

Scalar = str | float | int | bool | None
Status = Literal['POTENTIAL_OPPORTUNITY', 'EXCLUDED', 'INSUFFICIENT_DATA', 'NEEDS_REVIEW']

class Health(BaseModel):
    status: str
    models_available: bool
    data_available: bool
    model_version: str
    synthetic: bool = True

class Customer(BaseModel):
    customer_id: str
    features: dict[str, Scalar]
    data_timestamp: str
    synthetic: bool = True
    products: list[dict[str, Scalar]] = []

class CustomerPage(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[Customer]

class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    transaction_date: str
    merchant_name: str
    merchant_description: str
    amount_gbp: float
    sustainability_category: str
    category_source: str = 'synthetic reference label'

class TransactionPage(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[Transaction]

class Impact(BaseModel):
    impact_status: Literal['ESTIMATED', 'UNAVAILABLE']
    horizon: str = 'annual'
    baseline_kgco2e: float | None = None
    scenario_kgco2e: float | None = None
    avoided_kgco2e: float | None = None
    avoided_pages: float | None = None
    generation_kwh: float | None = None
    assumptions: list[str] = []
    factors: list[dict[str, Scalar]] = []
    limitations: list[str] = []
    reason: str | None = None
    accounting: str = 'Operational scenario estimate; not financed emissions or guaranteed realized savings'

class Recommendation(BaseModel):
    customer_id: str
    product_id: str
    product_name: str
    propensity: float = Field(ge=0, le=1)
    threshold_screen: dict[str, Scalar]
    confidence: float | None = None
    reliability: dict[str, Scalar]
    status: Status
    financial_eligibility: str = 'NOT_ASSESSED'
    applicable_exclusions: list[str]
    missing_or_conflicting: list[str]
    reason_codes: list[str]
    evidence: dict[str, Scalar]
    data_timestamp: str
    model_version: str
    impact: Impact
    recommended_action: str

class OpportunityResponse(BaseModel):
    customer_id: str
    opportunities: list[Recommendation]

class Explanation(BaseModel):
    product_id: str
    source: Literal['deterministic', 'openai_validated_selection']
    insight: str
    evidence: str
    impact: str
    limitations: str
    action: str
    fallback_reason: str | None = None

class Spending(BaseModel):
    month: str
    category: str
    amount_gbp: float

class Insights(BaseModel):
    customer_id: str
    explanations: list[Explanation]
    monthly_spending: list[Spending]

class ProductSummary(BaseModel):
    product_id: str
    product_name: str
    potential_customers: int
    status_counts: dict[str, int]
    propensity_histogram: list[int]
    priority_threshold: float
    priority_threshold_matches: int
    calculable_impact_customers: int
    conditional_avoided_kgco2e: float | None
    conditional_avoided_pages: float | None

class BusinessSummary(BaseModel):
    total_customers: int
    unique_customers_with_opportunities: int
    products: list[ProductSummary]
    data_timestamp: str
    model_version: str
    caveat: str

class Segment(BaseModel):
    region: str
    age_band: str
    customers: int
    potential_customers: int

class Segments(BaseModel):
    items: list[Segment]

class BusinessOpportunities(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[Recommendation]

class ClassifyRequest(BaseModel):
    merchant_name: str = Field(default='', max_length=200)
    merchant_description: str = Field(default='', max_length=500)

class ClassifyResponse(BaseModel):
    category: str
    confidence: float | None
    needs_review: bool
    confidence_kind: str | None = None
    reason: str | None = None
