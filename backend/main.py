from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import joblib
import re
import os
import numpy as np
import pandas as pd
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from scipy.sparse import hstack, csr_matrix

# Layer 5 — External verification
from verify import run_external_verification


# GLOBALS

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model", "model.pkl")

model_bundle = None  # now a dict: {tfidf, clf, numeric_columns}

# ── Suspicious keywords (must match train.py) ─────────────────────────────────
SUSPICIOUS_KW = [
    'no experience', 'earn from home', 'weekly pay', 'gift card',
    'wire transfer', 'no interview', 'immediate start', 'whatsapp',
    'telegram', 'bank account', 'ssn', 'social security',
    'money transfer', 'work from home', 'be your own boss',
    'unlimited earning', 'passive income'
]

TEXT_COLUMNS = [
    'title', 'company_profile', 'description',
    'requirements', 'benefits', 'location',
    'employment_type', 'required_experience',
    'required_education', 'industry', 'function'
]

# STARTUP — load model once

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_bundle
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"{MODEL_PATH} not found. Run training/train.py first.")
    model_bundle = joblib.load(MODEL_PATH)
    # Support both old pipeline and new bundle format
    if not isinstance(model_bundle, dict):
        print("Warning: old model format detected. Retrain with updated train.py for best results.")
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


# SCHEMAS

class JobInput(BaseModel):
    title:        str = ""
    company:      str = ""
    location:     str = ""
    salary:       str = ""
    description:  str = ""
    requirements: str = ""
    benefits:     str = ""
    telecommuting:     int = 0
    has_company_logo:  int = 1
    has_questions:     int = 0
    email:        Optional[str] = ""
    website:      Optional[str] = ""   # NEW — company website for Layer 5

class PredictionOutput(BaseModel):
    prediction:   str
    confidence:   float
    trust_score:  int
    risk_level:   str
    flags:        list
    label:        str
    message:      str
    verification: Optional[Dict[str, Any]] = None  # NEW — Layer 5 results

class URLInput(BaseModel):
    url: str

class URLScrapeResult(BaseModel):
    success:      bool
    url:          str
    title:        str
    company:      str
    description:  str
    requirements: str
    benefits:     str
    summary:      str
    prediction:   str
    confidence:   float
    trust_score:  int
    risk_level:   str
    flags:        list
    label:        str
    message:      str
    error:        str = ""


# HELPERS

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_numeric_features(job: JobInput) -> pd.DataFrame:
    """
    Mirror of engineer_features() in train.py.
    Builds the same numeric feature vector from a JobInput.
    """
    desc_full = (job.description or "") + " " + (job.title or "")

    def count_suspicious(text):
        text = text.lower()
        return sum(1 for kw in SUSPICIOUS_KW if kw in text)

    row = {
        # Binary columns
        "telecommuting":         float(job.telecommuting),
        "has_company_logo":      float(job.has_company_logo),
        "has_questions":         float(job.has_questions),
        # Missingness flags
        "missing_salary":        float(not job.salary.strip()),
        "missing_company":       float(not job.company.strip()),
        "missing_requirements":  float(not job.requirements.strip()),
        "missing_benefits":      float(not job.benefits.strip()),
        "missing_dept":          1.0,   # dept not in API input → always missing
        # Normalised text lengths (divide by rough max from training)
        "desc_len":              min(len(job.description) / 10000, 1.0),
        "req_len":               min(len(job.requirements) / 5000,  1.0),
        "company_len":           min(len(job.company)      / 3000,  1.0),
        # Suspicious keyword count
        "suspicious_kw_count":   float(count_suspicious(desc_full)),
    }
    return pd.DataFrame([row])


