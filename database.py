import sqlite3
import os

DB_PATH = "database.db"

# -----------------------------
#  CONNECTION
# -----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
#  INIT TABLES
# -----------------------------
def init_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS zapisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plovilo TEXT NOT NULL,
            datum TEXT NOT NULL,
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
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO zapisi (
            plovilo, datum, trenutni_radni_sati, servis_raden_na,
            ocekivani_servis, do_servisa, vrsta_unosa, napomena, attachments
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (plovilo, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, attachments))

    conn.commit()
    conn.close()

# -----------------------------
#  GET RECORDS FOR BOAT
# -----------------------------
def get_zapisi(plovilo):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM zapisi
        WHERE plovilo = ?
        ORDER BY id DESC
    """, (plovilo,))

    rows = cur.fetchall()
    conn.close()
    return rows

# -----------------------------
#  UPDATE RECORD
# -----------------------------
def update_zapis(id, datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE zapisi
        SET datum = ?, trenutni_radni_sati = ?, servis_raden_na = ?,
            ocekivani_servis = ?, do_servisa = ?, vrsta_unosa = ?, napomena = ?
        WHERE id = ?
    """, (datum, sati, servis_raden, ocekivani, do_servisa, vrsta, napomena, id))

    conn.commit()
    conn.close()

# -----------------------------
#  DELETE RECORD
# -----------------------------
def delete_zapis(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM zapisi WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# -----------------------------
#  FILE UPLOAD HANDLING
# -----------------------------
def save_uploaded_files(boat, record_id, files):
    folder = f"uploads/{boat}/{record_id}"
    os.makedirs(folder, exist_ok=True)

    saved_files = []

    for file in files:
        file_path = os.path.join(folder, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        saved_files.append(file_path)

    return folder, saved_files


def add_files_to_record(folder, files):
    os.makedirs(folder, exist_ok=True)
    saved_files = []

    for file in files:
        file_path = os.path.join(folder, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        saved_files.append(file_path)

    return saved_files

