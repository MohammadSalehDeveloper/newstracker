import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "news_tracker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.timezone = "Europe/Berlin"

poll_minutes = int(os.getenv("POLL_MINUTES", "3"))

celery_app.conf.beat_schedule = {
    "poll-gdelt-every-n-minutes": {
        "task": "app.tasks.poll_gdelt_and_alert",
        "schedule": crontab(minute=f"*/{poll_minutes}"),
    }
}