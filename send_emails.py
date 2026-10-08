#!/usr/bin/env python3
"""
Recruiter Email Automation Script

Reads recruiter email addresses from a CSV file, attaches a resume PDF,
and sends individual emails via SMTP (or runs in DRY_RUN mode). Includes duplicate
protection, email validation, and logging.
"""

import csv
import datetime
import mimetypes
import os
import re
import smtplib
import sys
import time
from email.message import EmailMessage

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Essential Credentials & Mode (from .env)
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "mahendargoud9866@gmail.com").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
DRY_RUN_RAW = os.getenv("DRY_RUN", "true").strip().lower()
DRY_RUN = DRY_RUN_RAW in ("true", "1", "t", "yes")

# Optional limit for testing (0 = send all)
MAX_EMAILS = int(os.getenv("MAX_EMAILS", "0"))

# Default Application Settings (Can optionally be overridden via .env)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "").strip() or SMTP_USERNAME
SENDER_NAME = os.getenv("SENDER_NAME", "Mahendar Bathini").strip()
CSV_PATH = os.getenv("CSV_PATH", "recruiters.csv").strip()
RESUME_PATH = os.getenv("RESUME_PATH", "resume.pdf").strip()
SEND_DELAY_SECONDS = float(os.getenv("SEND_DELAY_SECONDS", "10"))

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "email_log.csv")
EMAIL_TEMPLATE_FILE = "email_template.txt"
EMAIL_SUBJECT = "AI/ML & Generative AI Engineer – 2+ Years Experience"

# Email regex validation pattern
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email_address(email: str) -> bool:
    """Validate email address format using standard regex."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email))


def get_previously_sent_emails(log_path: str) -> set:
    """Read existing log file and return a set of emails that have been 'sent'."""
    sent_emails = set()
    if not os.path.exists(log_path):
        return sent_emails

    try:
        with open(log_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "sent" and row.get("email"):
                    sent_emails.add(row.get("email").strip().lower())
    except Exception as e:
        print(f"[WARNING] Could not read existing log file '{log_path}': {e}")

    return sent_emails


def initialize_log_file(log_path: str) -> None:
    """Ensure log directory and log CSV file exist with proper headers."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if not os.path.exists(log_path):
        with open(log_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "status", "timestamp", "error"])