def ml_predict(job: JobInput):
    """
    Runs ML prediction supporting both:
      - new bundle format: dict with tfidf + clf + numeric_columns
      - old pipeline format: sklearn Pipeline (fallback)
    Returns (is_fake: bool, confidence: float)
    """
    global model_bundle

    combined_text = clean_text(
        f"{job.title} {job.company} {job.location} {job.salary} "
        f"{job.description} {job.requirements} {job.benefits}"
    )

    # ── New bundle format (updated train.py) ──────────────────────────────────
    if isinstance(model_bundle, dict):
        tfidf   = model_bundle["tfidf"]
        clf     = model_bundle["clf"]
        num_cols = model_bundle["numeric_columns"]

        X_text    = tfidf.transform([combined_text])
        numeric_df = build_numeric_features(job)

        # Align columns to training order
        for col in num_cols:
            if col not in numeric_df.columns:
                numeric_df[col] = 0.0
        numeric_df = numeric_df[num_cols]

        X_numeric  = csr_matrix(numeric_df.values.astype(float))
        X_combined = hstack([X_text, X_numeric])

        pred  = clf.predict(X_combined)[0]
        proba = clf.predict_proba(X_combined)[0]

    # ── Old pipeline format (fallback) ────────────────────────────────────────
    else:
        pipeline = model_bundle
        pred  = pipeline.predict([combined_text])[0]
        proba = pipeline.predict_proba([combined_text])[0]

    is_fake = bool(pred == 1)
    conf    = float(proba[1] if is_fake else proba[0])
    return is_fake, conf


# LAYER 1 — RULE ENGINE

def run_rule_engine(job: JobInput) -> dict:
    flags = []
    risk_score = 0

    desc  = (job.description + " " + job.requirements + " " + job.benefits).lower()
    title = job.title.lower()
    sal   = job.salary.lower()
    comp  = job.company.lower()

    high_salary_words = [
        "5000/week", "5,000/week", "10000/week", "10,000/week",
        "$5000", "$10000", "daily pay", "500/day", "$500 daily"
    ]
    no_exp_words = [
        "no experience", "no qualification", "no degree",
        "no background", "anyone can apply", "no skills needed"
    ]
    if any(w in sal for w in high_salary_words) and any(w in desc for w in no_exp_words):
        flags.append("High salary claimed with zero requirements")
        risk_score += 40

    urgency_words    = ["immediate start", "urgently hiring", "apply now",
                        "limited spots", "hiring immediately", "start today",
                        "positions filling fast"]
    no_interview_words = ["no interview", "skip interview", "direct hire", "no screening"]
    if any(w in desc for w in urgency_words) and any(w in desc for w in no_interview_words):
        flags.append("Urgency language combined with no interview process")
        risk_score += 35

    fee_words = ["pay a fee", "training fee", "registration fee", "starter kit",
                 "purchase equipment", "send money", "upfront payment", "processing fee"]
    if any(w in desc for w in fee_words):
        flags.append("Upfront fee or payment requested")
        risk_score += 65

    suspicious_contact = ["whatsapp", "telegram", "paypal", "western union",
                          "moneygram", "zelle", "cash app", "wire transfer",
                          "bitcoin", "cryptocurrency"]
    hits = [w for w in suspicious_contact if w in desc]
    if hits:
        flags.append(f"Suspicious contact/payment method: {', '.join(hits)}")
        risk_score += 45

    if not comp or len(comp) < 3:
        flags.append("Company name missing or too short")
        risk_score += 20
    elif any(w in comp for w in ["solutions inc", "global corp", "intl ltd",
                                  "opportunities llc", "worldwide"]):
        flags.append("Generic or suspicious company name pattern")
        risk_score += 15

    wfh = any(w in desc for w in ["work from home", "work at home", "remote work"])
    unrealistic = any(w in desc for w in ["earn thousands", "unlimited income",
                                           "unlimited earning", "be your own boss",
                                           "financial freedom"])
    if wfh and unrealistic:
        flags.append("Work-from-home with unrealistic income promises")
        risk_score += 30

    if job.description.count("!") >= 3:
        flags.append(f"Excessive punctuation ({job.description.count('!')} exclamation marks)")
        risk_score += 10

    tech_titles = ["engineer", "developer", "analyst", "manager", "director"]
    if any(w in title for w in tech_titles) and len(job.requirements.strip()) < 30:
        flags.append("Technical role listed with no requirements")
        risk_score += 20

    # ── New: flag missing logo ────────────────────────────────────────────────
    if job.has_company_logo == 0:
        flags.append("No company logo provided (strong fraud signal)")
        risk_score += 25

    return {"flags": flags, "rule_risk": min(risk_score, 100)}


