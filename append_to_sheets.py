import os
from datetime import datetime
from zoneinfo import ZoneInfo

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SHEET_ID = os.environ["GSHEET_ID"]
TAB_HIST = os.environ.get("GSHEET_TAB", "Historial_usdt_ppal")
TAB_GRAF = "Datos Grafico"

VALUE = os.environ["VALUE_USDT"]

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
now = datetime.now(TZ)

fecha = now.strftime("%Y-%m-%d")
hora = now.strftime("%H:%M:%S")

# Nuevos campos
dia_mes = now.day
anio_mes = now.strftime("%Y-%m")

# credenciales
creds = Credentials.from_service_account_file(
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)

service = build("sheets", "v4", credentials=creds)

# ---------- TABLA HISTORIAL ----------
body_hist = {
    "values": [[fecha, hora, float(VALUE)]]
}

service.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range=f"{TAB_HIST}!A:C",
    valueInputOption="USER_ENTERED",
    insertDataOption="INSERT_ROWS",
    body=body_hist,
).execute()

print(f"APPENDED {fecha} {hora} {VALUE} -> {TAB_HIST}")

# ---------- TABLA DATOS GRAFICO ----------
body_graf = {
    "values": [[fecha, hora, float(VALUE), dia_mes, anio_mes]]
}

service.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range=f"{TAB_GRAF}!A:E",
    valueInputOption="USER_ENTERED",
    insertDataOption="INSERT_ROWS",
    body=body_graf,
).execute()

print(f"APPENDED {fecha} {hora} {VALUE} {dia_mes} {anio_mes} -> {TAB_GRAF}")
