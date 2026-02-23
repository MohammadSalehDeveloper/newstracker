from fastapi import FastAPI
from app.tasks import send_test_alerts

app = FastAPI(title="News Tracker MVP")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/test-alerts")
def test_alerts():
    # fire async task
    send_test_alerts.delay()
    return {"queued": True}