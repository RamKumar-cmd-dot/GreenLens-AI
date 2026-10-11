from typing import Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from backend.scenarios import normalize_selection

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
    references: list[dict[str, Scalar]] = []
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
    confidence_level: Literal['high', 'medium', 'low', 'unavailable'] = 'unavailable'
    confidence_method: str = 'validation-informed reliability assessment v1'
    reliability: dict[str, Any]
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
    presentation_status: Literal['STANDARD', 'EXPLORED', 'DEPRIORITIZED', 'SNOOZED', 'SUPPRESSED', 'INTERESTED'] = 'STANDARD'
    presentation_priority: int = 100
    presentation_note: str | None = None
    customer_memory: dict[str, Any] = Field(default_factory=dict)

class OpportunityResponse(BaseModel):
    customer_id: str
    opportunities: list[Recommendation]

InteractionAction = Literal['explore', 'dismiss', 'remind_later', 'not_interested', 'interested', 'clear']

class FeedbackRequest(BaseModel):
    product_id: Literal['GP01', 'GP02', 'GP03', 'GP04']
    action: InteractionAction
    reason: str | None = Field(default=None, max_length=500)
    snooze_until: datetime | None = None

    @model_validator(mode='after')
    def validate_reminder(self):
        if self.action == 'remind_later':
            if self.snooze_until is None:
                raise ValueError('snooze_until is required for remind_later')
            if self.snooze_until.tzinfo is None or self.snooze_until.utcoffset() is None:
                raise ValueError('snooze_until must include a timezone')
            if self.snooze_until <= datetime.now(timezone.utc):
                raise ValueError('snooze_until must be in the future')
        elif self.snooze_until is not None:
            raise ValueError('snooze_until is only valid for remind_later')
        return self

class CustomerInteraction(BaseModel):
    id: int
    customer_id: str
    product_id: Literal['GP01', 'GP02', 'GP03', 'GP04']
    action: InteractionAction
    reason: str | None = None
    created_at: str
    snooze_until: str | None = None

class CustomerInteractionPage(BaseModel):
    customer_id: str
    total: int
    offset: int
    limit: int
    items: list[CustomerInteraction]

class FeedbackResponse(BaseModel):
    customer_id: str
    interaction: CustomerInteraction
    recommendation: Recommendation
    message: str

class ScenarioRequest(BaseModel):
    apply: list[str] | None = None
    # Kept for clients of the former two-button API; only its original EV and
    # Paperless payloads are accepted and translated to canonical chip IDs.
    changes: dict[str, Scalar] | None = None

    @model_validator(mode='after')
    def normalize_chips(self):
        try:
            self.apply = normalize_selection(self.apply, self.changes)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return self


class ScenarioChipNote(BaseModel):
    chip_id: Literal['EV', 'GREEN_HOME', 'SOLAR', 'PAPERLESS']
    changed_features: list[str]
    note: str


class ScenarioSide(BaseModel):
    propensity: float = Field(ge=0, le=1)
    status: Status
    confidence_level: Literal['high', 'medium', 'low', 'unavailable']
    reason_codes: list[str]
    evidence: dict[str, Scalar]
    impact: Impact


class ScenarioComparison(BaseModel):
    product_id: Literal['GP01', 'GP02', 'GP03', 'GP04']
    product_name: str
    baseline: ScenarioSide
    scenario: ScenarioSide

class ScenarioResponse(OpportunityResponse):
    scenario_changes: dict[str, Scalar]
    applied_chips: list[str] = Field(default_factory=list)
    changed_attributes: dict[str, Scalar] = Field(default_factory=dict)
    original_attributes: dict[str, Scalar] = Field(default_factory=dict)
    chip_notes: list[ScenarioChipNote] = Field(default_factory=list)
    comparisons: list[ScenarioComparison] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    synthetic: bool = True

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
    portfolio_energy_kwh_year: float | None = None
    paperless_customers: int
    paperless_adoption_rate: float | None = None
    mobile_app_active_customers: int
    mean_monthly_digital_logins: float | None = None

class Segment(BaseModel):
    region: str
    age_band: str
    customers: int
    potential_customers: int

class Segments(BaseModel):
    items: list[Segment]

class BusinessTrendPoint(BaseModel):
    month: str
    category: str
    amount_gbp: float

class BusinessTrends(BaseModel):
    items: list[BusinessTrendPoint]
    data_timestamp: str
    caveat: str

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
