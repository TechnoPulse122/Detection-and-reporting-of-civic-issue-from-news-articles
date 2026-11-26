
import os
import traceback
from datetime import datetime
import pytz

from db import init_db
import scraper

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
TIMEZONE = "Asia/Kolkata"


def log(msg):
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"

    print(line)

    log_file = os.path.join(
        LOG_DIR,
        f"{now.strftime('%Y-%m-%d')}.log"
    )

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_pipeline():
    log("=" * 50)
    log("NEWS SCRAPING STARTED")
    log("=" * 50)

    try:
        log("Step 1 — Initializing database...")
        init_db()

        log("Step 2 — Scraping news and social media...")
        scraper.scrape_all(limit_per_source=15)

        log("NEWS SCRAPING COMPLETED SUCCESSFULLY")

    except Exception as e:
        log(f"SCRAPING ERROR: {e}")
        log(traceback.format_exc())

        # Make main.py aware that scraping failed
        raise


if __name__ == "__main__":
    run_pipeline()
