from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import joblib
import re
import os

# ─────────────────────────────────────────
# GLOBALS
# ─────────────────────────────────────────
pipeline = None

# ─────────────────────────────────────────
# STARTUP — load model once
# ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    if not os.path.exists("model/model.pkl"):
        raise RuntimeError("model/model.pkl not found. Run training/train.py first.")
    pipeline = joblib.load("model/model.pkl")
    print("Model loaded successfully.")
    yield

app = FastAPI(
    title="Fake Job Detector API",
    description="Multi-layer fake job detection",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────
class JobInput(BaseModel):
    title:        str = ""
    company:      str = ""
    location:     str = ""
    salary:       str = ""
    description:  str = ""
    requirements: str = ""
    benefits:     str = ""
    email:        Optional[str] = ""   # new optional field for domain check

class PredictionOutput(BaseModel):
    prediction:   str
    confidence:   float
    trust_score:  int
    risk_level:   str
    flags:        list
    label:        str
    message:      str

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ─────────────────────────────────────────
# LAYER 1 — RULE ENGINE
# Catches logical contradictions that text
# patterns alone cannot detect
# ─────────────────────────────────────────
def run_rule_engine(job: JobInput) -> dict:
    flags = []
    risk_score = 0

    desc  = (job.description  + " " + job.requirements + " " + job.benefits).lower()
    title = job.title.lower()
    sal   = job.salary.lower()
    comp  = job.company.lower()

    # Rule 1 — High salary + no requirements (strong contradiction)
    high_salary_words = [
        "5000/week", "5,000/week", "10000/week", "10,000/week",
        "$5000", "$10000", "daily pay", "500/day", "$500 daily"
    ]
    no_exp_words = [
        "no experience", "no qualification", "no degree",
        "no background", "anyone can apply", "no skills needed"
    ]
    is_high_salary = any(w in sal for w in high_salary_words)
    is_no_exp      = any(w in desc for w in no_exp_words)
    if is_high_salary and is_no_exp:
        flags.append("High salary claimed with zero requirements")
        risk_score += 40

    # Rule 2 — Urgency language + no interview mentioned
    urgency_words = [
        "immediate start", "urgently hiring", "apply now",
        "limited spots", "hiring immediately", "start today",
        "positions filling fast"
    ]
    no_interview_words = [
        "no interview", "skip interview", "direct hire",
        "no screening"
    ]
    has_urgency      = any(w in desc for w in urgency_words)
    has_no_interview = any(w in desc for w in no_interview_words)
    if has_urgency and has_no_interview:
        flags.append("Urgency language combined with no interview process")
        risk_score += 35

    # Rule 3 — Fee or payment request (near-certain scam)
    fee_words = [
        "pay a fee", "training fee", "registration fee",
        "starter kit", "purchase equipment", "send money",
        "upfront payment", "processing fee"
    ]
    if any(w in desc for w in fee_words):
        flags.append("Upfront fee or payment requested")
        risk_score += 65

    # Rule 4 — Suspicious contact or payment method
    suspicious_contact = [
        "whatsapp", "telegram", "paypal", "western union",
        "moneygram", "zelle", "cash app", "wire transfer",
        "bitcoin", "cryptocurrency"
    ]
    hits = [w for w in suspicious_contact if w in desc]
    if hits:
        flags.append(f"Suspicious contact/payment method: {', '.join(hits)}")
        risk_score += 45

    # Rule 5 — Empty or suspicious company name
    if not comp or len(comp) < 3:
        flags.append("Company name missing or too short")
        risk_score += 20
    elif any(w in comp for w in ["solutions inc", "global corp", "intl ltd",
                                   "opportunities llc", "worldwide"]):
        flags.append("Generic or suspicious company name pattern")
        risk_score += 15

    # Rule 6 — Work from home + unrealistic income combo
    wfh = any(w in desc for w in ["work from home", "work at home", "remote work"])
    unrealistic_income = any(w in desc for w in [
        "earn thousands", "unlimited income", "unlimited earning",
        "be your own boss", "financial freedom"
    ])
    if wfh and unrealistic_income:
        flags.append("Work-from-home with unrealistic income promises")
        risk_score += 30

    # Rule 7 — All caps or excessive punctuation (spam signal)
    exclamation_count = job.description.count("!")
    if exclamation_count >= 3:
        flags.append(f"Excessive punctuation ({exclamation_count} exclamation marks)")
        risk_score += 10

    # Rule 8 — No requirements at all for a technical role
    tech_titles = ["engineer", "developer", "analyst", "manager", "director"]
    is_tech_role = any(w in title for w in tech_titles)
    has_requirements = len(job.requirements.strip()) > 30
    if is_tech_role and not has_requirements:
        flags.append("Technical role listed with no requirements")
        risk_score += 20

    return {
        "flags": flags,
        "rule_risk": min(risk_score, 100)
    }

# ─────────────────────────────────────────
# LAYER 2 — TRUST SCORE SYSTEM
# Combines ML confidence + rule violations
# into one final 0-100 trust score
# ─────────────────────────────────────────
def calculate_trust_score(
    ml_confidence: float,
    is_fake_ml: bool,
    rule_risk: int
) -> dict:

    # Start fully trusted
    score = 100.0

    # ML model contributes up to 50 points
    if is_fake_ml:
        score -= ml_confidence * 50
    else:
        score -= (1 - ml_confidence) * 50

    # Rule violations subtract directly (scaled)
    score -= rule_risk * 0.5

    # Clamp between 0 and 100
    score = max(0.0, min(100.0, score))
    score = round(score)

    if score >= 70:
        risk_level = "low"
        label      = "Likely real"
        message    = "This job posting appears legitimate based on all checks."
    elif score >= 40:
        risk_level = "medium"
        label      = "Suspicious"
        message    = "Some warning signals detected. Verify independently before applying."
    else:
        risk_level = "high"
        label      = "High risk"
        message    = "Multiple fraud signals detected. Do not share personal information."

    return {
        "trust_score": score,
        "risk_level":  risk_level,
        "label":       label,
        "message":     message
    }

# ─────────────────────────────────────────
# LAYER 3 — DOMAIN & EMAIL CHECK
# Catches domain spoofing e.g.
# hr@google-careers.com != google.com
# ─────────────────────────────────────────

TRUSTED_DOMAINS = {
    "google":    "google.com",
    "microsoft": "microsoft.com",
    "amazon":    "amazon.com",
    "apple":     "apple.com",
    "meta":      "meta.com",
    "facebook":  "meta.com",
    "stripe":    "stripe.com",
    "netflix":   "netflix.com",
    "twitter":   "x.com",
    "linkedin":  "linkedin.com",
    "uber":      "uber.com",
    "airbnb":    "airbnb.com",
    "spotify":   "spotify.com",
    "adobe":     "adobe.com",
    "salesforce":"salesforce.com",
    "oracle":    "oracle.com",
    "ibm":       "ibm.com",
    "intel":     "intel.com",
}

FREE_PROVIDERS = [
    "gmail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "live.com", "aol.com",
    "protonmail.com", "icloud.com"
]

def check_domain(email: str, company: str) -> dict:
    if not email or "@" not in email:
        return {"domain_risk": 0, "domain_flag": None}

    domain       = email.split("@")[-1].strip().lower()
    company_lower = company.lower()

    # Check against known companies
    for keyword, official in TRUSTED_DOMAINS.items():
        if keyword in company_lower:
            if domain != official:
                return {
                    "domain_risk": 80,
                    "domain_flag": (
                        f"Email domain '{domain}' does not match "
                        f"official domain '{official}' for {company}"
                    )
                }
            else:
                # Domain matches — trust boost
                return {"domain_risk": -15, "domain_flag": None}

    # Free email for a corporate role
    if domain in FREE_PROVIDERS:
        return {
            "domain_risk": 30,
            "domain_flag": f"Corporate job using free email provider ({domain})"
        }

    return {"domain_risk": 0, "domain_flag": None}

# ─────────────────────────────────────────
# LAYER 4 — SMART PATTERN DETECTION
# Catches sophisticated fakes using
# combination patterns not single keywords
# ─────────────────────────────────────────
def run_smart_patterns(job: JobInput) -> dict:
    flags  = []
    risk   = 0
    full   = (job.title + " " + job.description + " " +
              job.requirements + " " + job.benefits).lower()

    # Pattern A — Vague description length
    # Real jobs have detailed descriptions
    word_count = len(job.description.split())
    if word_count < 30:
        flags.append("Job description is unusually short")
        risk += 15
    elif word_count > 20 and not job.requirements.strip():
        flags.append("Long description but no requirements listed")
        risk += 20

    # Pattern B — Copy-paste spam indicators
    spam_phrases = [
        "click here to apply", "limited time offer",
        "this is not a scam", "100% legitimate",
        "guaranteed income", "risk free"
    ]
    spam_hits = [p for p in spam_phrases if p in full]
    if spam_hits:
        flags.append(f"Spam phrases detected: {', '.join(spam_hits)}")
        risk += 35

    # Pattern C — Real job positive signals (reduces risk)
    real_signals = [
        "bachelor", "master", "degree", "years of experience",
        "401k", "health insurance", "dental", "equity",
        "pto", "vacation days", "annual bonus"
    ]
    real_hits = sum(1 for s in real_signals if s in full)
    if real_hits >= 3:
        # Strong real job signals — reduce overall risk
        risk -= 20
        flags.append(f"Strong legitimate signals found ({real_hits} professional markers)")

    # Pattern D — Salary range check
    # Fake jobs often have round unrealistic numbers
    salary_text = job.salary.lower().replace(",", "")
    if re.search(r"\$\d{4,5}/week", salary_text):
        flags.append("Weekly salary format uncommon in legitimate postings")
        risk += 20

    return {"smart_flags": flags, "smart_risk": max(0, risk)}

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status":  "running",
        "version": "2.0.0",
        "model":   "loaded" if pipeline else "not loaded",
        "layers":  ["ml_model", "rule_engine", "trust_score", "domain_check", "smart_patterns"]
    }

