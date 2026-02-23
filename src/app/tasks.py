import os
import time
from datetime import datetime, timezone
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.gdelt import fetch_gdelt
from app.notifiers import send_telegram, send_gmail
from app.scoring import classify_topic, urgency_score

logger = get_task_logger(__name__)

# in-memory dedupe for MVP (container restart resets it)
SEEN = {}  # url -> last_sent_epoch


def _dedupe_ok(url: str, window_hours: int = 6) -> bool:
    now = time.time()
    last = SEEN.get(url)
    if last and (now - last) < (window_hours * 3600):
        return False
    SEEN[url] = now
    return True


def _make_query():
    # Hard-filtered query. You can tune this anytime.
    # GDELT query syntax supports boolean operations.
    politics = os.getenv("KEYWORDS_POLITICS", "")
    econ = os.getenv("KEYWORDS_ECON", "")

    # Turn comma list into OR query
    def orize(csv: str):
        parts = [p.strip() for p in csv.split(",") if p.strip()]
        if not parts:
            return ""
        return "(" + " OR ".join([f'"{p}"' if " " in p else p for p in parts]) + ")"

    q = f"({orize(politics)} OR {orize(econ)})"
    # Add some global “signal” words to reduce junk:
    q += " AND (policy OR government OR election OR sanctions OR inflation OR central bank OR rates OR oil OR conflict)"
    return q


@celery_app.task(name="app.tasks.send_test_alerts")
def send_test_alerts():
    send_telegram("✅ News Tracker: Telegram test OK")
    send_gmail("News Tracker Test", "✅ Gmail SMTP test OK")
    return "ok"


@celery_app.task(name="app.tasks.poll_gdelt_and_alert")
def poll_gdelt_and_alert():
    normal_min = int(os.getenv("NORMAL_URGENCY_MIN", "60"))
    critical_min = int(os.getenv("CRITICAL_URGENCY_MIN", "85"))

    query = _make_query()
    logger.info(f"Polling GDELT: {query}")

    data = fetch_gdelt(query=query, maxrecords=50)
    articles = (data or {}).get("articles", []) or []
    logger.info(f"GDELT returned {len(articles)} articles")

    for a in articles:
        title = (a.get("title") or "").strip()
        url = (a.get("url") or "").strip()
        source = (a.get("sourceCountry") or a.get("source") or "").strip()
        seendate = (a.get("seendate") or "").strip()  # often like 2025-...Z
        domain = (a.get("domain") or "").strip()

        if not title or not url:
            continue

        if not _dedupe_ok(url):
            continue

        text_for_scoring = f"{title} {domain} {source}"

        topic = classify_topic(text_for_scoring)

        # Recency heuristic
        recent_minutes = None
        try:
            dt = datetime.fromisoformat(seendate.replace("Z", "+00:00"))
            recent_minutes = int((datetime.now(timezone.utc) - dt).total_seconds() / 60)
        except Exception:
            pass

        score = urgency_score(text_for_scoring, is_breaking=("breaking" in title.lower()), recent_minutes=recent_minutes)

        level = None
        if score >= critical_min:
            level = "CRITICAL"
        elif score >= normal_min:
            level = "NORMAL"

        if not level:
            continue

        msg = (
            f"🛎️ {level} [{topic.upper()}]\n"
            f"{title}\n"
            f"Score: {score}\n"
            f"Source: {domain or source}\n"
            f"{url}"
        )

        # Telegram is primary
        try:
            send_telegram(msg)
        except Exception as e:
            logger.exception(f"Telegram send failed: {e}")

        # Email backup/archive
        try:
            send_gmail(f"{level}: [{topic.upper()}] {title[:120]}", msg)
        except Exception as e:
            logger.exception(f"Email send failed: {e}")

    return f"processed={len(articles)}"