# Recruiter Email Automation

A robust, minimal Python application designed to send personalized job application emails with your PDF resume attached to recruiters listed in a CSV file.

Features:
- **Individual Emailing**: Sends separate emails to each recruiter (no CC or BCC).
- **Dry-Run Safety**: Simulates execution and logs `dry_run` status without connecting to or sending via SMTP by default.
- **Duplicate Protection**: Automatically skips emails already logged as `sent` in `logs/email_log.csv` and removes duplicate rows within the CSV.
- **Detailed Logging**: Logs outcome (`sent`, `failed`, `skipped`, `dry_run`, `skipped_duplicate`) with ISO timestamps and error details.
- **Secure Configuration**: Uses environment variables via `python-dotenv` and never logs SMTP credentials.

---

## Directory Structure

```text
recruiter-email-automation/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── recruiters.csv
├── resume.pdf
├── send_emails.py
├── email_template.txt
└── logs/
    └── email_log.csv
```

---

## 1. Setup Virtual Environment

Navigate into the project directory and create a virtual environment.

### Windows (PowerShell)
```powershell
cd recruiter-email-automation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)
```cmd
cd recruiter-email-automation
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### macOS / Linux
```bash
cd recruiter-email-automation
python3 -m venv .venv
source .venv/bin/activate
```

---

## 2. Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

*(Only `python-dotenv` is required; standard Python modules `smtplib`, `email`, `csv`, `re` are built-in.)*

---

## 3. Configure `.env`

Copy `.env.example` to `.env`:

### Windows
```cmd
copy .env.example .env
```

### macOS / Linux
```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
SENDER_NAME=Mahendar Bathini

CSV_PATH=recruiters.csv
RESUME_PATH=resume.pdf

SEND_DELAY_SECONDS=10
DRY_RUN=true
```

> [!WARNING]
> Never commit `.env` to Git. Keep `DRY_RUN=true` until you are ready to send real emails.

---

## 4. Prepare `recruiters.csv`

Create or update `recruiters.csv` with a single `email` header column:

```csv
email
recruiter1@company.com
recruiter2@company.com
recruiter3@company.com
```

The script will automatically trim whitespace, validate email syntax, and skip empty or duplicate addresses.

---

## 5. Prepare `resume.pdf`

Place your resume PDF file in the project folder and make sure `RESUME_PATH` in `.env` matches the file name (e.g., `resume.pdf`).

The script verifies that the file exists before starting.

---

## 6. How to Run in Dry-Run Mode

Ensure `DRY_RUN=true` in `.env`. Run the script:

```bash
python send_emails.py
```

In dry-run mode, the application will:
- Validate your resume and CSV.
- Deduplicate emails and check previous logs.
- Print recipient details and attachment verification to the console.
- Write `dry_run` records to `logs/email_log.csv`.
- **Not** contact the SMTP server.

---

## 7. How to Enable Real Email Sending

1. Set `DRY_RUN=false` in `.env`.
2. Ensure your `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SENDER_EMAIL` are configured in `.env`.
3. Run the automation:

```bash
python send_emails.py
```

Emails will be sent individually with a delay of `SEND_DELAY_SECONDS` between sends.

---

## 8. Duplicate Protection

Duplicate protection works in two layers:
1. **Intra-CSV Deduplication**: Duplicate email addresses in `recruiters.csv` are skipped during execution.
2. **Historical Log Checking**: Before processing, `send_emails.py` reads `logs/email_log.csv`. Any recruiter email already recorded with a `sent` status will be skipped and logged as `skipped_duplicate`.

This ensures that re-running the script will not result in sending duplicate emails to the same recruiter.

---

## 9. Email Logs

All actions are logged in `logs/email_log.csv`:

```csv
email,status,timestamp,error
recruiter1@company.com,sent,2026-10-08T10:30:00Z,
recruiter2@company.com,failed,2026-10-08T10:30:15Z,SMTP authentication failed
recruiter3@company.com,skipped_duplicate,2026-10-08T10:30:15Z,Already sent in a previous run
```

Possible statuses:
- `sent`: Email sent successfully.
- `failed`: SMTP delivery or network error.
- `skipped`: Empty or invalid email address.
- `skipped_duplicate`: Duplicate email in CSV or already sent previously.
- `dry_run`: Action logged during dry-run mode.

---

## 10. Troubleshooting SMTP Authentication

If using Gmail:
1. Enable **2-Step Verification** in your Google Account.
2. Generate an **App Password**:
   - Go to Google Account Security -> 2-Step Verification -> App Passwords.
   - Generate a key for "Mail" / "Custom Name".
3. Use your full Gmail address as `SMTP_USERNAME` and the generated 16-character App Password as `SMTP_PASSWORD`.
4. Do **not** use your primary Gmail login password.

If using another provider (Outlook, Yahoo, custom domain):
- Verify `SMTP_HOST` (e.g., `smtp.office365.com` for Outlook) and `SMTP_PORT` (usually `587` for STARTTLS or `465` for SSL).
