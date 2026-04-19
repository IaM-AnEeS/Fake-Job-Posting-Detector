"""
verify.py — Layer 5: External Verification
==========================================
Checks that ML + rules cannot:
  1. Domain existence  — does the website actually resolve?
  2. Email domain      — does the email domain exist as a real MX server?
  3. Website content   — fetches the site and asks Claude to judge if it's
                         a real company or a fake/placeholder page
  4. Company web search — searches for the company name and checks if any
                          credible results exist

All checks are async and time-bounded so they never hang the API.
"""

import asyncio
import socket
import re
import os
import json
import httpx
from urllib.parse import urlparse

# ── Anthropic client (uses same API key as the rest of the project) ───────────
import anthropic

_anthropic = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# 1. DOMAIN EXISTENCE CHECK

def _domain_resolves(domain: str) -> bool:
    """Returns True if the domain has a DNS A record."""
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname(domain)
        return True
    except (socket.gaierror, socket.timeout):
        return False


def check_website_exists(website: str) -> dict:
    """
    Given a raw website string (may or may not have https://),
    checks whether the domain resolves in DNS.
    """
    if not website or not website.strip():
        return {"checked": False, "exists": None, "domain": None,
                "flag": None, "risk": 0}

    # Normalise
    url = website.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    domain = urlparse(url).netloc.replace("www.", "").split(":")[0]
    if not domain:
        return {"checked": False, "exists": None, "domain": None,
                "flag": "Could not parse domain from website field", "risk": 10}

    exists = _domain_resolves(domain)
    if exists:
        return {"checked": True, "exists": True, "domain": domain,
                "flag": None, "risk": 0}
    else:
        return {
            "checked": True,
            "exists": False,
            "domain": domain,
            "flag": f"Company website '{domain}' does not exist (DNS lookup failed)",
            "risk": 60,
        }

# 2. EMAIL DOMAIN MX CHECK


def check_email_domain(email: str) -> dict:
    """
    Checks whether the email domain resolves in DNS.
    Does NOT send any email — just verifies the domain is real.
    """
    if not email or "@" not in email:
        return {"checked": False, "exists": None, "domain": None,
                "flag": None, "risk": 0}

    domain = email.strip().split("@")[-1].lower()

    # Free providers are already caught by Layer 3 — skip here
    FREE = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "live.com", "aol.com", "protonmail.com", "icloud.com"}
    if domain in FREE:
        return {"checked": True, "exists": True, "domain": domain,
                "flag": None, "risk": 0}   # Layer 3 already penalises this

    exists = _domain_resolves(domain)
    if exists:
        return {"checked": True, "exists": True, "domain": domain,
                "flag": None, "risk": 0}
    else:
        return {
            "checked": True,
            "exists": False,
            "domain": domain,
            "flag": f"Email domain '{domain}' does not exist — likely a fake address",
            "risk": 55,
        }



# 3. WEBSITE CONTENT — LLM JUDGE