# LAYER 2 — TRUST SCORE

def calculate_trust_score(ml_confidence, is_fake_ml, rule_risk):
    score = 100.0
    if is_fake_ml:
        score -= ml_confidence * 50
    else:
        score -= (1 - ml_confidence) * 50
    score -= rule_risk * 0.5
    score = round(max(0.0, min(100.0, score)))

    if score >= 70:
        return {"trust_score": score, "risk_level": "low",
                "label": "Likely real",
                "message": "This job posting appears legitimate based on all checks."}
    elif score >= 40:
        return {"trust_score": score, "risk_level": "medium",
                "label": "Suspicious",
                "message": "Some warning signals detected. Verify independently before applying."}
    else:
        return {"trust_score": score, "risk_level": "high",
                "label": "High risk",
                "message": "Multiple fraud signals detected. Do not share personal information."}


# LAYER 3 — DOMAIN CHECK

TRUSTED_DOMAINS = {
    "google": "google.com", "microsoft": "microsoft.com",
    "amazon": "amazon.com", "apple": "apple.com",
    "meta": "meta.com", "facebook": "meta.com",
    "stripe": "stripe.com", "netflix": "netflix.com",
    "twitter": "x.com", "linkedin": "linkedin.com",
    "uber": "uber.com", "airbnb": "airbnb.com",
    "spotify": "spotify.com", "adobe": "adobe.com",
    "salesforce": "salesforce.com", "oracle": "oracle.com",
    "ibm": "ibm.com", "intel": "intel.com",
}
FREE_PROVIDERS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                  "live.com", "aol.com", "protonmail.com", "icloud.com"]

def check_domain(email, company):
    if not email or "@" not in email:
        return {"domain_risk": 0, "domain_flag": None}
    domain = email.split("@")[-1].strip().lower()
    company_lower = company.lower()
    for keyword, official in TRUSTED_DOMAINS.items():
        if keyword in company_lower:
            if domain != official:
                return {"domain_risk": 80,
                        "domain_flag": f"Email domain '{domain}' does not match official domain '{official}' for {company}"}
            return {"domain_risk": -15, "domain_flag": None}
    if domain in FREE_PROVIDERS:
        return {"domain_risk": 30,
                "domain_flag": f"Corporate job using free email provider ({domain})"}
    return {"domain_risk": 0, "domain_flag": None}


# LAYER 4 — SMART PATTERNS

def run_smart_patterns(job: JobInput) -> dict:
    flags = []
    risk  = 0
    full  = (job.title + " " + job.description + " " +
             job.requirements + " " + job.benefits).lower()

    word_count = len(job.description.split())
    if word_count < 30:
        flags.append("Job description is unusually short")
        risk += 15
    elif word_count > 20 and not job.requirements.strip():
        flags.append("Long description but no requirements listed")
        risk += 20

    spam_phrases = ["click here to apply", "limited time offer", "this is not a scam",
                    "100% legitimate", "guaranteed income", "risk free"]
    spam_hits = [p for p in spam_phrases if p in full]
    if spam_hits:
        flags.append(f"Spam phrases detected: {', '.join(spam_hits)}")
        risk += 35

    real_signals = ["bachelor", "master", "degree", "years of experience",
                    "401k", "health insurance", "dental", "equity", "pto",
                    "vacation days", "annual bonus"]
    real_hits = sum(1 for s in real_signals if s in full)
    if real_hits >= 3:
        risk -= 20
        flags.append(f"Strong legitimate signals found ({real_hits} professional markers)")

    salary_text = job.salary.lower().replace(",", "")
    if re.search(r"\$\d{4,5}/week", salary_text):
        flags.append("Weekly salary format uncommon in legitimate postings")
        risk += 20

    return {"smart_flags": flags, "smart_risk": max(0, risk)}


