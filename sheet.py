import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = os.getenv("SHEET_ID")
PRIMARY_FIELD = os.getenv("PRIMARY_FIELD", "Discord ID")

def get_sheet_service():
    creds = Credentials.from_service_account_info({
        "type": "service_account",
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL")
    }, scopes=SCOPES)

    return build("sheets", "v4", credentials=creds).spreadsheets()


def find_user_row(discord_id: str):
    service = get_sheet_service()
    result = service.values().get(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A1:Z5000"
    ).execute()

    rows = result.get("values", [])
    if not rows:
        return None, None, None

    header = rows[0]
    if PRIMARY_FIELD not in header:
        return None, None, None

    col_index = header.index(PRIMARY_FIELD)

    for i, row in enumerate(rows[1:], start=2):
        if len(row) > col_index and row[col_index] == discord_id:
            return i, header, row

    return None, None, None


def update_role_assigned(row_number: int):
    service = get_sheet_service()
    service.values().update(
        spreadsheetId=SHEET_ID,
        range=f"Sheet1!N{row_number}",
        valueInputOption="USER_ENTERED",
        body={"values": [["TRUE"]]}
    ).execute()


def update_ticket_opened(row_number: int):
    service = get_sheet_service()
    service.values().update(
        spreadsheetId=SHEET_ID,
        range=f"Sheet1!O{row_number}",
        valueInputOption="USER_ENTERED",
        body={"values": [["TRUE"]]}
    ).execute()

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ⚙️ AUTH & SHEET SERVICE
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
import json
from google.oauth2.service_account import Credentials

creds_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

service = build("sheets", "v4", credentials=creds)

def get_profile(discord_id: str):
    """
    Fetches a profile row by Discord ID from the Profiles tab.
    Returns: dict or None
    """
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=PROFILE_SHEET_ID,
            range=f"{PROFILE_TAB_NAME}!A:F"
        ).execute()

        rows = result.get("values", [])
        if not rows:
            return None

        headers = rows[0]
        for row in rows[1:]:
            row_data = dict(zip(headers, row))
            if row_data.get("DiscordID") == discord_id:
                return row_data

        return None
    except Exception as e:
        print("[SHEET-PROFILE-ERROR]", e)
        return None
# ============= PROFILE FUNCTIONS =============

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

PROFILE_TAB = "Sheet1"  # confirmed by user

def get_profile(discord_id: str):
    try:
        creds = Credentials.from_service_account_info(SERVICE_JSON, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{PROFILE_TAB}!A2:Z999"
        ).execute()

        rows = result.get('values', [])
        purchases = []

        for row in rows:
            row_map = dict(zip(HEADERS, row))
            if row_map.get("Discord ID") == discord_id:
                purchases.append({
                    "product": row_map.get("Product", "Unknown"),
                    "status": row_map.get("Status", "Unknown"),
                    "payment_id": row_map.get("Payment ID", "N/A"),
                    "timestamp": row_map.get("Timestamp", "N/A")
                })

        return purchases

    except Exception as e:
        print("[PROFILE ERROR]", e)
        return None