def append_log_entry(log_path: str, email: str, status: str, error: str = "") -> None:
    """Append a single record entry to the CSV log file."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(log_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([email, status, timestamp, error])


def load_email_body() -> str:
    """Load the email template body from email_template.txt."""
    if os.path.exists(EMAIL_TEMPLATE_FILE):
        with open(EMAIL_TEMPLATE_FILE, mode="r", encoding="utf-8") as f:
            return f.read().strip()
    return (
        "Hi,\n\n"
        "I hope you’re doing well.\n\n"
        "I’m currently exploring new opportunities in AI/ML and Generative AI. "
        "I have around 2+ years of full-time experience as an AI Engineer, along with 8 months of AI/ML internship experience.\n\n"
        "My recent work has focused on RAG, LLM applications, LangChain, LangGraph, AWS Bedrock, vector databases, and Agentic AI.\n\n"
        "I’ve attached my resume for your reference. If there are any suitable openings matching my profile, "
        "I’d be grateful if you could consider my application.\n\n"
        "Thank you for your time, and I’d be happy to connect and discuss any relevant opportunities.\n\n"
        "Best regards,\n"
        "Mahendar Bathini\n"
        "Hyderabad, Telangana\n"
        "mahendargoud9866@gmail.com\n"
        "linkedin.com/in/mahendar-bathini"
    )


def build_email_message(
    recipient: str,
    subject: str,
    body: str,
    sender_name: str,
    sender_email: str,
    resume_path: str,
    resume_data: bytes,
) -> EmailMessage:
    """Construct a MIME EmailMessage object with resume attachment."""
    msg = EmailMessage()
    msg["Subject"] = subject
    if sender_name:
        msg["From"] = f"{sender_name} <{sender_email}>"
    else:
        msg["From"] = sender_email
    msg["To"] = recipient
    msg.set_content(body)

    filename = os.path.basename(resume_path)
    ctype, encoding = mimetypes.guess_type(resume_path)
    if ctype is None or encoding is not None:
        ctype = "application/pdf"
    maintype, subtype = ctype.split("/", 1)

    msg.add_attachment(
        resume_data, maintype=maintype, subtype=subtype, filename=filename
    )
    return msg


def main():
    print("==========================================")
    print("  Recruiter Email Automation Application  ")
    print("==========================================")

    # 1. Check Resume File
    if not os.path.exists(RESUME_PATH):
        print(f"\n[FATAL ERROR] Resume file '{RESUME_PATH}' does not exist.")
        print("Please place your resume PDF file in the project folder as 'resume.pdf'.")
        sys.exit(1)

    try:
        with open(RESUME_PATH, "rb") as f:
            resume_data = f.read()
    except Exception as e:
        print(f"\n[FATAL ERROR] Failed to read resume file '{RESUME_PATH}': {e}")
        sys.exit(1)

    print(f"[OK] Resume file verified: '{RESUME_PATH}' ({len(resume_data)} bytes)")

    # 2. Check CSV File
    if not os.path.exists(CSV_PATH):
        print(f"\n[FATAL ERROR] Recruiter CSV file '{CSV_PATH}' does not exist.")
        print("Please create 'recruiters.csv' with an 'email' column header.")
        sys.exit(1)

    # 3. Read and Parse CSV File
    csv_records = []
    try:
        with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "email" not in [col.strip().lower() for col in reader.fieldnames]:
                print(f"\n[FATAL ERROR] CSV file '{CSV_PATH}' is missing required 'email' column header.")
                sys.exit(1)
            
            email_key = next(col for col in reader.fieldnames if col.strip().lower() == "email")

            for row in reader:
                raw_email = row.get(email_key, "")
                cleaned_email = raw_email.strip() if raw_email else ""
                csv_records.append(cleaned_email)
    except Exception as e:
        print(f"\n[FATAL ERROR] Failed to read CSV file '{CSV_PATH}': {e}")
        sys.exit(1)

    total_csv_records = len(csv_records)
    print(f"[OK] Read {total_csv_records} record(s) from '{CSV_PATH}'.")

    # 4. Initialize Logging & Previous Sent Cache
    initialize_log_file(LOG_FILE)
    previously_sent = get_previously_sent_emails(LOG_FILE)
    if previously_sent:
        print(f"[INFO] Found {len(previously_sent)} previously sent email address(es) in '{LOG_FILE}'.")

    # 5. Load Email Body Template
    email_body = load_email_body()

    # 6. Deduplicate and Validate Candidates
    processed_emails = []
    seen_in_current_csv = set()

    for idx, email in enumerate(csv_records, start=1):
        if not email:
            processed_emails.append({
                "email": f"<empty_row_{idx}>",
                "status": "skipped",
                "error": "Empty email field",
                "valid": False
            })
            continue

        email_lower = email.lower()
        if email_lower in seen_in_current_csv:
            processed_emails.append({
                "email": email,
                "status": "skipped_duplicate",
                "error": "Duplicate entry within CSV file",
                "valid": False
            })
            continue

        seen_in_current_csv.add(email_lower)

        if not validate_email_address(email):
            processed_emails.append({
                "email": email,
                "status": "skipped",
                "error": "Invalid email address format",
                "valid": False
            })
            continue

        if email_lower in previously_sent:
            processed_emails.append({
                "email": email,
                "status": "skipped_duplicate",
                "error": "Already sent in a previous run",
                "valid": False
            })
            continue

        processed_emails.append({
            "email": email,
            "status": "pending",
            "error": "",
            "valid": True
        })

    valid_unique_count = sum(1 for item in processed_emails if item["valid"])

    # 7. Print Mode Status
    print("\n------------------------------------------")
    if DRY_RUN:
        print("MODE: [DRY RUN] (No actual emails will be sent)")
    else:
        print("MODE: [LIVE] (Emails WILL be sent via SMTP)")
    print("------------------------------------------\n")

    sendable_items = [item for item in processed_emails if item["valid"]]
    non_sendable_items = [item for item in processed_emails if not item["valid"]]

    if MAX_EMAILS > 0 and len(sendable_items) > MAX_EMAILS:
        print(f"[LIMIT] MAX_EMAILS={MAX_EMAILS} set. Will process only the first {MAX_EMAILS} sendable candidate(s).\n")
        sendable_items = sendable_items[:MAX_EMAILS]

    # 8. Establish SMTP Connection if LIVE mode
    smtp_server = None
    if not DRY_RUN:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print("[FATAL ERROR] SMTP_USERNAME and SMTP_PASSWORD must be configured in .env for LIVE mode.")
            sys.exit(1)

        print(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT} ...")
        try:
            smtp_server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            smtp_server.starttls()
            smtp_server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print(f"[OK] Authenticated successfully as '{SMTP_USERNAME}'.")
        except Exception as e:
            print(f"[FATAL ERROR] Failed to connect/authenticate with SMTP server: {e}")
            sys.exit(1)

    # 9. Processing Loop
    counts = {
        "total_csv": total_csv_records,
        "valid_unique": valid_unique_count,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "dry_run": 0
    }

    for item in non_sendable_items:
        email = item["email"]
        status = item["status"]
        error = item["error"]
        append_log_entry(LOG_FILE, email, status, error)
        counts["skipped"] += 1
        print(f"[-] {email:<32} | Status: {status:<18} | Note: {error}")

    num_sendable = len(sendable_items)
    for index, item in enumerate(sendable_items, start=1):
        email = item["email"]

        if DRY_RUN:
            status = "dry_run"
            error = ""
            append_log_entry(LOG_FILE, email, status, error)
            counts["dry_run"] += 1
            print(f"[{index}/{num_sendable}] DRY_RUN -> Recipient: {email}")
            print(f"      Subject: '{EMAIL_SUBJECT}'")
            print(f"      Attachment: '{RESUME_PATH}' ({len(resume_data)} bytes)")
            print(f"      Status logged as 'dry_run'.\n")

        else:
            try:
                msg = build_email_message(
                    recipient=email,
                    subject=EMAIL_SUBJECT,
                    body=email_body,
                    sender_name=SENDER_NAME,
                    sender_email=SENDER_EMAIL,
                    resume_path=RESUME_PATH,
                    resume_data=resume_data
                )
                smtp_server.send_message(msg)
                status = "sent"
                error = ""
                append_log_entry(LOG_FILE, email, status, error)
                counts["sent"] += 1
                print(f"[{index}/{num_sendable}] SENT -> {email}")

                if index < num_sendable and SEND_DELAY_SECONDS > 0:
                    print(f"      Waiting {SEND_DELAY_SECONDS} seconds before next send...")
                    time.sleep(SEND_DELAY_SECONDS)

            except Exception as e:
                status = "failed"
                error_msg = str(e).replace("\n", " ")
                append_log_entry(LOG_FILE, email, status, error_msg)
                counts["failed"] += 1
                print(f"[{index}/{num_sendable}] FAILED -> {email} | Error: {error_msg}")

    # 10. Clean up SMTP Connection
    if smtp_server:
        try:
            smtp_server.quit()
            print("\n[OK] SMTP connection closed cleanly.")
        except Exception:
            pass

    # 11. Final Summary Report
    print("\n==================================")
    print("Email Sending Summary")
    print("==================================")
    print(f"Total CSV records:       {counts['total_csv']}")
    print(f"Valid unique emails:     {counts['valid_unique']}")
    print(f"Successfully sent:       {counts['sent']}")
    print(f"Failed:                  {counts['failed']}")
    print(f"Skipped:                 {counts['skipped']}")
    print(f"Dry run:                 {counts['dry_run']}")
    print("==================================\n")


if __name__ == "__main__":
    main()