# URL SCRAPER

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def extract_job_from_html(html, url):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "aside", "form", "iframe"]):
        tag.decompose()

    job_containers = soup.find_all(
        ["div", "section", "article"],
        class_=lambda c: c and any(
            kw in str(c).lower() for kw in
            ["job", "posting", "description", "content", "detail", "listing", "vacancy"]
        )
    )
    if job_containers:
        main_text = max(job_containers, key=lambda x: len(x.get_text())).get_text(separator=" ", strip=True)
    else:
        body = soup.find("body")
        main_text = body.get_text(separator=" ", strip=True) if body else ""

    main_text = re.sub(r"\s+", " ", main_text).strip()
    title = ""
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    company = ""
    meta_org = soup.find("meta", {"property": "og:site_name"})
    if meta_org:
        company = meta_org.get("content", "")
    if not company:
        domain = urlparse(url).netloc
        company = domain.replace("www.", "").split(".")[0].capitalize()

    return {"title": title[:200], "company": company[:100],
            "raw_text": main_text[:8000], "url": url, "char_count": len(main_text)}


def split_job_sections(raw_text):
    text_lower = raw_text.lower()
    req_markers = ["requirements", "qualifications", "what you need",
                   "what we're looking for", "must have", "minimum qualifications"]
    ben_markers = ["benefits", "perks", "what we offer",
                   "compensation", "why join", "we offer"]

    req_start = next((text_lower.find(m) for m in req_markers if text_lower.find(m) != -1), len(raw_text))
    ben_start = next((text_lower.find(m) for m in ben_markers if text_lower.find(m) != -1), len(raw_text))

    if req_start < len(raw_text) and ben_start > req_start:
        return {"description": raw_text[:req_start].strip()[:2000],
                "requirements": raw_text[req_start:ben_start].strip()[:1000],
                "benefits": raw_text[ben_start:].strip()[:500]}
    elif req_start < len(raw_text):
        return {"description": raw_text[:req_start].strip()[:2000],
                "requirements": raw_text[req_start:].strip()[:1000],
                "benefits": ""}
    return {"description": raw_text[:2000], "requirements": "", "benefits": ""}


# ROUTES

@app.get("/")
def root():
    return {
        "status": "running", "version": "3.0.0",
        "model": "loaded" if model_bundle else "not loaded",
        "model_format": "bundle" if isinstance(model_bundle, dict) else "pipeline",
        "layers": ["ml_model", "rule_engine", "trust_score",
                   "domain_check", "smart_patterns", "external_verification"]
    }

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_bundle is not None}