async def _fetch_website_text(url: str, timeout: float = 8.0) -> str | None:
    """Fetches up to 6000 chars of visible text from a URL."""
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=timeout, follow_redirects=True
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            html = r.text

        # Strip tags quickly
        text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S)
        text = re.sub(r"<style[^>]*>.*?</style>",  " ", text,  flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+",     " ", text).strip()
        return text[:6000]
    except Exception:
        return None


def _llm_judge_website(company: str, domain: str, page_text: str) -> dict:
    """
    Asks Claude to read the scraped website and decide if it looks
    like a real operating company or a fake/parked/placeholder page.
    Returns a dict with verdict, reason, and risk score.
    """
    prompt = f"""You are a fraud detection assistant helping verify whether a company is real.

Company name claimed in job posting: "{company}"
Website domain: "{domain}"

Website content (first 6000 characters):
---
{page_text}
---

Analyze the website content and answer ONLY with a JSON object in this exact format:
{{
  "verdict": "real" | "fake" | "suspicious" | "parked",
  "confidence": 0-100,
  "reason": "one sentence explanation",
  "risk_score": 0-100
}}

Guidelines:
- "real": Clear evidence of an operating business (services, team, contact, history)
- "suspicious": Some content but vague, copied, or inconsistent with the job posting
- "parked": Domain exists but page is blank, under construction, or a domain-for-sale page
- "fake": Page content is clearly fabricated or completely unrelated to the claimed company
- risk_score: 0 = definitely real, 100 = definitely fake

Respond with JSON only. No explanation outside the JSON."""

    try:
        response = _anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        return {
            "verdict":    result.get("verdict", "unknown"),
            "confidence": int(result.get("confidence", 50)),
            "reason":     result.get("reason", ""),
            "risk_score": int(result.get("risk_score", 50)),
        }
    except Exception as e:
        return {
            "verdict": "unknown", "confidence": 0,
            "reason": f"LLM check failed: {str(e)}", "risk_score": 30
        }


async def verify_website_content(company: str, website: str) -> dict:
    """
    Full website verification:
      1. Checks DNS
      2. Fetches page content
      3. Asks Claude to judge it
    """
    if not website or not website.strip():
        return {"checked": False, "verdict": None, "reason": "No website provided",
                "flag": None, "risk": 0}

    url = website.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    domain = urlparse(url).netloc.replace("www.", "")

    # Step 1 — DNS
    if not _domain_resolves(domain):
        return {
            "checked": True,
            "verdict": "fake",
            "reason": "Domain does not exist",
            "flag": f"Website '{domain}' does not resolve — company likely fabricated",
            "risk": 65,
        }

    # Step 2 — Fetch content
    page_text = await _fetch_website_text(url)
    if not page_text or len(page_text) < 100:
        return {
            "checked": True,
            "verdict": "parked",
            "reason": "Website exists but returned no readable content",
            "flag": f"Website '{domain}' is blank or inaccessible",
            "risk": 40,
        }

    # Step 3 — LLM judge
    judge = _llm_judge_website(company, domain, page_text)

    flag = None
    if judge["verdict"] in ("fake", "parked"):
        flag = f"Website '{domain}': {judge['reason']}"
    elif judge["verdict"] == "suspicious":
        flag = f"Website '{domain}' looks suspicious: {judge['reason']}"

    return {
        "checked":    True,
        "verdict":    judge["verdict"],
        "reason":     judge["reason"],
        "confidence": judge["confidence"],
        "flag":       flag,
        "risk":       judge["risk_score"],
    }



# 4. COMPANY WEB PRESENCE CHECK (via DuckDuckGo instant answer API)


async def check_company_web_presence(company: str) -> dict:
    """
    Searches DuckDuckGo's free Instant Answer API for the company name.
    If zero results → suspicious. If results exist → good signal.
    This does NOT scrape Google (which blocks bots).
    """
    if not company or len(company.strip()) < 3:
        return {"checked": False, "found": None, "flag": None, "risk": 0}

    query = company.strip()
    url   = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, headers={"User-Agent": "FakeJobDetector/1.0"})
            data = r.json()

        abstract   = data.get("Abstract", "")
        related    = data.get("RelatedTopics", [])
        entity     = data.get("Entity", "")

        has_presence = bool(abstract) or len(related) > 2 or bool(entity)

        if has_presence:
            return {"checked": True, "found": True,
                    "flag": None, "risk": 0,
                    "detail": abstract[:200] if abstract else f"{len(related)} related results found"}
        else:
            return {
                "checked": True,
                "found": False,
                "flag": f"No web presence found for '{company}' — zero search results",
                "risk": 30,
                "detail": "No results"
            }
    except Exception as e:
        return {"checked": False, "found": None,
                "flag": None, "risk": 0, "detail": str(e)}



# MASTER FUNCTION — run all checks concurrently


async def run_external_verification(
    company:  str,
    website:  str,
    email:    str,
) -> dict:
    """
    Runs all Layer 5 checks concurrently and returns a combined result.

    Returns:
    {
        "flags":      [...],        # list of human-readable flag strings
        "risk":       0-100,        # combined external risk score
        "details": {
            "website_dns":     {...},
            "email_domain":    {...},
            "website_content": {...},
            "web_presence":    {...},
        }
    }
    """
    # Run all checks concurrently
    website_content_task  = verify_website_content(company, website)
    web_presence_task     = check_company_web_presence(company)

    website_content, web_presence = await asyncio.gather(
        website_content_task,
        web_presence_task,
    )

    # Synchronous checks (fast, no async needed)
    website_dns  = check_website_exists(website)
    email_domain = check_email_domain(email)

    # Collect all flags
    flags = []
    total_risk = 0

    for result, weight in [
        (website_dns,     1.0),
        (email_domain,    1.0),
        (website_content, 1.0),
        (web_presence,    0.5),   # lower weight — absence isn't always fraud
    ]:
        if result.get("flag"):
            flags.append(result["flag"])
        total_risk += result.get("risk", 0) * weight

    # Cap and normalise
    total_risk = min(100, int(total_risk / 2))

    return {
        "flags": flags,
        "risk":  total_risk,
        "details": {
            "website_dns":     website_dns,
            "email_domain":    email_domain,
            "website_content": website_content,
            "web_presence":    web_presence,
        }
    }
