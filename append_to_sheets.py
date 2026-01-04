import os, json
from datetime import datetime
from zoneinfo import ZoneInfo

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SHEET_ID = os.environ["GSHEET_ID"]
TAB_NAME = os.environ.get("GSHEET_TAB", "Historial_usdt_ppal")
VALUE = os.environ["VALUE_USDT"]

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
now = datetime.now(TZ)

fecha = now.strftime("%Y-%m-%d")
hora = now.strftime("%H:%M:%S")

# credenciales por archivo (seteo desde workflow)
creds = Credentials.from_service_account_file(
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)

service = build("sheets", "v4", credentials=creds)

body = {
    "values": [[fecha, hora, float(VALUE)]]
}

# Append al final
service.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range=f"{TAB_NAME}!A:C",
    valueInputOption="USER_ENTERED",
    insertDataOption="INSERT_ROWS",
    body=body,
).execute()

print(f"APPENDED {fecha} {hora} {VALUE} -> {TAB_NAME}")
