import os
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
# Only emails received on/after this date (YYYY-MM-DD) are pulled.
GMAIL_START_DATE = os.getenv("GMAIL_START_DATE", "2026-11-17")
GMAIL_QUERY = os.getenv("GMAIL_QUERY", "-from:me -filename:ics -category:promotions -category:social")
GMAIL_MAX_EMAILS = int(os.getenv("GMAIL_MAX_EMAILS", "300"))

LLM_PROVIDERS = {
    "lyber": {
        "base_url": "https://api.lyber.ai/v1",
        # Tried in order; DeepSeek is ~14x cheaper, Kimi is the fallback when DeepSeek isn't ready.
        "model": "deepseek-v4.1-flash-1017-abliterated,kimi-k31-pro-abliterated",
        "key_env": "LYBER_API_KEY",
        # Lyber rejects unknown fields (e.g. response_format), so only send documented ones.
        "extra": {"reasoning_effort": "none", "max_tokens": 512},
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "key_env": "OPENAI_API_KEY",
        "extra": {},
    },
}

LLM_PROVIDER = os.getenv("LLM_PROVIDER") or ("lyber" if os.getenv("LYBER_API_KEY") else "openai")
_preset = LLM_PROVIDERS.get(LLM_PROVIDER, LLM_PROVIDERS["openai"])
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv(_preset["key_env"], "")
LLM_BASE_URL = (os.getenv("LLM_BASE_URL") or _preset["base_url"]).rstrip("/")
LLM_MODELS = [m.strip() for m in (os.getenv("LLM_MODEL") or _preset["model"]).split(",") if m.strip()]
LLM_MODEL = LLM_MODELS[0]
LLM_EXTRA_PARAMS = _preset["extra"]


INDUSTRIES = [
    "AI / ML",
    "Fintech",
    "Healthtech",
    "Climate / Energy",
    "SaaS / B2B",
    "Developer Tools",
    "E-commerce / Retail",
    "Edtech",
    "Proptech / Real Estate",
    "Mobility / Logistics",
    "Cybersecurity",
    "Consumer / Social",
    "Biotech",
    "Web3 / Crypto",
    "Hardware / Robotics",
    "Food / Agtech",
    "HR / Future of Work",
    "Media / Entertainment",
    "Other",
]
