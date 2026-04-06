EXCEL_FILE = "excel_baza.xlsx"

SHEETS = [
    "RH198-SB", "RH194-SB", "RH199-SB", "RH187-SB",
    "RH75-VK", "RH195-SB", "RH88-VK", "RH7-SK"
]

COLUMNS = [
    "datum",
    "trenutni radni sati",
    "servis rađen na",
    "očekivani servis",
    "do servisa",
"vrsta unosa",

    "Napomena"
]

ADMIN_LOZINKA = "admin123"

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "servisi.xlsx")
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
from config import EXCEL_PATH
APP_VERSION = "v1.0.0"

