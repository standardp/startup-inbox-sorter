"""Fetch new Gmail messages, classify them by industry and write the encrypted docs/data.json.

Run by the GitHub Actions workflow once a day. Locally: `python sync.py --sample` builds demo data.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

import classifier
import gmail_client
from config import GMAIL_START_DATE, INDUSTRIES, LLM_API_KEY, LLM_MODEL, LLM_PROVIDER
from crypto_store import decrypt, encrypt
from sample_data import sample_emails

DATA_FILE = Path(__file__).parent / "docs" / "data.json"


def load(passphrase: str) -> dict:
    if not DATA_FILE.exists():
        return {"emails": []}
    # Raises on a wrong passphrase, so existing data is never overwritten.
    return decrypt(json.loads(DATA_FILE.read_text()), passphrase)


def main() -> None:
    sample = "--sample" in sys.argv
    passphrase = os.getenv("DASHBOARD_PASSPHRASE", "demo" if sample else "")
    if not passphrase:
        sys.exit("DASHBOARD_PASSPHRASE is not set")
    if not sample and not gmail_client.is_configured():
        sys.exit("GMAIL_ADDRESS / GMAIL_APP_PASSWORD are not set")

    data = {"emails": []} if sample else load(passphrase)
    emails = {e["id"]: e for e in data["emails"]}
    if sample:
        new = sample_emails()
    else:
        since = date.fromisoformat(GMAIL_START_DATE) if GMAIL_START_DATE else None
        if since and data.get("last_sync"):
            since = max(since, date.fromisoformat(data["last_sync"][:10]) - timedelta(days=2))
        new = gmail_client.fetch(set(emails), since)

    with ThreadPoolExecutor(max_workers=8) as pool:
        for e, result in zip(new, pool.map(classifier.classify, new)):
            emails[e["id"]] = {**e, **result}

    out = {
        "emails": sorted(emails.values(), key=lambda e: e.get("received_at") or "", reverse=True),
        "industries": INDUSTRIES,
        "source": "sample" if sample else "gmail",
        "start_date": GMAIL_START_DATE,
        "classifier": f"{LLM_PROVIDER} / {classifier.LAST_MODEL_USED['model'] or LLM_MODEL}" if LLM_API_KEY else "keywords",
        "last_sync": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo": os.getenv("GITHUB_REPOSITORY", ""),
    }
    DATA_FILE.write_text(json.dumps(encrypt(out, passphrase)))
    print(f"Added {len(new)} email(s); {len(emails)} total")


if __name__ == "__main__":
    main()
