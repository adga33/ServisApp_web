import pandas as pd
from datetime import datetime, timedelta
import os
import shutil

EXCEL_FILE = "servisi.xlsx"

COLUMNS = [
    "datum",
    "trenutni radni sati",
    "servis rađen na",
    "očekivani servis",
    "do servisa",
    "vrsta unosa",
    "Napomena",
]

def get_boats():
    if not os.path.exists(EXCEL_FILE):
        return []
    return pd.ExcelFile(EXCEL_FILE).sheet_names

def create_new_boat(name: str):
    df = pd.DataFrame(columns=COLUMNS)

    mode = "w" if not os.path.exists(EXCEL_FILE) else "a"

    with pd.ExcelWriter(EXCEL_FILE, mode=mode, if_sheet_exists="new") as writer:
        df.to_excel(writer, sheet_name=name, index=False)

def load_sheet(sheet):
    return pd.read_excel(EXCEL_FILE, sheet_name=sheet)

def save_sheet(sheet, df):
    with pd.ExcelWriter(EXCEL_FILE, mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=sheet, index=False)

def append_row(sheet, data):
    df = load_sheet(sheet)
    df.loc[len(df)] = data
    save_sheet(sheet, df)

def backup_excel():
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    shutil.copy(EXCEL_FILE, backup_name)
    return backup_name

def calculate_service_info(df, inicijalni):
    df_servisi = df[df["vrsta unosa"] == "Servis"]

    # izračun prvog servisa
    prvi_servis = calculate_first_service(inicijalni)

    if df_servisi.empty:
        zadnji = 0
        sljedeci = prvi_servis
    else:
        zadnji = int(df_servisi.iloc[-1]["servis rađen na"])
        broj_servisa = len(df_servisi)
        sljedeci = prvi_servis + broj_servisa * 100

    try:
        trenutni = int(df.iloc[-1]["trenutni radni sati"])
    except:
        trenutni = 0

    do_servisa = sljedeci - trenutni
    return zadnji, sljedeci, do_servisa

def calculate_tech_info(df):
    df_tech = df[df["vrsta unosa"] == "Tehnički pregled"]

    if df_tech.empty:
        return None, None

    zadnji = df_tech.iloc[-1]["datum"]
    zadnji_date = datetime.strptime(zadnji, "%d.%m.%Y")
    istek = zadnji_date + timedelta(days=365 * 2)
    dana = (istek - datetime.now()).days

    return istek, dana
def load_sheet(sheet):
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)

    # ⬇️ OVO DODAJ — ako sheet nema kolone, dodaj ih
    if df.empty or list(df.columns) != COLUMNS:
        df = pd.DataFrame(columns=COLUMNS)

    return df
def calculate_first_service(inicijalni):
    if inicijalni == 0:
        return 20
    return inicijalni + 10
import logging
import os

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", size=14)
        self.cell(0, 10, "Servisni Izvještaj", ln=True, align="C")

def create_pdf(data, filename="servisi_report.pdf"):
    pdf = PDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    for key, value in data.items():
        pdf.cell(0, 10, f"{key}: {value}", ln=True)

    pdf.output(filename)