@app.post("/predict", response_model=PredictionOutput)
async def predict(job: JobInput):
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if not job.title.strip() and not job.description.strip():
        raise HTTPException(status_code=400, detail="Title or description required")

    # Layers 1-4 (fast)
    rule_result   = run_rule_engine(job)
    domain_result = check_domain(job.email or "", job.company)
    smart_result  = run_smart_patterns(job)

    rule_flags  = rule_result["flags"]
    rule_risk   = rule_result["rule_risk"]
    domain_risk = domain_result["domain_risk"]
    domain_flag = domain_result["domain_flag"]
    smart_flags = smart_result["smart_flags"]
    smart_risk  = smart_result["smart_risk"]

    if domain_flag:
        rule_flags.append(domain_flag)

    is_fake, ml_conf = ml_predict(job)

    # Layer 5 — External verification (async, DNS + LLM website check)
    ext = await run_external_verification(
        company = job.company,
        website = job.website or "",
        email   = job.email   or "",
    )
    ext_flags = ext["flags"]
    ext_risk  = ext["risk"]

    # Combine all risk signals
    total_rule_risk = min(100, rule_risk + smart_risk + max(0, domain_risk) + ext_risk)
    trust_result    = calculate_trust_score(ml_conf, is_fake, total_rule_risk)

    if total_rule_risk >= 60:
        final_prediction = "fake"
    elif total_rule_risk <= 0 and not is_fake:
        final_prediction = "real"
    else:
        final_prediction = "fake" if is_fake else "real"

    return PredictionOutput(
        prediction   = final_prediction,
        confidence   = round(ml_conf, 4),
        trust_score  = trust_result["trust_score"],
        risk_level   = trust_result["risk_level"],
        flags        = rule_flags + smart_flags + ext_flags,
        label        = trust_result["label"],
        message      = trust_result["message"],
        verification = ext["details"],
    )


@app.post("/scan-url", response_model=URLScrapeResult)
async def scan_url(data: URLInput):
    url = data.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    parsed_domain = urlparse(url).netloc.lower()
    if any(b in parsed_domain for b in ["linkedin.com", "facebook.com"]):
        raise HTTPException(status_code=400,
            detail="LinkedIn cannot be scraped directly. Please paste job details manually.")

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Page took too long to load. Try pasting details manually.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Could not access URL: HTTP {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    extracted = extract_job_from_html(response.text, url)
    if extracted["char_count"] < 100:
        raise HTTPException(status_code=422, detail="Could not extract enough text. Try pasting manually.")

    sections = split_job_sections(extracted["raw_text"])

    job = JobInput(
        title        = extracted["title"],
        company      = extracted["company"],
        location     = "",
        salary       = "",
        description  = sections["description"],
        requirements = sections["requirements"],
        benefits     = sections["benefits"],
        telecommuting    = 0,
        has_company_logo = 0,   # unknown from scrape → conservative
        has_questions    = 0,
    )

    rule_result   = run_rule_engine(job)
    domain_result = check_domain("", job.company)
    smart_result  = run_smart_patterns(job)

    rule_flags  = rule_result["flags"]
    rule_risk   = rule_result["rule_risk"]
    domain_risk = domain_result["domain_risk"]
    domain_flag = domain_result["domain_flag"]
    smart_flags = smart_result["smart_flags"]
    smart_risk  = smart_result["smart_risk"]

    if domain_flag:
        rule_flags.append(domain_flag)

    is_fake, ml_conf = ml_predict(job)

    total_rule_risk = min(100, rule_risk + smart_risk + max(0, domain_risk))
    trust_result    = calculate_trust_score(ml_conf, is_fake, total_rule_risk)

    if total_rule_risk >= 60:
        final_prediction = "fake"
    elif total_rule_risk <= 0 and not is_fake:
        final_prediction = "real"
    else:
        final_prediction = "fake" if is_fake else "real"

    summary = (
        f"Job: {extracted['title']} at {extracted['company']}. "
        f"Scraped {extracted['char_count']} characters from {parsed_domain}. "
        f"Description: {len(sections['description'])} chars. "
        f"Requirements: {'yes' if sections['requirements'] else 'no'}. "
        f"Benefits: {'yes' if sections['benefits'] else 'no'}."
    )

    return URLScrapeResult(
        success      = True,
        url          = url,
        title        = extracted["title"],
        company      = extracted["company"],
        description  = sections["description"],
        requirements = sections["requirements"],
        benefits     = sections["benefits"],
        summary      = summary,
        prediction   = final_prediction,
        confidence   = round(ml_conf, 4),
        trust_score  = trust_result["trust_score"],
        risk_level   = trust_result["risk_level"],
        flags        = rule_flags + smart_flags,
        label        = trust_result["label"],
        message      = trust_result["message"],
    )
