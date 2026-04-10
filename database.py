import sqlite3
from datetime import datetime

DB_PATH = "database.db"


def init_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tablica plovila
    c.execute("""
        CREATE TABLE IF NOT EXISTS plovila (
            id TEXT PRIMARY KEY,
            registracija TEXT,
            inicijalni_sati INTEGER
        )
    """)

    # Tablica servisnih zapisa
    c.execute("""
        CREATE TABLE IF NOT EXISTS zapisi (
            id TEXT PRIMARY KEY,
            plovilo_id TEXT,
            datum TEXT,
            trenutni_sati INTEGER,
            servis_raden_na INTEGER,
            ocekivani_servis INTEGER,
            do_servisa INTEGER,
            vrsta_unosa TEXT,
            napomena TEXT,
            attachments TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- PLovila ----------------

def add_plovilo(registracija, inicijalni_sati):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    plovilo_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    c.execute("""
        INSERT INTO plovila (id, registracija, inicijalni_sati)
        VALUES (?, ?, ?)
    """, (plovilo_id, registracija, inicijalni_sati))

    conn.commit()
    conn.close()


def get_plovila():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("SELECT id, registracija, inicijalni_sati FROM plovila").fetchall()
    conn.close()
    return rows


def get_plovilo(plovilo_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute("SELECT id, registracija, inicijalni_sati FROM plovila WHERE id = ?", (plovilo_id,)).fetchone()
    conn.close()
    return row


# ---------------- Zapisi ----------------

def add_zapis(plovilo_id, datum, trenutni_sati, servis_raden_na,
              ocekivani_servis, do_servisa, vrsta_unosa, napomena, attachments):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    zapis_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    c.execute("""
        INSERT INTO zapisi (
            id, plovilo_id, datum, trenutni_sati, servis_raden_na,
            ocekivani_servis, do_servisa, vrsta_unosa, napomena, attachments
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (zapis_id, plovilo_id, datum, trenutni_sati, servis_raden_na,
          ocekivani_servis, do_servisa, vrsta_unosa, napomena, attachments))

    conn.commit()
    conn.close()


def get_zapisi(plovilo_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("""
        SELECT id, datum, trenutni_sati, vrsta_unosa, do_servisa
        FROM zapisi
        WHERE plovilo_id = ?
        ORDER BY datum DESC
    """, (plovilo_id,)).fetchall()
    conn.close()
    return rows
