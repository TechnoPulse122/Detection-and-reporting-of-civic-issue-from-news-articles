import os
import traceback
from datetime import datetime
import pytz

# Import your custom modules
from db import init_db
import scraper
import classify
import report

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
TIMEZONE = "Asia/Kolkata"

def log(msg):
    tz = pytz.timezone(TIMEZONE)
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_file = os.path.join(LOG_DIR, f"{datetime.now(tz).strftime('%Y-%m-%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run_pipeline():
    log("=" * 50)
    log("   LUDHIANA CIVIC PIPELINE STARTED")
    log("=" * 50)

    try:
        # Step 1: Database Setup
        log("Step 1 — Initializing database tables...")
        init_db()

        # Step 2: Scraping
        # This calls scrape_all() from scraper.py, which uses db.py to save raw articles
        log("Step 2 — Scraping news from HT, Tribune, TOI, Jagran, and PK...")
        scraper.scrape_all(limit_per_source=15)

        # Step 3: Classification
        # This calls run_classifier() from classify.py (Matches your script's function name)
        log("Step 4 — Running AI Classifier (Groq Llama 3.1)...")
        classify.run_classifier()

        # Step 4: Reporting
        # This calls send_all_reports() from report.py
        log("Step 5 — Sending email reports to departments...")
        report.send_all_reports()

        log("=" * 50)
        log("✅ PIPELINE EXECUTION COMPLETE")
        log("=" * 50)

    except Exception as e:
        log(f"❌ CRITICAL PIPELINE ERROR: {e}")
        log(traceback.format_exc())

if __name__ == "__main__":
    run_pipeline()