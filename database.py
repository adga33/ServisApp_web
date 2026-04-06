import pandas as pd
import os
from tkinter import messagebox
from config import EXCEL_FILE, SHEETS, COLUMNS


def ensure_excel_exists():
    if not os.path.exists(EXCEL_FILE):
        writer = pd.ExcelWriter(EXCEL_FILE, engine="openpyxl")
        for sheet in SHEETS:
            df = pd.DataFrame(columns=COLUMNS)
            df.to_excel(writer, sheet_name=sheet, index=False)
        writer.save()


def load_sheet(sheet):
    ensure_excel_exists()
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
        return df
    except Exception as e:
        messagebox.showerror("Greška", str(e))
        return pd.DataFrame(columns=COLUMNS)


def append_row(sheet, data):
    df = load_sheet(sheet)
    df.loc[len(df)] = data
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
    except Exception as e:
        messagebox.showerror("Greška", str(e))


def backup_excel():
    import shutil
    try:
        shutil.copy(EXCEL_FILE, "backup_excel_baza.xlsx")
        messagebox.showinfo("Backup", "Backup uspješno napravljen.")
    except Exception as e:
        messagebox.showerror("Greška", str(e))
import shutil
import datetime

def backup_excel():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy("servisi.xlsx", f"backup_excel_baza_{timestamp}.xlsx")
import os
import time

def cleanup_old_backups(days=30):
    now = time.time()
    for file in os.listdir():
        if file.startswith("backup_excel_baza_") and file.endswith(".xlsx"):
            if os.stat(file).st_mtime < now - days * 86400:
                os.remove(file)
import pandas as pd
import os

def ensure_excel_exists():
    if not os.path.exists("servisi.xlsx"):
        df = pd.DataFrame(columns=["Datum", "Broj broda", "Opis", "Cijena"])
        df.to_excel("servisi.xlsx", index=False)


