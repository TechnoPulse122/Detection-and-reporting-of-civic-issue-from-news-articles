import smtplib
from dotenv import load_dotenv
import os
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("testemail")




try:
    print("🔌 Connecting...")

    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)

    print("✅ Connected")

    server.ehlo()
    server.starttls()
    server.ehlo()

    print("✅ TLS started")

    server.login(SENDER_EMAIL, APP_PASSWORD)

    print("✅ Login successful")

    server.quit()

    print("✅ SMTP test completed successfully")

except Exception as e:
    print("❌ SMTP ERROR:", repr(e))