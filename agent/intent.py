from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class ParsedQuery:
    intent: str                 # 'rev_vs_budget', 'gm_trend', 'opex_breakdown', 'cash_runway', 'unknown'
    month: str | None = None    # '2025-06' style
    last_n: int | None = None   # for trend windows
    currency: str = "USD"


MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
}

def normalize_month(text: str) -> str | None:
    # e.g., "June 2025" -> "2025-06"
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(20\d{2})", text, re.I)
    if not m:
        return None
    mon = MONTH_MAP[m.group(1).lower()]
    year = m.group(2)
    return f"{year}-{mon}"

def parse_last_n(text: str) -> int | None:
    m = re.search(r"last\s+(\d+)\s+months?", text, re.I)
    return int(m.group(1)) if m else None

def detect_intent(q: str) -> ParsedQuery:
    q_l = q.lower()
    # currency (default USD)
    currency = "USD"
    mcur = re.search(r"\b(in|to)\s+(usd|eur|gbp|jpy|krw)\b", q_l)
    if mcur:
        currency = mcur.group(2).upper()

    # order matters a bit
    if ("revenue" in q_l and "budget" in q_l) or "vs budget" in q_l:
        return ParsedQuery("rev_vs_budget", month=normalize_month(q_l), currency=currency)

    if "gross margin" in q_l or "gm%" in q_l:
        return ParsedQuery("gm_trend", last_n=parse_last_n(q_l) or 3, currency=currency)

    if "opex" in q_l and ("breakdown" in q_l or "by category" in q_l):
        return ParsedQuery("opex_breakdown", month=normalize_month(q_l), currency=currency)

    if "cash runway" in q_l or ("runway" in q_l and "cash" in q_l):
        return ParsedQuery("cash_runway", currency=currency)

    return ParsedQuery("unknown", currency=currency)
