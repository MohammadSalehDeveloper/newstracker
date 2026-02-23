import os
import smtplib
import requests
from email.mime.text import MIMEText


def send_telegram(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": False}, timeout=20)
    r.raise_for_status()


def send_gmail(subject: str, body: str) -> None:
    user = os.getenv("GMAIL_USER", "").strip()
    app_pw = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not user or not app_pw:
        raise RuntimeError("Missing GMAIL_USER or GMAIL_APP_PASSWORD in .env")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = user

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
        s.starttls()
        s.login(user, app_pw)
        s.send_message(msg)