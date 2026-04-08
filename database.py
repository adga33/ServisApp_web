import sqlite3
import os

DB_NAME = "database.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_tables():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS zapisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

def migrate_database():
    """Dodaje stupce koji nedostaju u starim bazama."""
    conn = get_connection()
    c = conn.cursor()

    required_cols = {
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
    existing_cols = [col[1] for col in existing]

    for col, col_type in required_cols.items():
        if col not in existing_cols:
            c.execute(f"ALTER TABLE zapisi ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()

def add_zapis(*args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO zapisi (
            plovilo, datum, trenutni_radni_sati, servis_raden_na,
            ocekivani_servis, do_servisa, vrsta_unosa, napomena, attachments
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, args)
    conn.commit()
    conn.close()

def get_zapisi(plovilo):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM zapisi WHERE plovilo=? ORDER BY id DESC", (plovilo,))
    rows = c.fetchall()
    conn.close()

    cols = [
        "id", "plovilo", "datum", "trenutni_radni_sati", "servis_raden_na",
        "ocekivani_servis", "do_servisa", "vrsta_unosa", "napomena", "attachments"
    ]

    return [dict(zip(cols, row)) for row in rows]

def update_zapis(record_id, *args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE zapisi SET
            datum=?, trenutni_radni_sati=?, servis_raden_na=?,
            ocekivani_servis=?, do_servisa=?, vrsta_unosa=?, napomena=?
        WHERE id=?
    """, (*args, record_id))
    conn.commit()
    conn.close()

def delete_zapis(record_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM zapisi WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

def save_uploaded_files(plovilo, record_id, files):
    folder = f"uploads/{plovilo}/{record_id}"
    os.makedirs(folder, exist_ok=True)
    saved = []
    for f in files:
        path = os.path.join(folder, f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        saved.append(path)
    return folder, saved

def add_files_to_record(folder, files):
    os.makedirs(folder, exist_ok=True)
    for f in files:
        path = os.path.join(folder, f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())
