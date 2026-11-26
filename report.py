import smtplib
import json
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os

# Standardized import matching your core MySQL Database helper file
from db import get_connection, log_email, init_db
load_dotenv()
# ==============================
# CONFIGURATION
# ==============================
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("testemail") 


#updation---------------------------------------------------------------------------------------------------------

DEPARTMENT_EMAILS = {
    "Ludhiana Traffic Police": os.getenv("emailfirst"),  
    "Punjab Health Department": os.getenv("emailfirst"),
}

ZONE_EMAILS = {
    "Zone A": os.getenv("emailsecond"),
    "Zone B": os.getenv("emailsecond"),
    "Zone C": os.getenv("emailsecond"),
    "Zone D": os.getenv("emailsecond"),
    "Zone Unknown": os.getenv("emailsecond"),
}
#------------------------------------------------------------------------------------------------------------
# ==============================
# ZONE MAPPING (locality → zone)
# ==============================
ZONE_MAP = {
    # ZONE A — Central / Old City (Mata Rani Chowk HQ)
    "Chaura Bazaar": "Zone A", "Dal Bazaar": "Zone A", "Ghas Mandi": "Zone A", "Purana Bazaar": "Zone A",
    "Pansari Bazaar": "Zone A", "Sadar Bazaar": "Zone A", "Kesar Ganj": "Zone A", "Kitab Bazaar": "Zone A",
    "Lakkad Bazaar": "Zone A", "Partap Bazaar": "Zone A", "Hindi Bazaar": "Zone A", "Gur Mandi": "Zone A",
    "GT Road": "Zone A", "Field Ganj": "Zone A", "Civil Lines": "Zone A", "Circular Road": "Zone A",
    "Daresi Road": "Zone A", "Jail Road": "Zone A", "Brown Road": "Zone A", "Hospital Road": "Zone A",
    "CMC Hospital": "Zone A", "Banjiman Road": "Zone A", "Iqbal Ganj": "Zone A", "Gokul Road": "Zone A",
    "Fateh Ganj": "Zone A", "Kidwai Nagar": "Zone A", "Mata Rani Chowk": "Zone A", "Clock Tower": "Zone A",
    "Chawal Bazaar": "Zone A", "Mina Bazaar": "Zone A", "Madhopuri": "Zone A", "Harbanspura": "Zone A",
    "Islamia School Road": "Zone A", "Gaushala Road": "Zone A", "Gandhi Nagar": "Zone A", "Shivpuri": "Zone A",
    "Basant Nagar": "Zone A", "Kalyan Nagar": "Zone A", "Subhash Nagar": "Zone A", "Bhagatpura": "Zone A",
    "Guru Nanak Nagar": "Zone A", "Salem Tabri": "Zone A", "Neta Ji Nagar": "Zone A", "Janakpuri": "Zone A",
    "Sardar Nagar": "Zone A", "Basti Jodhewal": "Zone A", "Rahon Road": "Zone A", "Azad Nagar": "Zone A",
    "Aman Nagar": "Zone A", "Dana Mandi": "Zone A", "Noorwala Road": "Zone A", "Kakowal Road": "Zone A",
    "Jalandhar Bypass": "Zone A", "Bhadurke Road": "Zone A", "New Shimla Colony": "Zone A", "Lajpat Nagar": "Zone A",
    "Bhadaur House": "Zone A", "Shahpur Road": "Zone A", "Issa Nagri": "Zone A", "Kamran Road": "Zone A",

    # ZONE B — North-East (Backside Shingar Cinema HQ)
    "Focal Point": "Zone B", "Sherpur": "Zone B", "Sherpur Kalan": "Zone B", "Sherpur Khurd": "Zone B",
    "Dhandari": "Zone B", "Dhandari Khurd": "Zone B", "Tajpur Road": "Zone B", "Tibba Road": "Zone B",
    "Chandigarh Road": "Zone B", "Mundian": "Zone B", "Mundian Kalan": "Zone B", "Kuliewal": "Zone B",
    "Bhamian Road": "Zone B", "Jamalpur": "Zone B", "Central Jail": "Zone B", "Gopal Chowk": "Zone B",
    "Subhash Nagar": "Zone B", "Adarsh Nagar": "Zone B", "Amarpura": "Zone B", "Habib Ganj": "Zone B",
    "Islam Ganj": "Zone B", "Mushtaq Ganj": "Zone B", "Kot Alamgir": "Zone B", "Kidwai Nagar LIT": "Zone B",
    "Hargobind Nagar": "Zone B", "Cheema Chowk": "Zone B", "Cheema Colony": "Zone B", "Janakpuri TP": "Zone B",
    "Industrial Area A": "Zone B", "Shingar Cinema": "Zone B", "Dharampura": "Zone B", "Samrala Chowk": "Zone B",
    "Moti Nagar": "Zone B", "Transport Nagar": "Zone B", "Hargobindpura": "Zone B", "Arya Colony": "Zone B",
    "Baba Deep Singh Nagar": "Zone B", "Kailash Nagar": "Zone B", "Guru Bagh Colony": "Zone B", "Kuldeep Nagar": "Zone B",
    "Kashmir Nagar": "Zone B", "Kirpal Nagar": "Zone B", "Daulat Colony": "Zone B", "Nirankari Colony": "Zone B",
    "Sunder Nagar": "Zone B", "Jagat Nagar": "Zone B", "Harcharan Nagar": "Zone B", "Basti Mani Singh": "Zone B",
    "Rahon Road Tibba": "Zone B", "Golden Avenue": "Zone B", "Punjabi Bagh": "Zone B", "Guru Nanak Nagar Tibba": "Zone B",
    "GTB Nagar": "Zone B", "Shakti Nagar": "Zone B", "Police Colony Tibba": "Zone B", "Sector 32": "Zone B",
    "Sector 33": "Zone B", "Sector 38": "Zone B", "Sector 39": "Zone B", "Sector 40": "Zone B",

    # ZONE C — South-West (Gill Chowk HQ)
    "Gill Road": "Zone C", "Gill Chowk": "Zone C", "Dholewal": "Zone C", "Dholewal Chowk": "Zone C",
    "Shimlapuri": "Zone C", "New Shimlapuri": "Zone C", "Giaspura": "Zone C", "Daba": "Zone C",
    "Daba Colony": "Zone C", "Daba Road": "Zone C", "Lohara": "Zone C", "Daba Lohara Road": "Zone C",
    "Sua Road": "Zone C", "Tedi Road": "Zone C", "33 Feet Road": "Zone C", "Millarganj": "Zone C",
    "Millar Ganj": "Zone C", "Mungfali Mandi": "Zone C", "Central Market": "Zone C", "Gobindpura": "Zone C",
    "Haripura": "Zone C", "Himatpura": "Zone C", "Sewakpura": "Zone C", "Nanakpuri": "Zone C",
    "Deep Nagar": "Zone C", "Arjan Nagar": "Zone C", "Chet Singh Nagar": "Zone C", "Dasmesh Nagar": "Zone C",
    "ATI Chowk": "Zone C", "Ittan Wala Chowk": "Zone C", "Janta Nagar Gill": "Zone C", "New Janta Nagar": "Zone C",
    "Overlock Road": "Zone C", "Double Fatak": "Zone C", "Manju Cinema": "Zone C", "Dhoori Line": "Zone C",
    "Industrial Area B": "Zone C", "Industrial Area C": "Zone C", "Dhandari Kalan": "Zone C", "Dugri": "Zone C",
    "Preet Nagar Dugri": "Zone C", "Jagdish Nagar Dugri": "Zone C", "BHS Nagar": "Zone C", "Canal Avenue": "Zone C",
    "Jawaddi": "Zone C", "Karol Bagh Dugri": "Zone C", "MBD Mall": "Zone C", "South Bypass": "Zone C",
    "Guru Nanak Colony Gill": "Zone C", "Shaheed Karnail Singh Nagar": "Zone C", "Nirmal Nagar": "Zone C",
    "Bhai Himmat Singh Nagar": "Zone C", "Merado Colony": "Zone C", "Pakhowal": "Zone C",

    # ZONE D — South / Industrial (Sarabha Nagar HQ)
    "Model Town": "Zone D", "Model Town Extension": "Zone D", "New Model Town": "Zone D", "South Model Gram": "Zone D",
    "Sarabha Nagar": "Zone D", "BRS Nagar": "Zone D", "New BRS Nagar": "Zone D", "Sham Nagar": "Zone D",
    "Haibowal": "Zone D", "Haibowal Kalan": "Zone D", "Tagore Nagar": "Zone D", "New Tagore Nagar": "Zone D",
    "Sandhu Nagar": "Zone D", "Joshi Nagar": "Zone D", "Chander Nagar Haibowal": "Zone D", "Bhagat Singh Nagar Haibowal": "Zone D",
    "Sun City": "Zone D", "Ranjodh Park": "Zone D", "Rajguru Nagar": "Zone D", "Barewal": "Zone D",
    "Ferozpur Road": "Zone D", "Ferozepur Road": "Zone D", "Pakhowal Road": "Zone D", "Jawadi": "Zone D",
    "Punjab Mata Nagar": "Zone D", "Shaheed Karnail Singh Ph": "Zone D", "Guru Gyan Vihar": "Zone D", "Sarvmitra Colony": "Zone D",
    "Kanchan Colony": "Zone D", "Passi Nagar": "Zone D", "Basant Vihar Jawadi": "Zone D", "Punjabi Bagh Jawadi": "Zone D",
    "Kartar Nagar Dugri": "Zone D", "Dugri Main Road": "Zone D", "Atam Nagar": "Zone D", "Model Gram": "Zone D",
    "Sargodha Colony": "Zone D", "Canal Colony": "Zone D", "ESI Hospital": "Zone D", "Feroze Gandhi Market": "Zone D",
    "Kundan Nagar": "Zone D", "Model House": "Zone D", "Jawahar Nagar Camp": "Zone D", "Gandhi Colony": "Zone D",
    "Harnaam Nagar": "Zone D", "Jagjit Nagar": "Zone D", "Green Field": "Zone D", "Lajpat Nagar Model Town": "Zone D",
    "Sant Fateh Singh Nagar": "Zone D", "Pritam Nagar Model Town": "Zone D", "Hambran Road": "Zone D", "Kitchlu Nagar": "Zone D",
    "Mall Road": "Zone D", "DMC": "Zone D", "Dayanand Hospital": "Zone D", "Ghumar Mandi": "Zone D",
    "Rose Garden": "Zone D", "National Road": "Zone D", "College Road": "Zone D", "Club Road": "Zone D",
    "Ferozpur Road Canal": "Zone D", "Punjab Agricultural University": "Zone D", "PAU": "Zone D", "Civil Lines Area": "Zone D",
    "Kundan Puri": "Zone D", "Shahi Mohalla": "Zone D", "Court Road": "Zone D", "Session Chowk": "Zone D",
    "Dairy Complex": "Zone D", "Hambran Chowk": "Zone D", "Focal Point Sahnewal": "Zone D", "Sahnewal": "Zone D",
    "Ludhiana City Centre": "Zone D", "Jawadi Chowk": "Zone D", "Pakhowal Road Canal": "Zone D", "Lodhi Club": "Zone D",
    "New BRS Nagar Pakhowal": "Zone D", "Housefed Complex": "Zone D", "Gobind Nagar Civil": "Zone D", "Bharat Nagar": "Zone D",
    "Bus Stand": "Zone D", "Preet Cinema": "Zone D", "Sita Nagar": "Zone D", "Sham Nagar Bus Stand": "Zone D",
    "Link Road": "Zone D", "Jagraon Bridge": "Zone D", "Abdullapur Basti": "Zone D", "Engine Shed": "Zone D",
    "Aarti Road": "Zone D", "Tajpur": "Zone D", "Koom Kalan": "Zone D", "Phases IV": "Zone D",
    "Focal Point Phase": "Zone D",
}

