import os
import sqlite3
from datetime import datetime
import shutil

DB_PATH = "database.db"

# -------------------------------------------------
# INIT TABLES
# -------------------------------------------------

def init_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS zapisi (
            id TEXT PRIMARY KEY,
            plovilo TEXT,
            datum TEXT,
            trenutni_radni_sati INTEGER,
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

# -------------------------------------------------
# MIGRATION (ako postoje stare verzije)
# -------------------------------------------------

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Dodaj stupce ako nedostaju
    columns = [row[1] for row in c.execute("PRAGMA table_info(zapisi)").fetchall()]

    required = {
        "servis_raden_na": "INTEGER",
        "ocekivani_servis": "INTEGER",
        "do_servisa": "INTEGER",
        "attachments": "TEXT"
    }

    for col, typ in required.items():
        if col not in columns:
            c.execute(f"ALTER TABLE zapisi ADD COLUMN {col} {typ}")

    conn.commit()
    conn.close()

# -------------------------------------------------
# ADD RECORD
# -------------------------------------------------

def add_zapis(plovilo, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, attachments):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    c.execute("""
        INSERT INTO zapisi (
            id, plovilo, datum, trenutni_radni_sati,
            servis_raden_na, ocekivani_servis, do_servisa,
            vrsta_unosa, napomena, attachments
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_id, plovilo, datum, sati,
        servis_raden, ocekivani, do_servisa,
        vrsta, napomena, attachments
    ))

    conn.commit()
    conn.close()

# -------------------------------------------------
# GET RECORDS
# -------------------------------------------------

def get_zapisi(plovilo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, plovilo, datum, trenutni_radni_sati,
               servis_raden_na, ocekivani_servis, do_servisa,
               vrsta_unosa, napomena, attachments
        FROM zapisi
        WHERE plovilo = ?
        ORDER BY trenutni_radni_sati DESC
    """, (plovilo,)).fetchall()

    conn.close()

    return [
        {
            "id": r[0],
            "plovilo": r[1],
            "datum": r[2],
            "trenutni_radni_sati": r[3],
            "servis_raden_na": r[4],
            "ocekivani_servis": r[5],
            "do_servisa": r[6],
            "vrsta_unosa": r[7],
            "napomena": r[8],
            "attachments": r[9]
        }
        for r in rows
    ]

# -------------------------------------------------
# UPDATE RECORD
# -------------------------------------------------

def update_zapis(record_id, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE zapisi
        SET datum = ?,
            trenutni_radni_sati = ?,
            servis_raden_na = ?,
            ocekivani_servis = ?,
            do_servisa = ?,
            vrsta_unosa = ?,
            napomena = ?
        WHERE id = ?
    """, (
        datum, sati, servis_raden, ocekivani,
        do_servisa, vrsta, napomena, record_id
    ))

    conn.commit()
    conn.close()

# -------------------------------------------------
# DELETE RECORD
# -------------------------------------------------

def delete_zapis(record_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Prvo dohvatimo folder s dokumentima
    row = c.execute("SELECT attachments FROM zapisi WHERE id = ?", (record_id,)).fetchone()
    if row and row[0] and os.path.exists(row[0]):
        shutil.rmtree(row[0], ignore_errors=True)

    c.execute("DELETE FROM zapisi WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

# -------------------------------------------------
# SAVE UPLOADED FILES
# -------------------------------------------------

def save_uploaded_files(plovilo, record_id, files):
    folder = os.path.join("uploads", plovilo, record_id)
    os.makedirs(folder, exist_ok=True)

    saved_files = []

    for file in files:
        path = os.path.join(folder, file.name)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        saved_files.append(path)

    return folder, saved_files

# -------------------------------------------------
# ADD FILES TO EXISTING RECORD
# -------------------------------------------------

def add_files_to_record(folder, files):
    os.makedirs(folder, exist_ok=True)

    for file in files:
        path = os.path.join(folder, file.name)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
