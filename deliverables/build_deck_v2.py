"""
Generate GreenLens AI High-Contrast, Big-Font Presentation Deck (PPTX & PDF).
Every shape, run, and paragraph has explicit high-contrast colors.
Font sizes are significantly increased for presentation readability.
"""
import os
import subprocess
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_presentation(pptx_path="deliverables/GreenLens_AI_Final_Deck.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # High-contrast color palette
    DARK_GREEN = RGBColor(11, 61, 44)       # #0B3D2C - Main Brand & Titles
    EMERALD = RGBColor(16, 122, 87)          # #107A57 - Accent Green
    CHARCOAL = RGBColor(26, 32, 44)          # #1A202C - Primary High-Contrast Text
    SLATE = RGBColor(71, 85, 105)            # #475569 - Secondary Muted Text
    ALERT_RED = RGBColor(185, 28, 28)        # #B91C1C - Exclusions & Warnings
    AMBER = RGBColor(180, 83, 9)             # #B45309 - Cautions / Reviews
    CARD_BG = RGBColor(241, 246, 244)        # #F1F6F4 - Clean Tinted Card Background
    CARD_BORDER = RGBColor(203, 213, 225)    # #CBD5E1 - Visible Card Border
    WHITE = RGBColor(255, 255, 255)
    PILL_BG = RGBColor(230, 244, 238)        # #E6F4EE - Soft Green Pill

    def add_header(slide, category, title):
        # Top banner / category tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.45))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = category.upper()
        p_tag.font.name = "Calibri"
        p_tag.font.size = Pt(13)
        p_tag.font.bold = True
        p_tag.font.color.rgb = EMERALD

        # Main slide title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.85))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Calibri"
        p_title.font.size = Pt(32)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_GREEN

    def add_footer(slide, slide_num, speaker):
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.7), Inches(0.35))
        tf_f = footer_box.text_frame
        tf_f.word_wrap = True
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        pf = tf_f.paragraphs[0]
        pf.text = f"GreenLens AI · Team 43   |   Slide {slide_num} of 12   |   Presenter: {speaker}"
        pf.font.name = "Calibri"
        pf.font.size = Pt(11)
        pf.font.color.rgb = SLATE

    def add_bullets(slide, bullets, left=Inches(0.8), top=Inches(1.85), width=Inches(6.4), height=Inches(4.8)):
        box = slide.shapes.add_textbox(left, top, width, height)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        for i, b in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_before = Pt(14)
            p.space_after = Pt(4)
            if ": " in b:
                lead, rest = b.split(": ", 1)
                r1 = p.add_run()
                r1.text = f"•  {lead}: "
                r1.font.name = "Calibri"
                r1.font.size = Pt(18)
                r1.font.bold = True
                r1.font.color.rgb = DARK_GREEN

                r2 = p.add_run()
                r2.text = rest
                r2.font.name = "Calibri"
                r2.font.size = Pt(16)
                r2.font.color.rgb = CHARCOAL
            else:
                r = p.add_run()
                r.text = f"•  {b}"
                r.font.name = "Calibri"
                r.font.size = Pt(16)
                r.font.color.rgb = CHARCOAL

    def create_card(slide, x, y, w, h, bg_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.2)
        tf.margin_bottom = Inches(0.2)
        return tf

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    # Background Hero Card
    hero = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.8))
    hero.fill.solid()
    hero.fill.fore_color.rgb = CARD_BG
    hero.line.color.rgb = EMERALD
    hero.line.width = Pt(2)
    htf = hero.text_frame
    htf.word_wrap = True
    htf.margin_left = Inches(0.6)
    htf.margin_top = Inches(0.5)

    p = htf.paragraphs[0]
    p.text = "MEGATHON X: SINGULARITY · PROBLEM STATEMENT 1 (LLOYDS)"
    p.font.name = "Calibri"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = EMERALD

    p = htf.add_paragraph()
    p.text = "GreenLens AI"
    p.font.name = "Calibri"
    p.font.size = Pt(46)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN
    p.space_before = Pt(8)

    p = htf.add_paragraph()
    p.text = "An Explainable Green Customer Insights Platform Grounded in Evidence"
    p.font.name = "Calibri"
    p.font.size = Pt(22)
    p.font.color.rgb = CHARCOAL
    p.space_before = Pt(4)

    p = htf.add_paragraph()
    p.text = "Team 43   |   Retail Customer & Business Intelligence Dashboards"
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = SLATE
    p.space_before = Pt(16)

    pillars = [
        "Analyzes everyday transaction patterns to identify four green product opportunities.",
        "Strictly separates machine learning predictions from deterministic carbon calculations and bank policy.",
        "Guarantees zero hallucinations through a constrained, verified explanation architecture."
    ]
    for pil in pillars:
        p = htf.add_paragraph()
        p.text = f"✓  {pil}"
        p.font.name = "Calibri"
        p.font.size = Pt(17)
        p.font.color.rgb = CHARCOAL
        p.space_before = Pt(10)

    add_footer(slide1, 1, "Speaker 1")

    # =========================================================================
    # SLIDE 2: The Problem & Opportunity
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Problem & Opportunity", "Why Green Banking Needs Strict Separation")
    add_bullets(slide2, [
        "The Banking Challenge: Banks hold rich debit spend and account data, but lack tools to pinpoint genuine green transition opportunities.",
        "The Greenwashing Risk: Unverified carbon numbers destroy regulatory and consumer trust. Impact must be auditable and conservative.",
        "Dual Stakeholder Value: Retail customers get non-intrusive green guidance; relationship managers get high-priority portfolio leads.",
        "Our Standard: Practical insights that never confuse commercial sales propensity with credit eligibility or financial approval."
    ])
    add_footer(slide2, 2, "Speaker 1")

    # Right side: 3 stakeholder cards
    roles = [
        ("Retail Customer", "Clear, personalized green options (EV, Solar, Green Home, Paperless) with full reason codes and customer memory controls.", EMERALD),
        ("Relationship Team", "Portfolio intelligence across 5,000 customers with validated priority screens and impact drill-downs.", DARK_GREEN),
        ("Compliance & Governance", "Audit-ready operational impact scenarios with documented UK government emission factors and zero LLM guesswork.", ALERT_RED)
    ]
    ry = Inches(1.85)
    for title_txt, body_txt, col in roles:
        ctf = create_card(slide2, Inches(7.5), ry, Inches(5.0), Inches(1.4))
        p = ctf.paragraphs[0]
        p.text = title_txt
        p.font.name = "Calibri"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = ctf.add_paragraph()
        p2.text = body_txt
        p2.font.name = "Calibri"
        p2.font.size = Pt(13)
        p2.font.color.rgb = CHARCOAL
        p2.space_before = Pt(4)
        ry += Inches(1.6)

    # =========================================================================
    # SLIDE 3: The Core Rule (Four Pillars)
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "The Brief's Core Rule", "The Four-Way Division of Responsibility")
    add_bullets(slide3, [
        "Machine Learning Predicts: Estimates simulated customer take-up propensity from spending trends and circumstances.",
        "Carbon Engine Calculates: Computes operational emission impacts using verified 2025 UK government factors.",
        "Product Rules Decide Eligibility: Enforces explicit bank policies (e.g. existing EV exclusions) independently of ML scores.",
        "The LLM Only Explains: Acts as a safe sentence selector from approved templates; never predicts, calculates, or approves."
    ])
    add_footer(slide3, 3, "Speaker 1")

    # Right side: 4 clear pillars
    pillars_data = [
        ("1. ML Models", "Predicts simulated take-up propensity", DARK_GREEN),
        ("2. Carbon Engine", "Computes documented annual kgCO2e", EMERALD),
        ("3. Product Rules", "Decides eligibility & explicit exclusions", ALERT_RED),
        ("4. Guarded LLM", "Only selects approved factual sentences", SLATE)
    ]
    ry = Inches(1.85)
    for p_title, p_desc, col in pillars_data:
        ctf = create_card(slide3, Inches(7.5), ry, Inches(5.0), Inches(1.1))
        p = ctf.paragraphs[0]
        p.text = p_title
        p.font.name = "Calibri"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = ctf.add_paragraph()
        p2.text = f"→ {p_desc}"
        p2.font.name = "Calibri"
        p2.font.size = Pt(13)
        p2.font.color.rgb = CHARCOAL
        p2.space_before = Pt(3)
        ry += Inches(1.22)

    # =========================================================================
    # SLIDE 4: Technical Architecture
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Technical Architecture", "A Modular, Read-Only Production Pipeline")
    add_bullets(slide4, [
        "Immutable Snapshot: Relational customer data and transactions import into SQLite with SHA-256 source verification.",
        "Batch Inference: Four trained scikit-learn pipelines load once at startup and score 5,000 customers in seconds.",
        "Deterministic Carbon Engine: Verified UK conversion factors compute operational scenarios without database mutation.",
        "Guarded Delivery: Typed FastAPI contracts serve twin React dashboards with 100% offline deterministic fallbacks."
    ])
    add_footer(slide4, 4, "Speaker 2")

    # Right side: 5-step Architecture Card
    ctf = create_card(slide4, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "END-TO-END PIPELINE"
    p.font.name = "Calibri"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    arch_steps = [
        ("1. Synthetic CSVs", "5,000 customers, 368k transactions"),
        ("2. Customer 360", "28 pre-cutoff behavioral features"),
        ("3. ML Inference", "4 propensity models + TF-IDF classifier"),
        ("4. Rules & Carbon", "2025 DESNZ factors + exclusion screens"),
        ("5. Guarded LLM", "Safe sentence selection (fails closed)"),
        ("6. FastAPI & React", "Customer Insights + Business Intelligence")
    ]
    for s_name, s_detail in arch_steps:
        p = ctf.add_paragraph()
        p.text = f"\n{s_name}"
        p.font.name = "Calibri"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = EMERALD
        p2 = ctf.add_paragraph()
        p2.text = s_detail
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 5: Data & Partition Hygiene
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Data & Partition Hygiene", "Synthetic UK Cohort with Clean Splits")
    add_bullets(slide5, [
        "Synthetic UK Cohort: 5,000 customers and 368,323 transactions with realistic UK spending distributions (no real PII).",
        "Disjoint Partitioning: 3,500 train (70%) / 750 validation (15%) / 750 test (15%), split strictly by customer ID with 0% overlap.",
        "Pre-Cutoff Features: All 28 Customer 360 features derive strictly from activity prior to the synthetic prediction cutoff date.",
        "Zero Leakage: Numeric missing-value imputers use training medians only, verified by automated audit scripts."
    ])
    add_footer(slide5, 5, "Speaker 2")

    # Right side: Data Stats Card
    ctf = create_card(slide5, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "DATASET SPECIFICATIONS"
    p.font.name = "Calibri"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    data_stats = [
        ("Total Cohort Size", "5,000 synthetic UK customers"),
        ("Transaction Records", "368,323 category-mapped rows"),
        ("Training Partition", "3,500 customers (70%)"),
        ("Validation Partition", "750 customers (15%)"),
        ("Held-Out Test Partition", "750 customers (15%)"),
        ("Customer Overlap", "0% (completely disjoint IDs)"),
        ("Feature Leakage", "Zero (all pre-cutoff features)")
    ]
    for k, v in data_stats:
        p = ctf.add_paragraph()
        p.text = f"{k}:"
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = DARK_GREEN
        p.space_before = Pt(8)
        p2 = ctf.add_paragraph()
        p2.text = v
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 6: Models & Evaluation
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Machine Learning Evaluation", "Propensity Results & The Unseen-Merchant Check")
    add_bullets(slide6, [
        "Four Models Beat Baselines (Test AUC): GP01 EV 0.751, GP02 Home 0.815, GP03 Solar 0.901, GP04 Paperless 0.866.",
        "Priority Thresholds (Test F1): EV 0.389 (thr 0.24), Home 0.327 (thr 0.10), Solar 0.353 (thr 0.23), Paperless 0.577 (thr 0.28).",
        "Transaction Categorization: TF-IDF text model achieves 0.980 test macro F1 on customer splits vs 0.918 for rule baseline.",
        "Honest Unseen-Merchant Check: On 7 held-out merchants, TF-IDF drops to 0.095 while the rule baseline retains 0.921."
    ])
    add_footer(slide6, 6, "Speaker 3")

    # Right side: 2 Result Cards
    ctf1 = create_card(slide6, Inches(7.5), Inches(1.85), Inches(5.0), Inches(2.2))
    p = ctf1.paragraphs[0]
    p.text = "PROPENSITY TEST EVALUATION"
    p.font.name = "Calibri"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    auc_lines = [
        "GP01 EV Finance:       AUC 0.751  |  F1: 0.389",
        "GP02 Green Home Loan:  AUC 0.815  |  F1: 0.327",
        "GP03 Solar Finance:    AUC 0.901  |  F1: 0.353",
        "GP04 Paperless:        AUC 0.866  |  F1: 0.577"
    ]
    for l in auc_lines:
        p = ctf1.add_paragraph()
        p.text = l
        p.font.name = "Calibri"
        p.font.size = Pt(12)
        p.font.color.rgb = CHARCOAL
        p.space_before = Pt(4)

    ctf2 = create_card(slide6, Inches(7.5), Inches(4.25), Inches(5.0), Inches(2.3))
    p = ctf2.paragraphs[0]
    p.text = "HONEST UNSEEN-MERCHANT DIAGNOSTIC"
    p.font.name = "Calibri"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ALERT_RED

    p = ctf2.add_paragraph()
    p.text = "Customer Split:  TF-IDF F1 = 0.980  |  Rule = 0.918"
    p.font.name = "Calibri"
    p.font.size = Pt(13)
    p.font.color.rgb = CHARCOAL
    p.space_before = Pt(6)

    p = ctf2.add_paragraph()
    p.text = "Merchant Holdout: TF-IDF F1 = 0.095  |  Rule = 0.921"
    p.font.name = "Calibri"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ALERT_RED
    p.space_before = Pt(4)

    p = ctf2.add_paragraph()
    p.text = "Finding: Classifier memorized merchant names. Production requires keyword/regex rules for new merchants."
    p.font.name = "Calibri"
    p.font.size = Pt(11)
    p.font.color.rgb = CHARCOAL
    p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 7: Sustainability Engine
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Sustainability Methodology", "Deterministic Scenarios & Honest Boundary Limits")
    add_bullets(slide7, [
        "Verified UK Factors: Official 2025 DESNZ factors (petrol 2.069 kg/L, diesel 2.571 kg/L, UK electricity 0.177 kg/kWh).",
        "Operational Scenarios: EV models petrol emissions vs grid charging; Green Home models a 10% gas efficiency package.",
        "Solar Regional Boundary: Models a 4 kWp London reference system (919 kWh/kWp/year yield); all other regions return UNAVAILABLE.",
        "Paperless Boundary: Shows 48 pages/year avoided; CO2 is marked UNAVAILABLE because no verified lifecycle envelope factor exists."
    ])
    add_footer(slide7, 7, "Speaker 4")

    # Right side: Worked Example Card C002056
    ctf = create_card(slide7, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "WORKED EXAMPLE: CUSTOMER C002056"
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    lines_c = [
        ("Customer Circumstances", "Petrol car, 24,033 annual miles, £289/mo fuel"),
        ("Baseline Transport Emissions", "5,618 kgCO2e / year (petrol combustion)"),
        ("EV Scenario Charging Emissions", "1,234 kgCO2e / year (UK grid electricity)"),
        ("Net Annual Avoided Impact", "4,384 kgCO2e / year (ESTIMATED)")
    ]
    for k, v in lines_c:
        p = ctf.add_paragraph()
        p.text = f"{k}:"
        p.font.name = "Calibri"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = DARK_GREEN
        p.space_before = Pt(6)
        p2 = ctf.add_paragraph()
        p2.text = v
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = EMERALD if "Avoided" in k else CHARCOAL

    p = ctf.add_paragraph()
    p.text = "\nTRANSPARENT BOUNDARIES"
    p.font.name = "Calibri"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ALERT_RED

    p = ctf.add_paragraph()
    p.text = "• Solar outside London: UNAVAILABLE (no local yield data)\n• Paperless CO2: UNAVAILABLE (no verified envelope factor)"
    p.font.name = "Calibri"
    p.font.size = Pt(11)
    p.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 8: Explainability & Trust
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Explainability & Trust", "Transparent Evidence, Reason Codes & Exclusions")
    add_bullets(slide8, [
        "Auditable Reason Codes: Every opportunity surfaces plain reasons (e.g. HIGH_FUEL_SPEND, EXISTING_PETROL_VEHICLE).",
        "Evidence Drawer: Customers and advisors inspect exact inputs (fuel spend £288.70, mileage 24,033) and conversion source URLs.",
        "Qualitative Reliability Tiers: Tiers (High / Medium / Low / Unavailable) assess feature completeness and training familiarity.",
        "Dedicated Exclusion Section: Ineligible customers appear in a separate 'Not recommended' section with clear reasons."
    ])
    add_footer(slide8, 8, "Speaker 3")

    # Right side: Status Legend Card
    ctf = create_card(slide8, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "STATUS & GOVERNANCE LEGEND"
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    statuses = [
        ("[POTENTIAL_OPPORTUNITY]", "Rules satisfied, above validation priority threshold.", EMERALD),
        ("[EXCLUDED]", "Disqualified by bank policy (e.g. already owns EV).", ALERT_RED),
        ("[NEEDS_REVIEW]", "Conflicting or incomplete customer facts detected.", AMBER),
        ("[INSUFFICIENT_DATA]", "Key physical inputs absent; impact marked UNAVAILABLE.", SLATE)
    ]
    for tag_name, tag_desc, col in statuses:
        p = ctf.add_paragraph()
        p.text = f"\n{tag_name}"
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = ctf.add_paragraph()
        p2.text = tag_desc
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 9: Live Application Demonstration
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Live Application Demonstration", "Interactive Customer & Business Workspaces")
    add_bullets(slide9, [
        "Step 1: Retail Customer View (C002056): Shows Customer 360 profile, EV Finance card (58% propensity), and savings.",
        "Step 2: Eligibility Separation (C000042): High EV propensity is suppressed to EXCLUDED by rule EXISTING_EV_NO_REPLACEMENT.",
        "Step 3: What-If Scenario Explorer (C000018): Toggle EV or Paperless chips to re-run models dynamically without altering records.",
        "Step 4: Business Dashboard: Portfolio view across 5,000 customers with drill-down from segment to evidence and actions."
    ])
    add_footer(slide9, 9, "Speaker 5")

    # Right side: 4 screenshot placeholder cards
    demo_boxes = [
        ("Demo Step 1", "[SCREENSHOT: Customer Card C002056]"),
        ("Demo Step 2", "[SCREENSHOT: EV Exclusion Badge C000042]"),
        ("Demo Step 3", "[SCREENSHOT: What-If Scenario Chips C000018]"),
        ("Demo Step 4", "[SCREENSHOT: Business Intelligence Table]")
    ]
    ry = Inches(1.85)
    for s_step, s_shot in demo_boxes:
        ctf = create_card(slide9, Inches(7.5), ry, Inches(5.0), Inches(1.1))
        p = ctf.paragraphs[0]
        p.text = s_step
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = DARK_GREEN
        p2 = ctf.add_paragraph()
        p2.text = s_shot
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = SLATE
        p2.space_before = Pt(3)
        ry += Inches(1.22)

    # =========================================================================
    # SLIDE 10: Responsible AI & Governance
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "Responsible AI & Governance", "Guarded LLM Explanations & Ethics by Design")
    add_bullets(slide10, [
        "Zero Free-Form Hallucinations: LLM is a constrained style selector choosing between pre-approved factual sentences.",
        "Validated Guardrails: 28/28 offline test cases pass (including 4/4 missing/conflicting data checks); fails closed to templates.",
        "Privacy Protection: Customer IDs and personal markers are stripped before sending any external API payload.",
        "Customer Autonomy: Interactive memory controls allow users to snooze ('Remind me later'), explore, or permanently dismiss."
    ])
    add_footer(slide10, 10, "Speaker 4")

    # Right side: Test Scorecard Card
    ctf = create_card(slide10, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "GUARDRAIL & GOVERNANCE SCORECARD"
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    checks = [
        ("Groundedness Guardrails", "28 / 28 cases passed"),
        ("Factual Accuracy Guardrails", "28 / 28 cases passed"),
        ("Completeness Checks", "28 / 28 cases passed"),
        ("Numerical Consistency", "28 / 28 cases passed"),
        ("Missing / Conflicting Data", "4 / 4 edge checks passed"),
        ("Automated Test Suite", "57 automated tests passed (51 backend + 6 frontend)")
    ]
    for c_name, c_res in checks:
        p = ctf.add_paragraph()
        p.text = f"✓ {c_name}:"
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = DARK_GREEN
        p.space_before = Pt(8)
        p2 = ctf.add_paragraph()
        p2.text = c_res
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = EMERALD

    # =========================================================================
    # SLIDE 11: Honest Limitations & Roadmap
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    add_header(slide11, "Limitations & Roadmap", "Honest Limitations & Next Steps")
    add_bullets(slide11, [
        "Synthetic Data Boundary: Metrics reflect the synthetic generator; testing against real banking data is essential before deployment.",
        "Merchant Generalization: Unseen merchants require regex dictionaries and fuzzy category lookups alongside ML models.",
        "Solar Geographic Scope: Solar models London only; expanding nationwide requires localized irradiance and EPC roof data.",
        "Future Roadmap: Integrate PCAF-aligned financed emissions reporting and test live LLM provider responses under banking network SLAs."
    ])
    add_footer(slide11, 11, "Speaker 2")

    # Right side: Limitations vs Roadmap Card
    ctf = create_card(slide11, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "CURRENT LIMITS & FUTURE ROADMAP"
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    road_items = [
        ("Current Limit: Synthetic Labels", "Performance reflects simulation; real cohort testing is required.", ALERT_RED),
        ("Current Limit: Merchant Holdout", "Model memorized synthetic merchant tokens; needs regex fallback.", ALERT_RED),
        ("Next Step: EPC & Solar Ingestion", "Ingest UK Energy Performance Certificates for roof orientation.", EMERALD),
        ("Next Step: PCAF Accounting", "Implement financed emissions attribution metrics for banking.", EMERALD)
    ]
    for r_title, r_desc, col in road_items:
        p = ctf.add_paragraph()
        p.text = f"\n{r_title}"
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = ctf.add_paragraph()
        p2.text = r_desc
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 12: Conclusion & Q&A
    # =========================================================================
    slide12 = prs.slides.add_slide(blank_layout)
    add_header(slide12, "Conclusion", "GreenLens AI: Actionable, Transparent Green Banking")
    add_bullets(slide12, [
        "Meets the Brief: Full four-product platform with dual customer and relationship manager dashboards.",
        "Principled Separation: Machine learning predicts take-up, deterministic rules compute carbon, and AI explains facts.",
        "Audit-Ready Governance: Honest about limits, zero greenwashing, and fully reproducible across 57 automated tests.",
        "Thank You: Team 43 is ready to take your questions."
    ])
    add_footer(slide12, 12, "Speaker 1")

    # Right side: Closing Summary Card
    ctf = create_card(slide12, Inches(7.5), Inches(1.85), Inches(5.0), Inches(4.7))
    p = ctf.paragraphs[0]
    p.text = "KEY TAKEAWAY"
    p.font.name = "Calibri"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    p = ctf.add_paragraph()
    p.text = "GreenLens AI proves that banks can deliver intelligent, personalized green recommendations while upholding the highest standards of financial governance."
    p.font.name = "Calibri"
    p.font.size = Pt(14)
    p.font.color.rgb = CHARCOAL
    p.space_before = Pt(10)

    p = ctf.add_paragraph()
    p.text = "\n• 4 Green Products Implemented\n• 5,000 Customers Analyzed\n• 100% Deterministic Carbon Engine\n• Zero LLM Hallucinations\n• 57 Automated Tests Passing"
    p.font.name = "Calibri"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = EMERALD

    p = ctf.add_paragraph()
    p.text = "\nReady for Questions & Demonstration"
    p.font.name = "Calibri"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = DARK_GREEN

    os.makedirs(os.path.dirname(pptx_path), exist_ok=True)
    prs.save(pptx_path)
    print(f"High-contrast PPTX successfully saved to {pptx_path}")

if __name__ == "__main__":
    build_presentation()
