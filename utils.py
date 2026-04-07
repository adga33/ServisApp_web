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
    Izračun zadnjeg servisa, sljedećeg servisa i preostalog vremena.
    Očekuje DataFrame iz SQLite-a.
    """

    if df.empty:
        return inicijalni, inicijalni + 100, 100

    # Zadnji servis
    df_servis = df[df["vrsta_unosa"] == "Servis"]

    if df_servis.empty:
        zadnji = inicijalni
    else:
        zadnji = int(df_servis.iloc[0]["trenutni_radni_sati"])

    # Sljedeći servis svakih 100h
    sljedeci = zadnji + 100

    # Preostalo
    if not df.empty:
        trenutni = int(df.iloc[0]["trenutni_radni_sati"])
    else:
        trenutni = inicijalni

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
