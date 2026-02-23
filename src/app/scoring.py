import os
import re

def _csv_env(name: str):
    raw = os.getenv(name, "")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]

POLITICS_KW = _csv_env("KEYWORDS_POLITICS")
ECON_KW = _csv_env("KEYWORDS_ECON")

STRONG = [
    "sanction", "designated", "blacklist", "export control",
    "rate decision", "interest rate", "hike", "cut",
    "missile", "airstrike", "attack", "explosion", "assassination",
    "martial law", "state of emergency",
    "default", "bankruptcy", "bank run",
]

MEDIUM = [
    "ceasefire", "deal", "agreement", "talks", "negotiation",
    "budget", "court ruling", "indictment",
    "inflation", "cpi", "gdp", "unemployment",
]

ENTITIES = [
    "fed", "ecb", "white house", "u.s. treasury", "treasury",
    "pentagon", "nato", "eu commission",
    "irgc", "iaea", "strait of hormuz", "suez", "bab el-mandeb",
]


def classify_topic(text: str) -> str:
    t = text.lower()
    p_hits = sum(1 for k in POLITICS_KW if k in t)
    e_hits = sum(1 for k in ECON_KW if k.lower() in t)
    if e_hits > p_hits:
        return "economy"
    if p_hits > e_hits:
        return "politics"
    # fallback
    if any(x in t for x in ["inflation", "cpi", "gdp", "unemployment", "rates", "bond", "oil"]):
        return "economy"
    return "politics"


def urgency_score(text: str, is_breaking: bool = False, recent_minutes: int | None = None) -> int:
    t = text.lower()
    score = 0

    for kw in STRONG:
        if kw in t:
            score += 40
    for kw in MEDIUM:
        if kw in t:
            score += 20
    for ent in ENTITIES:
        if ent in t:
            score += 10

    # crude "new numbers" boost
    if re.search(r"\b\d+(\.\d+)?\s?(%|bps|basis points|million|billion|trillion|usd|eur)\b", t):
        score += 10

    if is_breaking:
        score += 15
    if recent_minutes is not None and recent_minutes <= 30:
        score += 15

    if score > 100:
        score = 100
    if score < 0:
        score = 0
    return score