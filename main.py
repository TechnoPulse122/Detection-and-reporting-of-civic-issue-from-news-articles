
import subprocess
import sys
import traceback

from report import send_all_reports


def run_script(script_name, description):
    print(f"\n{'=' * 60}")
    print(f"Starting: {description}")
    print(f"{'=' * 60}")

    try:
        subprocess.run(
            [sys.executable, script_name],
            check=True
        )

        print(f"SUCCESS: {description} completed.\n")
        return True

    except subprocess.CalledProcessError as e:
        print(f"ERROR: {script_name} failed with exit code {e.returncode}")
        return False


def run_system_pipeline():

    dashboard = None

    try:
        # STEP 1: Scraping
        if not run_script(
            "run.py",
            "Scraping news and social media"
        ):
            return

        # STEP 2: NLP preprocessing
        if not run_script(
            "nlp.py",
            "NLP preprocessing"
        ):
            return

        # STEP 3: Final AI classification
        if not run_script(
            "classify.py",
            "Final AI classification"
        ):
            return

        # STEP 4: Email reporting
        print("\n" + "=" * 60)
        print("STEP 4: Sending Email Reports")
        print("=" * 60)

        send_all_reports()

        print("Email reporting completed.")

        # STEP 5: Launch dashboard
        print("\n" + "=" * 60)
        print("STEP 5: Launching Civic Monitoring Dashboard")
        print("=" * 60)

        dashboard = subprocess.Popen(
            [sys.executable, "dash.py"]
        )

        print("Dashboard started.")
        print("Open: http://127.0.0.1:5000")
        print("\nSystem is live. Press Ctrl+C to stop.")

        dashboard.wait()

    except KeyboardInterrupt:
        print("\nShutting down system...")

    except Exception as e:
        print(f"PIPELINE ERROR: {e}")
        traceback.print_exc()

    finally:
        if dashboard and dashboard.poll() is None:
            dashboard.terminate()
            dashboard.wait()

        print("System shut down.")


if __name__ == "__main__":
    run_system_pipeline()
