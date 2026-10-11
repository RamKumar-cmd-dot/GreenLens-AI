"""Generate GreenLens AI Final Deck PPTX."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="deliverables/GreenLens_AI_Final_Deck.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # blank layout

    # Colors
    DARK_GREEN = RGBColor(18, 65, 48)       # #124130
    CHARCOAL = RGBColor(45, 55, 72)          # #2D3748
    MUTED_TEXT = RGBColor(100, 116, 139)     # #64748B
    CARD_BG = RGBColor(241, 245, 243)        # #F1F5F3
    BORDER_COL = RGBColor(203, 213, 225)     # #CBD5E1
    ACCENT_RED = RGBColor(197, 48, 48)       # #C53030
    ACCENT_GREEN = RGBColor(34, 139, 34)     # #228B22
    WHITE = RGBColor(255, 255, 255)

    slides_data = [
        # Slide 1
        {
            "num": 1,
            "category": "MEGATHON X: SINGULARITY · PS1 (LLOYDS)",
            "title": "GreenLens AI",
            "subtitle": "An Explainable Green Customer Insights Platform Grounded in Evidence",
            "team": "Team 43",
            "is_title": True,
            "speaker": "Speaker 1",
            "bullets": [
                "Transforms routine customer transactions into verified green product opportunities.",
                "Enforces strict boundaries between ML predictions, carbon calculations, and bank rules.",
                "Delivers dual dashboards for retail customers and banking relationship teams."
            ]
        },
        # Slide 2
        {
            "num": 2,
            "category": "PROBLEM & OPPORTUNITY",
            "title": "Why Green Banking Needs Strict Separation",
            "speaker": "Speaker 1",
            "bullets": [
                "Missing Context: Banks see monthly spend and account history, but struggle to spot actionable, relevant green transitions.",
                "The Greenwashing Risk: Unsubstantiated carbon claims damage trust. Customers and regulators demand transparent, documented calculations.",
                "Who Benefits: Retail customers get personalized, non-intrusive green options; relationship managers see vetted, audit-ready portfolio opportunities.",
                "Our Standard: Practical guidance without confusing sales propensity with credit eligibility or real-world loan approval."
            ],
            "visual_type": "benefit_cards"
        },
        # Slide 3
        {
            "num": 3,
            "category": "CORE PRINCIPLE",
            "title": "The Four-Way Division of Responsibility",
            "speaker": "Speaker 1",
            "bullets": [
                "ML Models Predict: Estimate simulated customer take-up propensity from historical spending and profile features.",
                "Rules-Based Carbon Engine Calculates: Computes operational emission impacts using verified 2025 UK government factors.",
                "Product Rules Decide Eligibility: Enforce explicit exclusions (e.g. existing EV) and data-integrity holds independently of ML scores.",
                "LLM Only Explains: Acts as a safe sentence selector from pre-approved templates; never calculates, predicts, or approves."
            ],
            "visual_type": "four_pillars"
        },
        # Slide 4
        {
            "num": 4,
            "category": "TECHNICAL ARCHITECTURE",
            "title": "A Modular, Read-Only Production Pipeline",
            "speaker": "Speaker 2",
            "bullets": [
                "Immutable Snapshot: Relational customer data and transactions import into SQLite without live mutation.",
                "Batch Inference: Four trained scikit-learn pipelines load once at startup and score 5,000 customers.",
                "Two-Tier Evaluation: Propensity scores feed into independent business-eligibility screens and deterministic carbon logic.",
                "Constrained Delivery: Typed FastAPI contracts serve twin React dashboards with offline deterministic fallbacks."
            ],
            "visual_type": "pipeline_diagram"
        },
        # Slide 5
        {
            "num": 5,
            "category": "DATA & LEAKAGE CONTROL",
            "title": "Synthetic Cohort with Strict Split Hygiene",
            "speaker": "Speaker 2",
            "bullets": [
                "Full Synthetic UK Cohort: 5,000 customers and 368,323 transactions with realistic UK spending distributions.",
                "Clean Split Partitioning: 3,500 train / 750 validation / 750 test customers. Split by customer ID with zero cross-set leakage.",
                "Pre-Cutoff Features: All Customer 360 attributes compute strictly before the synthetic prediction cutoff date.",
                "Saved Training Imputers: Numeric missing-value imputers use training medians only, verified by automated audit scripts."
            ],
            "visual_type": "data_table"
        },
        # Slide 6
        {
            "num": 6,
            "category": "MACHINE LEARNING EVALUATION",
            "title": "Propensity Results & The Unseen-Merchant Check",
            "speaker": "Speaker 3",
            "bullets": [
                "All Four Propensity Models Beat Baselines: GP01 EV (AUC 0.751), GP02 Home (0.815), GP03 Solar (0.901), GP04 Paperless (0.866).",
                "Transaction Classifier: TF-IDF achieves 0.980 test macro F1 on customer-held-out splits vs 0.918 for rule baseline.",
                "Honest Diagnostic Finding: On a merchant-held-out split (7 unseen merchants), TF-IDF drops to 0.095 while the rule baseline retains 0.921.",
                "Engineering Takeaway: The classifier learned merchant names, not general concepts. We document this open limitation."
            ],
            "visual_type": "ml_results_table"
        },
        # Slide 7
        {
            "num": 7,
            "category": "SUSTAINABILITY ENGINE",
            "title": "Deterministic Scenarios & Honest Boundary Limits",
            "speaker": "Speaker 4",
            "bullets": [
                "UK Government Factors: Uses official 2025 DESNZ conversion factors (petrol 2.069 kg/L, diesel 2.571 kg/L, grid electricity 0.177 kg/kWh).",
                "Operational Scenarios: EV scenario compares annual petrol emissions against grid charging; Green Home models a 10% gas efficiency package.",
                "Solar Regional Bound: Solar models a 4 kWp London reference system (919 kWh/kWp/yr yield); other regions return UNAVAILABLE without local yield.",
                "Paperless Boundary: Shows 48 pages/year avoided; CO2 is UNAVAILABLE because no verified lifecycle envelope factor exists."
            ],
            "visual_type": "carbon_box"
        },
        # Slide 8
        {
            "num": 8,
            "category": "EXPLAINABILITY & TRUST",
            "title": "Transparent Evidence, Reason Codes & Exclusions",
            "speaker": "Speaker 3",
            "bullets": [
                "Auditable Reason Codes: Every flagged opportunity surfaces plain reasons (e.g. HIGH_FUEL_SPEND, EXISTING_PETROL_VEHICLE).",
                "Full Evidence Drawer: Customers and advisors inspect exact inputs (fuel spend £288.70, mileage 24,033) and conversion source URLs.",
                "Qualitative Reliability Tiers: Tiers (High / Medium / Low / Unavailable) evaluate feature completeness, training familiarity, and validation calibration.",
                "Dedicated Exclusion Section: Ineligible customers (e.g. EXISTING_EV) appear under 'Not recommended' with clear explanations."
            ],
            "visual_type": "trust_legend"
        },
        # Slide 9
        {
            "num": 9,
            "category": "LIVE APPLICATION DEMONSTRATION",
            "title": "Interactive Customer & Business Workspaces",
            "speaker": "Speaker 5",
            "bullets": [
                "Step 1: Customer C002056: High fuel spend triggers EV Finance (58% propensity) with 4,000+ kgCO2e conditional savings.",
                "Step 2: Customer C000042: High EV propensity is suppressed to EXCLUDED by rule EXISTING_EV_NO_REPLACEMENT.",
                "Step 3: What-If Scenario Explorer (C000018): Toggle EV or Paperless chips to re-run models dynamically without altering database records.",
                "Step 4: Business Dashboard: Portfolio view across 5,000 customers with drill-down from segment to evidence and actions."
            ],
            "visual_type": "demo_placeholders"
        },
        # Slide 10
        {
            "num": 10,
            "category": "RESPONSIBLE AI & GOVERNANCE",
            "title": "Guarded LLM Explanations & Ethics by Design",
            "speaker": "Speaker 4",
            "bullets": [
                "Zero Free-Form Hallucinations: LLM is a constrained style selector choosing only between pre-approved factual sentences.",
                "Verified Offline Guardrails: 28/28 offline test cases pass (including 4/4 missing or conflicting data checks); fails closed to deterministic templates.",
                "Privacy & Compliance: Customer IDs and personal identifiable markers are stripped before any external API payload.",
                "Customer Autonomy: Interactive memory controls allow users to snooze ('Remind me later'), explore, or dismiss recommendations."
            ],
            "visual_type": "responsible_pillars"
        },
        # Slide 11
        {
            "num": 11,
            "category": "LIMITATIONS & ROADMAP",
            "title": "Honest Limitations & Next Steps",
            "speaker": "Speaker 2",
            "bullets": [
                "Synthetic Cohort: Metrics reflect the synthetic data generator; validation on real banking transactions is required before deployment.",
                "Merchant Generalization: Unseen merchants require hybrid regex and fuzzy merchant-name dictionaries.",
                "Local Solar Data: Expanding beyond London requires postcode-level solar irradiance and EPC roof data.",
                "Future Roadmap: Integrate PCAF-aligned financed emissions reporting and test live LLM provider responses."
            ],
            "visual_type": "roadmap_timeline"
        },
        # Slide 12
        {
            "num": 12,
            "category": "CONCLUSION",
            "title": "GreenLens AI: Actionable, Transparent Green Banking",
            "speaker": "Speaker 1",
            "bullets": [
                "Meeting the Brief: Complete 4-product green insights platform with customer and relationship team dashboards.",
                "Spine of the System: Machine learning predicts take-up, deterministic rules compute carbon, and AI explains with facts.",
                "Audit-Ready Integrity: Transparent about synthetic limits, unseen-merchant failure, and unavailable calculations.",
                "Thank you for your time. Team 43 is ready for questions."
            ],
            "visual_type": "summary_card"
        }
    ]

    for data in slides_data:
        slide = prs.slides.add_slide(blank_layout)

        # Header background banner
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.3))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.text = data["category"]
        p0.font.name = "Calibri"
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = MUTED_TEXT

        p1 = tf.add_paragraph()
        p1.text = data["title"]
        p1.font.name = "Calibri"
        p1.font.size = Pt(28 if not data.get("is_title") else 38)
        p1.font.bold = True
        p1.font.color.rgb = DARK_GREEN
        p1.space_before = Pt(4)

        # Slide Number & Speaker footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.733), Inches(0.4))
        ftf = footer_box.text_frame
        ftf.word_wrap = True
        ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
        fp = ftf.paragraphs[0]
        fp.text = f"GreenLens AI · Team 43  |  Slide {data['num']} of 12  |  Suggested Presenter: {data['speaker']}"
        fp.font.name = "Calibri"
        fp.font.size = Pt(10)
        fp.font.color.rgb = MUTED_TEXT

        # Left / Main bullet area
        is_title = data.get("is_title", False)
        left_w = Inches(6.5) if not is_title else Inches(11.5)
        content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.9), left_w, Inches(4.7))
        ctf = content_box.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_top = ctf.margin_right = ctf.margin_bottom = 0

        if is_title:
            sub_p = ctf.paragraphs[0]
            sub_p.text = data.get("subtitle", "")
            sub_p.font.name = "Calibri"
            sub_p.font.size = Pt(18)
            sub_p.font.color.rgb = CHARCOAL
            sub_p.space_after = Pt(24)

            for b in data["bullets"]:
                bp = ctf.add_paragraph()
                bp.text = f"•   {b}"
                bp.font.name = "Calibri"
                bp.font.size = Pt(16)
                bp.font.color.rgb = CHARCOAL
                bp.space_before = Pt(10)
        else:
            for idx, b in enumerate(data["bullets"]):
                bp = ctf.paragraphs[0] if idx == 0 else ctf.add_paragraph()
                # Split title part if colon exists
                if ": " in b:
                    lead, rest = b.split(": ", 1)
                    r1 = bp.add_run()
                    r1.text = f"•   {lead}: "
                    r1.font.bold = True
                    r1.font.color.rgb = DARK_GREEN
                    r2 = bp.add_run()
                    r2.text = rest
                    r2.font.color.rgb = CHARCOAL
                else:
                    bp.text = f"•   {b}"
                    bp.font.color.rgb = CHARCOAL
                bp.font.name = "Calibri"
                bp.font.size = Pt(13)
                bp.space_before = Pt(12)

        # Right visual area (if not title)
        if not is_title:
            right_x = Inches(7.7)
            right_y = Inches(1.9)
            right_w = Inches(4.8)
            right_h = Inches(4.6)

            # Draw container card
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x, right_y, right_w, right_h)
            card.fill.solid()
            card.fill.fore_color.rgb = CARD_BG
            card.line.color.rgb = BORDER_COL
            card.line.width = Pt(1)

            # Card inner text
            c_tf = card.text_frame
            c_tf.word_wrap = True
            c_tf.margin_left = c_tf.margin_right = Inches(0.25)
            c_tf.margin_top = Inches(0.2)

            cp0 = c_tf.paragraphs[0]
            cp0.font.name = "Calibri"
            cp0.font.size = Pt(12)
            cp0.font.bold = True
            cp0.font.color.rgb = DARK_GREEN

            vtype = data.get("visual_type")
            if vtype == "benefit_cards":
                cp0.text = "STAKEHOLDER BENEFITS"
                items = [
                    ("Retail Customer", "Actionable, non-intrusive green options based on actual circumstances."),
                    ("Relationship Manager", "Pre-filtered commercial portfolio opportunities with verified reasons."),
                    ("Compliance & Risk", "Deterministic calculations with zero LLM hallucination or lending bias.")
                ]
                for role, desc in items:
                    p = c_tf.add_paragraph()
                    p.text = f"\n{role}"
                    p.font.bold = True
                    p.font.size = Pt(11)
                    p.font.color.rgb = DARK_GREEN
                    p2 = c_tf.add_paragraph()
                    p2.text = desc
                    p2.font.size = Pt(10)
                    p2.font.color.rgb = CHARCOAL

            elif vtype == "four_pillars":
                cp0.text = "THE BRIEF'S CORE RULE"
                pillars = [
                    ("ML Models", "Predict simulated take-up propensity", DARK_GREEN),
                    ("Carbon Engine", "Computes documented annual kgCO2e", DARK_GREEN),
                    ("Product Rules", "Decide eligibility & strict exclusions", ACCENT_RED),
                    ("LLM Layer", "Only explains structured facts", CHARCOAL)
                ]
                for name, duty, col in pillars:
                    p = c_tf.add_paragraph()
                    p.text = f"\n{name}"
                    p.font.bold = True
                    p.font.size = Pt(11)
                    p.font.color.rgb = col
                    p2 = c_tf.add_paragraph()
                    p2.text = f"→ {duty}"
                    p2.font.size = Pt(10)
                    p2.font.color.rgb = CHARCOAL

            elif vtype == "pipeline_diagram":
                cp0.text = "PIPELINE ARCHITECTURE"
                steps = [
                    "1. Seeded Synthetic CSVs (368k txns)",
                    "2. Pre-Cutoff Customer 360 Features",
                    "3. SQLite Immutable Snapshot",
                    "4. ML Propensity (4) + TF-IDF Classifier",
                    "5. Rules-Based Carbon Engine (2025 DESNZ)",
                    "6. Guardrailed LLM Explanation Layer",
                    "7. FastAPI + React Dashboards"
                ]
                for s in steps:
                    p = c_tf.add_paragraph()
                    p.text = s
                    p.font.size = Pt(10)
                    p.font.color.rgb = CHARCOAL
                    p.space_before = Pt(5)

            elif vtype == "data_table":
                cp0.text = "DATASET & PARTITIONS"
                stats = [
                    ("Total Cohort", "5,000 synthetic UK customers"),
                    ("Transactions", "368,323 category-mapped rows"),
                    ("Training Set", "3,500 customers (70%)"),
                    ("Validation Set", "750 customers (15%)"),
                    ("Held-Out Test", "750 customers (15%)"),
                    ("Partitioning", "Disjoint by customer ID (0% overlap)"),
                    ("Data Origin", "Realistic generator, zero real PII")
                ]
                for k, v in stats:
                    p = c_tf.add_paragraph()
                    p.text = f"{k}: {v}"
                    p.font.size = Pt(10)
                    p.font.color.rgb = CHARCOAL
                    p.space_before = Pt(4)

            elif vtype == "ml_results_table":
                cp0.text = "TEST SET EVALUATION"
                lines = [
                    ("GP01 EV Finance", "AUC 0.751  |  F1: 0.389 (thr 0.24)"),
                    ("GP02 Green Home", "AUC 0.815  |  F1: 0.327 (thr 0.10)"),
                    ("GP03 Solar Finance", "AUC 0.901  |  F1: 0.353 (thr 0.23)"),
                    ("GP04 Paperless", "AUC 0.866  |  F1: 0.577 (thr 0.28)"),
                    ("---", "---"),
                    ("Customer Split", "TF-IDF F1: 0.980 vs Rule 0.918"),
                    ("Merchant Split", "TF-IDF F1: 0.095 vs Rule 0.921")
                ]
                for k, v in lines:
                    p = c_tf.add_paragraph()
                    if k == "---":
                        p.text = "--------------------------------------"
                    else:
                        p.text = f"{k}: {v}"
                    p.font.size = Pt(10)
                    p.font.color.rgb = CHARCOAL
                    p.space_before = Pt(4)

            elif vtype == "carbon_box":
                cp0.text = "WORKED IMPACT EXAMPLE: C002056"
                lines = [
                    "Customer Profile: Petrol car, 24,033 mi/yr",
                    "Baseline Transport: 5,618 kgCO2e/yr",
                    "EV Scenario Grid: 1,234 kgCO2e/yr",
                    "Net Avoided: 4,384 kgCO2e/year",
                    "",
                    "Status Legend:",
                    "• ESTIMATED: EV & Green Home",
                    "• LONDON-ONLY: Solar (919 kWh/kWp)",
                    "• UNAVAILABLE: Paperless CO2 (0 factor)"
                ]
                for l in lines:
                    p = c_tf.add_paragraph()
                    p.text = l
                    p.font.size = Pt(10)
                    p.font.color.rgb = CHARCOAL
                    p.space_before = Pt(3)

            elif vtype == "trust_legend":
                cp0.text = "QUALITATIVE STATUS LEGEND"
                statuses = [
                    ("POTENTIAL_OPPORTUNITY", "Use-case rules met, above priority threshold."),
                    ("EXCLUDED", "Disqualified by bank policy (e.g. owns EV)."),
                    ("NEEDS_REVIEW", "Missing or conflicting verification data."),
                    ("INSUFFICIENT_DATA", "Key inputs absent; impact is UNAVAILABLE.")
                ]
                for st, desc in statuses:
                    p = c_tf.add_paragraph()
                    p.text = f"\n[{st}]"
                    p.font.bold = True
                    p.font.size = Pt(10)
                    p.font.color.rgb = DARK_GREEN if st == "POTENTIAL_OPPORTUNITY" else ACCENT_RED
                    p2 = c_tf.add_paragraph()
                    p2.text = desc
                    p2.font.size = Pt(10)
                    p2.font.color.rgb = CHARCOAL

            elif vtype == "demo_placeholders":
                cp0.text = "LIVE DEMO SCREENSHOTS"
                boxes = [
                    "[SCREENSHOT: customer card C002056]",
                    "[SCREENSHOT: EV exclusion C000042]",
                    "[SCREENSHOT: scenario chips C000018]",
                    "[SCREENSHOT: business view drill-down]"
                ]
                for b in boxes:
                    p = c_tf.add_paragraph()
                    p.text = f"\n{b}"
                    p.font.size = Pt(10)
                    p.font.color.rgb = MUTED_TEXT

            elif vtype == "responsible_pillars":
                cp0.text = "GOVERNANCE & TEST RESULTS"
                checks = [
                    ("Groundedness", "28 / 28 cases passed"),
                    ("Factual Accuracy", "28 / 28 cases passed"),
                    ("Completeness", "28 / 28 cases passed"),
                    ("Numerical Safety", "28 / 28 cases passed"),
                    ("Missing/Conflict", "4 / 4 checks passed"),
                    ("Total Tests", "57 automated tests passed")
                ]
                for k, v in checks:
                    p = c_tf.add_paragraph()
                    p.text = f"• {k}: {v}"
                    p.font.size = Pt(10)
                    p.font.color.rgb = CHARCOAL
                    p.space_before = Pt(4)

            elif vtype == "roadmap_timeline":
                cp0.text = "DEVELOPMENT ROADMAP"
                stages = [
                    ("Phase 1 (Completed)", "Synthetic cohort, 4 propensity models, 2025 DESNZ engine, dual UI."),
                    ("Phase 2 (Immediate)", "Regex/hybrid merchant parsing, London EPC expansion."),
                    ("Phase 3 (Pilot)", "Verified live LLM integration, PCAF-aligned portfolio reporting.")
                ]
                for phase, desc in stages:
                    p = c_tf.add_paragraph()
                    p.text = f"\n{phase}"
                    p.font.bold = True
                    p.font.size = Pt(10)
                    p.font.color.rgb = DARK_GREEN
                    p2 = c_tf.add_paragraph()
                    p2.text = desc
                    p2.font.size = Pt(10)
                    p2.font.color.rgb = CHARCOAL

            elif vtype == "summary_card":
                cp0.text = "KEY TAKEAWAY"
                lines = [
                    "GreenLens AI provides actionable green financial insights by pairing machine learning with strict rules-based governance.",
                    "",
                    "No black-box guesses.",
                    "No unverified carbon numbers.",
                    "Complete transparency."
                ]
                for l in lines:
                    p = c_tf.add_paragraph()
                    p.text = l
                    p.font.size = Pt(10)
                    p.font.color.rgb = CHARCOAL
                    p.space_before = Pt(4)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_deck()
