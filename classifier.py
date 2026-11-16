import json
import re

import httpx

from config import INDUSTRIES, LLM_API_KEY, LLM_BASE_URL, LLM_EXTRA_PARAMS, LLM_MODELS

LAST_MODEL_USED: dict = {"model": None}

KEYWORDS: dict[str, list[str]] = {
    "AI / ML": ["ai", "machine learning", "llm", "gpt", "neural", "copilot", "agent", "genai", "computer vision", "nlp"],
    "Fintech": ["fintech", "bookkeeping", "accounting", "payments", "banking", "lending", "credit", "invoice", "payroll", "neobank", "insurtech", "insurance", "wealth", "trading"],
    "Healthtech": ["health", "medical", "clinic", "patient", "telehealth", "doctor", "hospital", "mental health", "wellness", "pharma"],
    "Climate / Energy": ["climate", "carbon", "solar", "energy", "battery", "emissions", "sustainab", "renewable", "ev charging", "cleantech"],
    "SaaS / B2B": ["saas", "b2b", "crm", "workflow", "enterprise", "dashboard", "analytics", "productivity"],
    "Developer Tools": ["developer", "api", "sdk", "devops", "open source", "github", "observability", "infrastructure", "database", "kubernetes"],
    "E-commerce / Retail": ["e-commerce", "ecommerce", "shopify", "retail", "marketplace", "checkout", "d2c", "dtc", "store"],
    "Edtech": ["edtech", "education", "learning", "students", "teachers", "course", "tutor", "school", "university"],
    "Proptech / Real Estate": ["real estate", "proptech", "property", "rental", "landlord", "mortgage", "construction"],
    "Mobility / Logistics": ["logistics", "delivery", "fleet", "shipping", "freight", "mobility", "supply chain", "warehouse", "last-mile"],
    "Cybersecurity": ["security", "cyber", "threat", "compliance", "soc 2", "zero trust", "identity", "fraud", "encryption"],
    "Consumer / Social": ["consumer", "social", "community", "dating", "creator", "app for", "friends", "lifestyle"],
    "Biotech": ["biotech", "genomic", "drug discovery", "protein", "therapeutics", "crispr", "molecule", "lab"],
    "Web3 / Crypto": ["web3", "crypto", "blockchain", "defi", "nft", "token", "wallet", "stablecoin"],
    "Hardware / Robotics": ["hardware", "robot", "drone", "iot", "sensor", "manufacturing", "chip", "semiconductor"],
    "Food / Agtech": ["food", "restaurant", "agtech", "farm", "agricultur", "grocery", "meal", "crop"],
    "HR / Future of Work": ["hr", "hiring", "recruit", "talent", "remote work", "employee", "onboarding", "workforce"],
    "Media / Entertainment": ["media", "music", "gaming", "game", "video", "streaming", "podcast", "content", "entertainment"],
}

# AI shows up in every pitch; down-weight it so the domain-specific industry wins ties.
WEIGHTS = {"AI / ML": 0.5}

NON_STARTUP_SIGNALS = [
    "newsletter", "digest", "unsubscribe", "receipt", "your order", "no-reply", "noreply",
    "notifications@", "news@", "invoice #", "password reset", "verify your",
    "calendar-notification", "google calendar", "appointment booked", "darse de baja", "cancelar suscripción",
]

CALENDAR_SUBJECT = re.compile(
    r"^(accepted|declined|tentative|invitation|updated invitation|reminder|aceptado|rechazado|invitación|recordatorio)\b",
    re.I,
)


def _count(text: str, word: str) -> int:
    pattern = r"\b" + re.escape(word) if len(word) <= 4 else re.escape(word)
    return len(re.findall(pattern, text))


def keyword_classify(email: dict) -> dict:
    text = f"{email.get('subject', '')} {email.get('body', '')}".lower()
    scores = {
        ind: WEIGHTS.get(ind, 1) * sum(_count(text, kw) for kw in kws) for ind, kws in KEYWORDS.items()
    }
    best, score = max(scores.items(), key=lambda kv: kv[1])
    sender = (email.get("sender_email") or "").lower()
    is_startup = not (
        any(sig in f"{sender} {text}" for sig in NON_STARTUP_SIGNALS)
        or CALENDAR_SUBJECT.match(email.get("subject") or "")
    )
    domain = sender.split("@")[-1]
    if domain and domain.split(".")[0] not in {"gmail", "googlemail", "outlook", "hotmail", "yahoo", "icloud"}:
        company = domain.split(".")[0].replace("-", " ").title()
    else:
        company = email.get("sender_name") or ""
    return {
        "industry": best if score > 0 else "Other",
        "company": company,
        "is_startup": 1 if is_startup else 0,
        "summary": (email.get("snippet") or "")[:160],
        "classifier": "keywords",
    }


PROMPT = """You sort emails that an investor/ecosystem person receives from startups.
Return ONLY JSON with keys:
- "is_startup": true if the email is from or about a startup (pitch, intro, investor update, launch, partnership), false for newsletters, receipts, calendar invites/scheduling, personal or unrelated mail
Emails may be in Spanish, English or Portuguese.
- "company": the startup's name ("" if unknown)
- "industry": exactly one of {industries}
- "summary": one sentence (max 25 words) on what the startup does / wants

From: {sender}
Subject: {subject}
Body:
{body}
"""


def llm_classify(email: dict) -> dict | None:
    if not LLM_API_KEY:
        return None
    prompt = PROMPT.format(
        industries=json.dumps(INDUSTRIES),
        sender=f"{email.get('sender_name', '')} <{email.get('sender_email', '')}>",
        subject=email.get("subject", ""),
        body=(email.get("body") or "")[:4000],
    )
    data = None
    for model in LLM_MODELS:
        try:
            resp = httpx.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    **LLM_EXTRA_PARAMS,
                },
                timeout=120,
            )
            if resp.status_code in (404, 429, 503) and model != LLM_MODELS[-1]:
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
            LAST_MODEL_USED["model"] = model
            break
        except Exception as exc:  # noqa: BLE001
            print(f"LLM classification with {model} failed: {exc}")
    if data is None:
        return None
    industry = data.get("industry") if data.get("industry") in INDUSTRIES else "Other"
    return {
        "industry": industry,
        "company": str(data.get("company") or ""),
        "is_startup": 1 if data.get("is_startup", True) else 0,
        "summary": str(data.get("summary") or ""),
        "classifier": "llm",
    }


def classify(email: dict) -> dict:
    return llm_classify(email) or keyword_classify(email)
