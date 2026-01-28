import json
import os
import subprocess

from dotenv import load_dotenv

from CEACStatusBot import (
    EmailNotificationHandle,
    NotificationManager,
    TelegramNotificationHandle,
)

# --- Load .env if present, else fallback to system env ---
if os.path.exists(".env"):
    load_dotenv(dotenv_path=".env")  # loads into os.environ
else:
    print(".env not found, using system environment only")


def download_artifact():
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/artifacts"],
            capture_output=True,
            text=True,
        )
        artifacts = json.loads(result.stdout)
        artifact_exists = any(artifact["name"] == "status-artifact" for artifact in artifacts["artifacts"])

        if artifact_exists:
            subprocess.run(["gh", "run", "download", "--name", "status-artifact"], check=True)
        else:
            with open("status_record.json", "w") as file:
                json.dump({"statuses": []}, file)
    except Exception as e:
        print(f"Error downloading artifact: {e}")


# --- Read env vars ---
GH_TOKEN = os.getenv("GH_TOKEN")
if not GH_TOKEN:
    print("GH_TOKEN not found")

if not os.path.exists("status_record.json"):
    download_artifact()

try:
    NUMBER = os.environ["NUMBER"]
    PASSPORT_NUMBER = os.environ["PASSPORT_NUMBER"]
    SURNAME = os.environ["SURNAME"]

    notificationManager = NotificationManager(
        number=NUMBER,
        passport_number=PASSPORT_NUMBER,
        surname=SURNAME
    )
except KeyError as e:
    raise RuntimeError(f"Missing required env var: {e}") from e


# --- Optional: Email notifications ---
FROM = os.getenv("FROM")         # Gmail address
TO = os.getenv("TO")             # Recipients separated by "|"
PASSWORD = os.getenv("PASSWORD") # Gmail app password
SMTP = os.getenv("SMTP")         # Optional, defaults to smtp.gmail.com

if FROM and TO and PASSWORD:
    emailNotificationHandle = EmailNotificationHandle(FROM, TO, PASSWORD, SMTP or "smtp.gmail.com")
    notificationManager.addHandle(emailNotificationHandle)
else:
    print("Email notification config missing or incomplete")


# --- Optional: Telegram notifications ---
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

if BOT_TOKEN and CHAT_ID:
    tgNotif = TelegramNotificationHandle(BOT_TOKEN, CHAT_ID)
    notificationManager.addHandle(tgNotif)
else:
    print("Telegram bot notification config missing or incomplete")


# --- Send notifications ---
notificationManager.send()


# --- TEST EMAIL (will send once, delete this block after confirmation) ---
print("Debug: Email config:")
print("FROM:", FROM)
print("TO:", TO)
print("PASSWORD loaded:", bool(PASSWORD))
print("SMTP:", SMTP or "smtp.gmail.com")

if FROM and TO and PASSWORD:
    print("Sending test email...")
    emailNotificationHandle.send({
        "application_num_origin": "TEST",
        "status": "Test Email",
        "description": "This is a test email from CEACStatusBot",
        "visa_type": "TEST",
        "application_num": "TEST123",
        "case_created": None,
        "case_last_updated": None
    })
else:
    print("Test email not sent because configuration is incomplete.")
