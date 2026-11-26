
import subprocess
import sys
from report import send_all_reports


def run_script(script_name, description):
    print(f"\n{'=' * 60}")
    print(f"Starting: {description}")
    print(f"{'=' * 60}")

    try:
        subprocess.run([sys.executable, script_name], check=True)
        print(f"SUCCESS: {description} completed.\n")
        return True

    except subprocess.CalledProcessError as e:
        print(f"ERROR: {script_name} failed with exit code {e.returncode}")
        return False


def run_system_pipeline():

    # STEP 1: Scraping
    if not run_script("run.py", "Scraping news and social media"):
        return

    # STEP 2: NLP Preprocessing
    if not run_script("nlp.py", "NLP preprocessing"):
        return

    # STEP 3: AI Classification
    if not run_script("classify.py", "AI classification"):
        return

    # STEP 4: Launch Dashboard
    print("\n=== STEP 4: Launching Civic Monitoring Dashboard ===")

    try:
        dashboard = subprocess.Popen(
            [sys.executable, "dash.py"]
        )

        print("Dashboard started.")
        print("Open: http://127.0.0.1:5000")

    except Exception as e:
        print(f"Dashboard launch failed: {e}")
        return

    # STEP 5: Email Reporting
    print("\n=== STEP 5: Starting Automated Email Reporting ===")

    try:
        send_all_reports()
        print("Email reporting completed.\n")

    except Exception as e:
        print(f"Email reporting failed: {e}")

    # Keep dashboard running
    print("System is live. Press Ctrl+C to stop.")

    try:
        dashboard.wait()

    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        dashboard.terminate()
        dashboard.wait()
        print("System shut down successfully.")


if __name__ == "__main__":
    run_system_pipeline()