@app.get("/health")
def health():
    return {
        "status":       "ok",
        "model_loaded": pipeline is not None
    }

@app.post("/predict", response_model=PredictionOutput)
def predict(job: JobInput):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not job.title.strip() and not job.description.strip():
        raise HTTPException(status_code=400, detail="Title or description required")

    # ── Layer 1: Rule engine ──────────────
    rule_result   = run_rule_engine(job)
    rule_flags    = rule_result["flags"]
    rule_risk     = rule_result["rule_risk"]

    # ── Layer 3: Domain check ─────────────
    domain_result = check_domain(job.email or "", job.company)
    domain_risk   = domain_result["domain_risk"]
    domain_flag   = domain_result["domain_flag"]
    if domain_flag:
        rule_flags.append(domain_flag)

    # ── Layer 4: Smart patterns ───────────
    smart_result  = run_smart_patterns(job)
    smart_flags   = smart_result["smart_flags"]
    smart_risk    = smart_result["smart_risk"]

    # ── ML model (TF-IDF + LR) ───────────
    combined = clean_text(
        f"{job.title} {job.company} {job.location} {job.salary} "
        f"{job.description} {job.requirements} {job.benefits}"
    )
    ml_pred  = pipeline.predict([combined])[0]
    ml_proba = pipeline.predict_proba([combined])[0]
    is_fake  = bool(ml_pred == 1)
    ml_conf  = float(ml_proba[1] if is_fake else ml_proba[0])

    # ── Layer 2: Trust score ──────────────
    # Combine all risk signals
    total_rule_risk = min(100, rule_risk + smart_risk + max(0, domain_risk))
    trust_result    = calculate_trust_score(ml_conf, is_fake, total_rule_risk)

    # ── Final prediction ──────────────────
    # Rule engine can override ML if very high risk
    if total_rule_risk >= 60:
        final_prediction = "fake"
    elif total_rule_risk <= 0 and not is_fake:
        final_prediction = "real"
    else:
        final_prediction = "fake" if is_fake else "real"

    all_flags = rule_flags + smart_flags

    return PredictionOutput(
        prediction  = final_prediction,
        confidence  = round(ml_conf, 4),
        trust_score = trust_result["trust_score"],
        risk_level  = trust_result["risk_level"],
        flags       = all_flags,
        label       = trust_result["label"],
        message     = trust_result["message"]
    )