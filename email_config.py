import smtplib
from email.mime.text import MIMEText

GMAIL_USER = "mohammadsalehdeveloper@gmail.com"
GMAIL_APP_PASSWORD = "lyjf dvlj nxqy erwn"  # app password, not your normal password

msg = MIMEText("Hello from your news tracker")
msg["Subject"] = "News Tracker Test"
msg["From"] = GMAIL_USER
msg["To"] = GMAIL_USER

with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls()
    s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    s.send_message(msg)
