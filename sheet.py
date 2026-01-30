import os
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ================= CONFIG =================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_ID = os.getenv("SHEET_ID")
PROFILE_SHEET_ID = os.getenv("PROFILE_SHEET_ID")
PROFILE_TAB_NAME = "Profiles"
PRIMARY_FIELD = "Discord ID"

# ================= AUTH =================
creds = Credentials.from_service_account_info(
    json.loads(os.getenv("GOOGLE_CREDS_JSON")),
    scopes=SCOPES
)

client = gspread.authorize(creds)

# ================= CORE FUNCTIONS =================
def find_user_row(discord_id: str):
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        rows = sheet.get_all_values()

        if not rows:
            return None, None, None

        header = rows[0]
        if PRIMARY_FIELD not in header:
            print("[SHEET ERROR] Discord ID column missing")
            return None, None, None

        idx = header.index(PRIMARY_FIELD)

        for row_num, row in enumerate(rows[1:], start=2):
            if len(row) > idx and row[idx].strip() == discord_id:
                return row_num, header, row

    except Exception as e:
        print("[FIND USER ERROR]", e)

    return None, None, None


def update_role_assigned(row_number: int):
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        sheet.update(f"N{row_number}", "TRUE")
    except Exception as e:
        print("[ROLE UPDATE ERROR]", e)


def update_ticket_opened(row_number: int):
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        sheet.update(f"O{row_number}", "TRUE")
    except Exception as e:
        print("[TICKET UPDATE ERROR]", e)


def update_profile_sheet(member, row):
    try:
        sheet = client.open_by_key(PROFILE_SHEET_ID)
        tab = sheet.worksheet(PROFILE_TAB_NAME)

        discord_id = row[0]
        product = row[5]
        status = row[8]

        final_row = [
            discord_id,
            member.name,
            member.display_name,
            "N/A",
            product,
            datetime.datetime.now().strftime("%Y-%m-%d"),
            status
        ]

        existing = tab.col_values(1)
        if discord_id in existing:
            idx = existing.index(discord_id) + 1
            tab.update(f"A{idx}:G{idx}", [final_row])
        else:
            tab.append_row(final_row)

    except Exception as e:
        print("[PROFILE UPDATE ERROR]", e)