def get_zone(locality: Optional[str]) -> str:
    """Match locality string to MCL zone."""
    if not locality:
        return "Zone Unknown"
    if locality.startswith("["):
        try:
            locs = json.loads(locality)
            for loc in locs:
                zone = _match_zone(str(loc))
                if zone != "Zone Unknown":
                    return zone
            return "Zone Unknown"
        except Exception:
            pass
    return _match_zone(locality)

def _match_zone(locality: str) -> str:
    locality_lower = locality.lower()
    for area, zone in ZONE_MAP.items():
        if area.lower() in locality_lower:
            return zone
    return "Zone Unknown"

# ==============================
# DATABASE LAYER (MySQL Helper Routing)
# ==============================
def get_unreported_issues() -> List[Dict]:
    """Fetch detected civic issues from MySQL that haven't been emailed yet."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Query issues missing delivered records in email_log
    cursor.execute("""
        SELECT 
            i.id,
            i.title,
            i.detected_at       AS scraped_at,
            i.issue             AS issue_type,
            i.department        AS concerned_department,
            i.location          AS locality,
            i.severity,
            i.source,
            i.link
        FROM issues i
        LEFT JOIN email_log el ON i.id = el.issue_id AND el.status = 'sent'
        WHERE el.id IS NULL
          AND i.issue != 'General News'
        ORDER BY 
            CASE UPPER(i.severity)
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END,
            i.detected_at DESC
    """)
    issues = cursor.fetchall()
    cursor.close()
    conn.close()
    return issues

# ==============================
# EMAIL BUILDER (Plain Text Format)
# ==============================
def build_email_text(department: str, issues: List[Dict]) -> str:
    """Build plain text email for one department."""
    now  = datetime.now().strftime("%d %b %Y, %I:%M %p")
    sep  = "=" * 60
    dash = "-" * 60

    critical_count = sum(1 for i in issues if (str(i.get("severity") or "")).lower() == "critical")
    high_count     = sum(1 for i in issues if (str(i.get("severity") or "")).lower() == "high")

    lines = []
    lines.append(sep)
    lines.append("LUDHIANA CIVIC ISSUE REPORT")
    lines.append(f"Generated : {now}")
    lines.append(f"Department: {department}")
    lines.append(sep)
    lines.append(f"Total Issues : {len(issues)}  |  Critical : {critical_count}  |  High : {high_count}")
    lines.append(sep)
    lines.append("")

    for idx, issue in enumerate(issues, 1):
        locality = issue.get("locality") or "Ludhiana"
        if locality.startswith("["):
            try:
                locs     = json.loads(locality)
                locality = ", ".join(str(l).strip('"') for l in locs)
            except Exception:
                pass

        zone       = get_zone(locality)
        date       = str(issue.get("scraped_at") or "—")[:16].replace("T", " ")
        title      = issue.get("title")        or "Untitled"
        issue_type = issue.get("issue_type")   or "Other"
        severity   = str(issue.get("severity")  or "—").upper()
        source     = issue.get("source")       or "—"
        link       = issue.get("link")         or "—"

        lines.append(f"[{idx}] {title}")
        lines.append(dash)
        lines.append(f"  Date      : {date}")
        lines.append(f"  Category  : {issue_type}")
        lines.append(f"  Severity  : {severity}")
        lines.append(f"  Location  : {locality}")
        lines.append(f"  Zone      : {zone}")
        lines.append(f"  Source    : {source}")
        lines.append(f"  Link      : {link}")
        lines.append("")

    lines.append(sep)
    lines.append("This is an automated report by the Ludhiana Civic Monitor system.")
    lines.append("Please take necessary action at the earliest.")
    lines.append(sep)

    return "\n".join(lines)

# ==============================
# DEPARTMENT NAME NORMALISER
# ==============================
DEPT_ALIASES = {
    "Municipal Corporation Ludhiana (O&M Cell)": "Municipal Corporation Ludhiana (Operations & Maintenance - O&M Branch)",

    "Municipal Corporation Ludhiana (Roads Branch)": "Municipal Corporation Ludhiana (Building & Roads - B&R Branch)",

    "Municipal Corporation Ludhiana (Street Lighting Cell)": "Municipal Corporation Ludhiana (Lights Branch)",

    "Municipal Corporation Ludhiana (Estate Department)": "Municipal Corporation Ludhiana (Estate Branch)",

    "Municipal Corporation": "Municipal Corporation Ludhiana (Building & Roads - B&R Branch)",

    "Municipal Corporation Ludhiana": "Municipal Corporation Ludhiana (Building & Roads - B&R Branch)",
} 

def normalise_dept(dept: str) -> str:
    return DEPT_ALIASES.get(dept, dept)

def is_mcl_department(dept: str) -> bool:
    """
    Returns True for any Municipal Corporation Ludhiana department.
    """
    if not dept:
        return False

    return dept == "Municipal Corporation Ludhiana" or \
           dept.startswith("Municipal Corporation Ludhiana (")

# ==============================
# MAIN REPORTING PIPELINE
# ==============================

def run_report():
    init_db()

    # ==========================================
    # GET UNREPORTED CIVIC ISSUES
    # ==========================================
    issues = get_unreported_issues()

    if not issues:
        print("✅ No new civic issues to report.")
        return

    print(f"\n{'═'*55}")
    print(
        f"  Ludhiana Civic Report — "
        f"{datetime.now().strftime('%d %b %Y %I:%M %p')}"
    )
    print(f"  {len(issues)} new issue(s) to report")
    print(f"{'═'*55}")

    # ==========================================
    # GROUP ISSUES
    # ==========================================
    dept_groups: Dict[str, List[Dict]] = {}
    zone_groups: Dict[str, List[Dict]] = {}
    skipped = []

    for issue in issues:

        dept = normalise_dept(
            issue.get("concerned_department") or "MANUAL_REVIEW"
        )

        # --------------------------------------
        # MUNICIPAL CORPORATION LUDHIANA
        # Group according to zone
        # --------------------------------------
        if is_mcl_department(dept):

            zone = get_zone(issue.get("locality"))

            zone_groups.setdefault(zone, []).append(issue)

        # --------------------------------------
        # TRAFFIC POLICE / HEALTH
        # Group according to department
        # --------------------------------------
        else:

            if dept not in DEPARTMENT_EMAILS:
                skipped.append(issue)
                continue

            dept_groups.setdefault(dept, []).append(issue)

    # ==========================================
    # CONNECT TO GMAIL SMTP — ONLY ONCE
    # ==========================================
    try:

        print("\n🔌 Connecting to Gmail SMTP...")

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        )

        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        print("✅ Gmail SMTP connected and logged in.")

    except Exception as e:

        print(f"❌ SMTP Connection Error: {e}")
        return

    # ==========================================
    # TRACK SUCCESSFULLY REPORTED ISSUES
    # ==========================================
    reported_ids = []

    # ==========================================
    # SEND MCL REPORTS — ZONE WISE
    # ==========================================
    for zone, zone_issues in zone_groups.items():

        to_email = ZONE_EMAILS.get(zone)

        if not to_email:

            skipped.extend(zone_issues)

            print(
                f"\n⚠️ No email configured for {zone}. "
                f"Skipping {len(zone_issues)} issue(s)."
            )

            continue

        subject = (
            f"[Civic Alert] {len(zone_issues)} Issue(s) — "
            f"Municipal Corporation Ludhiana ({zone}) — "
            f"{datetime.now().strftime('%d %b %Y')}"
        )

        print(
            f"\n  📧 Municipal Corporation Ludhiana ({zone})"
        )
        print(f"     To      : {to_email}")
        print(f"     Issues  : {len(zone_issues)}")

        body = build_email_text(
            f"Municipal Corporation Ludhiana ({zone})",
            zone_issues
        )

        msg = MIMEText(
            body,
            "plain",
            "utf-8"
        )

        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        try:

            server.send_message(msg)

            print("     Status  : ✅ Delivered")

            # Mark every issue in this email as successfully sent
            for issue in zone_issues:

                reported_ids.append(issue["id"])

                log_email(
                    issue["id"],
                    to_email,
                    subject,
                    "sent"
                )

        except Exception as e:

            print(
                f"     Status  : ❌ Delivery failed: {e}"
            )

            # Log failure, but DO NOT mark as sent
            for issue in zone_issues:

                log_email(
                    issue["id"],
                    to_email,
                    subject,
                    f"failed: {str(e)}"
                )

    # ==========================================
    # SEND TRAFFIC / HEALTH REPORTS
    # ==========================================
    for dept, dept_issues in dept_groups.items():

        to_email = DEPARTMENT_EMAILS.get(dept)

        if not to_email:

            skipped.extend(dept_issues)

            print(
                f"\n⚠️ No email configured for {dept}. "
                f"Skipping {len(dept_issues)} issue(s)."
            )

            continue

        subject = (
            f"[Civic Alert] {len(dept_issues)} Issue(s) — "
            f"{dept} — "
            f"{datetime.now().strftime('%d %b %Y')}"
        )

        print(f"\n  📧 {dept}")
        print(f"     To      : {to_email}")
        print(f"     Issues  : {len(dept_issues)}")

        body = build_email_text(
            dept,
            dept_issues
        )

        msg = MIMEText(
            body,
            "plain",
            "utf-8"
        )

        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        try:

            server.send_message(msg)

            print("     Status  : ✅ Delivered")

            # Mark every issue in this email as successfully sent
            for issue in dept_issues:

                reported_ids.append(issue["id"])

                log_email(
                    issue["id"],
                    to_email,
                    subject,
                    "sent"
                )

        except Exception as e:

            print(
                f"     Status  : ❌ Delivery failed: {e}"
            )

            # Log failure, but DO NOT mark as sent
            for issue in dept_issues:

                log_email(
                    issue["id"],
                    to_email,
                    subject,
                    f"failed: {str(e)}"
                )

    # ==========================================
    # CLOSE SMTP CONNECTION — ONLY ONCE
    # ==========================================
    try:
        server.quit()
        print("\n🔌 SMTP connection closed.")

    except Exception as e:
        print(f"\n⚠️ SMTP close warning: {e}")

    # ==========================================
    # FINAL REPORT
    # ==========================================
    emails_sent = (
        len(zone_groups) +
        len(dept_groups)
    )

    print(f"\n{'═'*55}")
    print("  Report Complete")
    print(f"  Emails sent       : {emails_sent}")
    print(f"  Issues reported   : {len(reported_ids)}")
    print(f"  Skipped (no email): {len(skipped)}")

    if skipped:

        print("\n  Skipped departments:")

        for d in sorted(
            {
                i["concerned_department"]
                for i in skipped
            }
        ):
            print(f"    — {d}")

    print(f"{'═'*55}\n")


def send_all_reports():
    """Wrapper function to preserve compatibility with main.py pipeline engine."""
    run_report()

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    send_all_reports()