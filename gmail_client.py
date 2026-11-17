import email
import email.message
import imaplib
import re
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime
from html import unescape

from datetime import date, timedelta

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GMAIL_MAX_EMAILS, GMAIL_QUERY, GMAIL_START_DATE


def is_configured() -> bool:
    return bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:  # noqa: BLE001
        return value


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _body(msg: email.message.Message) -> str:
    plain, html = [], []
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() == "multipart" or part.get("Content-Disposition", "").startswith("attachment"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if part.get_content_type() == "text/plain":
            plain.append(text)
        elif part.get_content_type() == "text/html":
            html.append(text)
    if plain:
        return re.sub(r"\s+", " ", " ".join(plain)).strip()
    return _html_to_text(" ".join(html))


def _parse(raw: bytes, gm_id: str) -> dict | None:
    msg = email.message_from_bytes(raw)
    name, addr = parseaddr(_decode(msg.get("From")))
    body = _body(msg)
    try:
        received_dt = parsedate_to_datetime(msg.get("Date")).astimezone()
    except Exception:  # noqa: BLE001
        received_dt = None
    if GMAIL_START_DATE and received_dt and received_dt.date() < date.fromisoformat(GMAIL_START_DATE):
        return None
    received = received_dt.isoformat() if received_dt else ""
    return {
        "id": gm_id,
        "source": "gmail",
        "sender_name": name or addr,
        "sender_email": addr,
        "subject": _decode(msg.get("Subject")),
        "snippet": body[:200],
        "body": body[:8000],
        "received_at": received,
    }


def fetch(skip_ids: set[str], since: date | None) -> list[dict]:
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    try:
        imap.select('"[Gmail]/All Mail"', readonly=True)
        if since and since > date.today():
            return []
        parts = []
        if since:
            # Gmail's after: is day-granular; _parse() drops anything before GMAIL_START_DATE.
            parts.append(f"after:{since - timedelta(days=1):%Y/%m/%d}")
        if GMAIL_QUERY:
            parts.append(GMAIL_QUERY)
        query = " ".join(parts)
        _, data = imap.uid("SEARCH", "X-GM-RAW", f'"{query}"')
        uids = data[0].split()
        if not uids:
            return []
        _, id_data = imap.uid("FETCH", b",".join(uids[-5000:]), "(X-GM-MSGID)")
        gm_ids = {}
        for line in id_data:
            raw_line = line[0] if isinstance(line, tuple) else line
            match = re.search(rb"X-GM-MSGID (\d+).*UID (\d+)|UID (\d+).*X-GM-MSGID (\d+)", raw_line or b"")
            if match:
                msgid = match.group(1) or match.group(4)
                uid = match.group(2) or match.group(3)
                gm_ids[uid] = f"gmail-{msgid.decode()}"
        # Slice AFTER dedup: each run classifies up to GMAIL_MAX_EMAILS *new* emails,
        # so a large backlog drains in daily batches without re-classifying.
        todo = [u for u in reversed(uids) if gm_ids.get(u, f"gmail-uid-{u.decode()}") not in skip_ids][:GMAIL_MAX_EMAILS]
        results = []
        for i in range(0, len(todo), 50):
            chunk = todo[i : i + 50]
            _, msg_data = imap.uid("FETCH", b",".join(chunk), "(UID BODY.PEEK[])")
            for part in msg_data:
                if not isinstance(part, tuple):
                    continue
                uid_match = re.search(rb"UID (\d+)", part[0])
                if not uid_match:
                    continue
                uid = uid_match.group(1)
                parsed = _parse(part[1], gm_ids.get(uid, f"gmail-uid-{uid.decode()}"))
                if parsed:
                    results.append(parsed)
        return results
    finally:
        imap.logout()
