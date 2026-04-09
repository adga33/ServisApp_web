import os
import sqlite3
from datetime import datetime

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
# MIGRATION – FIX OLD STRUCTURES + INVALID IDs
# -------------------------------------------------

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1) Ensure all required columns exist
    required_columns = {
        "id": "TEXT",
        "plovilo": "TEXT",
        "datum": "TEXT",
        "trenutni_radni_sati": "INTEGER",
        "servis_raden_na": "INTEGER",
        "ocekivani_servis": "INTEGER",
        "do_servisa": "INTEGER",
        "vrsta_unosa": "TEXT",
        "napomena": "TEXT",
        "attachments": "TEXT"
    }

    existing = c.execute("PRAGMA table_info(zapisi)").fetchall()
    existing_cols = {row[1] for row in existing}

    for col, col_type in required_columns.items():
        if col not in existing_cols:
            c.execute(f"ALTER TABLE zapisi ADD COLUMN {col} {col_type}")

    # 2) Fix NULL or empty IDs
    c.execute("""
        UPDATE zapisi
        SET id = strftime('%Y%m%d%H%M%S', 'now') || '_' || rowid
        WHERE id IS NULL OR id = ''
    """)

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
    rows = c.execute("SELECT * FROM zapisi WHERE plovilo = ?", (plovilo,)).fetchall()
    conn.close()
    return rows


# -------------------------------------------------
# UPDATE RECORD
# -------------------------------------------------

def update_zapis(record_id, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE zapisi
        SET datum = ?, trenutni_radni_sati = ?, servis_raden_na = ?,
            ocekivani_servis = ?, do_servisa = ?, vrsta_unosa = ?, napomena = ?
        WHERE id = ?
    """, (datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, record_id))

    conn.commit()
    conn.close()


# -------------------------------------------------
# DELETE RECORD
# -------------------------------------------------

def delete_zapis(record_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM zapisi WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


# -------------------------------------------------
# FILE HANDLING
# -------------------------------------------------

def save_uploaded_files(plovilo, record_id, files):
    folder = f"uploads/{plovilo}/{record_id}"
    os.makedirs(folder, exist_ok=True)

    saved_files = []
    for file in files:
        path = os.path.join(folder, file.name)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        saved_files.append(path)

    return folder, saved_files


def add_files_to_record(folder, files):
    os.makedirs(folder, exist_ok=True)
    for file in files:
        path = os.path.join(folder, file.name)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
