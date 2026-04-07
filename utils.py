import os
import logging
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------
#  LOGGING
# -----------------------------
def setup_logging():
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Aplikacija pokrenuta.")


# -----------------------------
#  BOATS MANAGEMENT
# -----------------------------
def get_boats():
    """Vraća listu plovila (foldera u uploads/)."""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    boats = [
        name for name in os.listdir("uploads")
        if os.path.isdir(os.path.join("uploads", name))
    ]

    return sorted(boats)


def create_new_boat(name):
    """Kreira novi folder za plovilo."""
    path = os.path.join("uploads", name)
    os.makedirs(path, exist_ok=True)


# -----------------------------
#  SERVICE INFO CALCULATIONS
# -----------------------------
def calculate_service_info(df, inicijalni):
    """
    Pravila:
    - Ako inicijalni = 0 → prvi servis na 20h
    - Nakon prvog servisa → svakih 100h
    - Ako inicijalni > 0 → prvi servis na inicijalni + 100h
    """

    # Ako nema zapisa uopće
    if df.empty:
        if inicijalni == 0:
            return 0, 20, 20
        else:
            return inicijalni, inicijalni + 100, 100

    # Ako postoje zapisi, tražimo zadnji servis
    df_servis = df[df["vrsta_unosa"] == "Servis"]

    # Ako nema servisa, ali ima drugih zapisa
    if df_servis.empty:
        trenutni = int(df.iloc[0]["trenutni_radni_sati"])

        if inicijalni == 0:
            sljedeci = 20
        else:
            sljedeci = inicijalni + 100

        do_servisa = sljedeci - trenutni
        return inicijalni, sljedeci, do_servisa

    # Ako postoje servisi
    zadnji = int(df_servis.iloc[0]["trenutni_radni_sati"])
    sljedeci = zadnji + 100

    trenutni = int(df.iloc[0]["trenutni_radni_sati"])
    do_servisa = sljedeci - trenutni

    return zadnji, sljedeci, do_servisa


# -----------------------------
#  TECHNICAL INSPECTION INFO
# -----------------------------
def calculate_tech_info(df):
    """
    Izračun tehničkog pregleda.
    Očekuje DataFrame iz SQLite-a.
    """

    df_tech = df[df["vrsta_unosa"] == "Tehnički pregled"]

    if df_tech.empty:
        return None, None

    last_date_str = df_tech.iloc[0]["datum"]
    last_date = datetime.strptime(last_date_str, "%d.%m.%Y")

    expiry_date = last_date + timedelta(days=365)
    days_left = (expiry_date - datetime.now()).days

    return expiry_date, days_left
