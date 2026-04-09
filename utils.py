import os
import logging
from datetime import datetime, timedelta

# -------------------------------------------------
# LOGGING
# -------------------------------------------------

def setup_logging():
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Aplikacija pokrenuta.")

# -------------------------------------------------
# DOHVAT PLOVILA (folderi u uploads/)
# -------------------------------------------------

def get_boats():
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    boats = [
        name for name in os.listdir("uploads")
        if os.path.isdir(os.path.join("uploads", name))
    ]

    return sorted(boats)

# -------------------------------------------------
# TEHNIČKI PREGLED – izračun
# -------------------------------------------------

def calculate_tech_info(df):
    """
    Traži zadnji tehnički pregled i računa koliko dana vrijedi.
    Pretpostavka: tehnički vrijedi 365 dana.
    """

    if df.empty:
        return None, None

    # Filtriraj samo tehničke preglede
    tech_rows = df[df["vrsta_unosa"] == "Tehnički pregled"]

    if tech_rows.empty:
        return None, None

    # Najnoviji tehnički
    latest = tech_rows.sort_values("datum", ascending=False).iloc[0]

    try:
        expiry_date = datetime.strptime(latest["datum"], "%d.%m.%Y") + timedelta(days=365)
        days_left = (expiry_date - datetime.today()).days
        return expiry_date, days_left
    except:
        return None, None
