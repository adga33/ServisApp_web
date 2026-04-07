import sqlite3
import os

DB_NAME = "database.db"

# -----------------------------
#  CONNECTION
# -----------------------------
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

# -----------------------------
#  INIT TABLES
# -----------------------------
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

# -----------------------------
#  ADD RECORD
# -----------------------------
def add_zapis(plovilo, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, attachments):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO zapisi (
            plovilo, datum, trenutni_radni_sati, servis_raden_na,
            ocekivani_servis, do_servisa, vrsta_unosa, napomena, attachments
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (plovilo, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, attachments))

    conn.commit()
    conn.close()

# -----------------------------
#  GET RECORDS
# -----------------------------
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

# -----------------------------
#  UPDATE RECORD
# -----------------------------
def update_zapis(record_id, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE zapisi SET
            datum=?, trenutni_radni_sati=?, servis_raden_na=?,
            ocekivani_servis=?, do_servisa=?, vrsta_unosa=?, napomena=?
        WHERE id=?
    """, (datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, record_id))

    conn.commit()
    conn.close()

# -----------------------------
#  DELETE RECORD
# -----------------------------
def delete_zapis(record_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM zapisi WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

# -----------------------------
#  FILE UPLOADS
# -----------------------------
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
