import os
import hashlib
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from fpdf import FPDF

from database import (
    init_tables,
    migrate_database,
    add_zapis,
    get_zapisi,
    update_zapis,
    delete_zapis,
    save_uploaded_files,
    add_files_to_record
)

from utils import (
    setup_logging,
    get_boats,
    calculate_tech_info
)

# -------------------------------------------------
# INIT
# -------------------------------------------------

init_tables()
migrate_database()
setup_logging()
st.set_page_config(page_title="Servis plovila", layout="wide")

# -------------------------------------------------
# LOGIN
# -------------------------------------------------

PASSWORD_HASH = hashlib.sha256("servis123".encode()).hexdigest()

def check_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest() == PASSWORD_HASH

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Prijava u ServisApp")
    pw = st.text_input("Lozinka", type="password")
    if st.button("Prijavi se"):
        if check_password(pw):
            st.session_state["logged_in"] = True
            st.success("Prijava uspješna!")
        else:
            st.error("Pogrešna lozinka.")
    st.stop()

# -------------------------------------------------
# MAIN UI
# -------------------------------------------------

st.title("⛵ Evidencija servisa plovila")

# -------------------------------------------------
# SIDEBAR – DODAVANJE PLOVILA
# -------------------------------------------------

st.sidebar.subheader("➕ Dodaj novo plovilo")
novo_plovilo = st.sidebar.text_input("Naziv novog plovila")

if st.sidebar.button("Dodaj plovilo"):
    if not novo_plovilo.strip():
        st.sidebar.error("Unesi ispravan naziv.")
    else:
        os.makedirs(f"uploads/{novo_plovilo.strip()}", exist_ok=True)
        st.sidebar.success(f"Plovilo '{novo_plovilo}' je dodano.")
        st.rerun()

# -------------------------------------------------
# ODABIR PLOVILA
# -------------------------------------------------

boats = get_boats()
if not boats:
    st.info("Nema plovila u bazi.")
    st.stop()

plovilo = st.selectbox("Odaberi plovilo", boats)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

rows = get_zapisi(plovilo)
df = pd.DataFrame(rows)

required_cols = [
    "id", "plovilo", "datum", "trenutni_radni_sati",
    "servis_raden_na", "ocekivani_servis", "do_servisa",
    "vrsta_unosa", "napomena", "attachments"
]

for col in required_cols:
    if col not in df.columns:
        df[col] = None

if not df.empty:
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["napomena"] = df["napomena"].astype(str)

    numeric_cols = ["trenutni_radni_sati", "servis_raden_na", "ocekivani_servis", "do_servisa"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df.sort_values("trenutni_radni_sati", ascending=False)
    df = df.set_index("id")

# -------------------------------------------------
# TABS
# -------------------------------------------------

tabs = st.tabs(["Novi zapis", "Pregled", "Uredi", "Dokumenti", "Tehnički pregled", "PDF", "Baza"])

# -------------------------------------------------
# TAB 1: NOVI ZAPIS
# -------------------------------------------------

with tabs[0]:
    st.subheader("➕ Dodaj novi zapis")

    datum = st.date_input("Datum")
    sati_raw = st.text_input("Radni sati", placeholder="Unesi radne sate")

    if sati_raw.strip() == "":
        sati = None
    else:
        try:
            sati = int(sati_raw)
        except:
            st.error("Radni sati moraju biti broj.")
            st.stop()

    vrste = ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"]
    vrsta = st.selectbox("Vrsta unosa", vrste)

    napomena = st.text_input("Napomena")

    files = st.file_uploader("📎 Priloži dokumente", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if st.button("💾 Spremi zapis"):
        if sati is None:
            st.error("Unesi radne sate.")
            st.stop()

        datum_str = datum.strftime("%d.%m.%Y")

        # SERVIS LOGIKA U BAZI
        if vrsta == "Servis":
            servis_raden = sati
        else:
            servis_raden = df["servis_raden_na"].max() if not df.empty else 0

        ocekivani = servis_raden + 100
        do_servisa_val = ocekivani - sati

        record_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        attachments = ""

        if files:
            folder, saved = save_uploaded_files(plovilo, record_id, files)
            attachments = folder

        add_zapis(plovilo, datum_str, sati, servis_raden, ocekivani, do_servisa_val, vrsta, napomena, attachments)

        st.success("Zapis spremljen.")
        st.rerun()

# -------------------------------------------------
# TAB 2: PREGLED
# -------------------------------------------------

with tabs[1]:
    st.subheader("📑 Pregled zapisa")
    if df.empty:
        st.info("Nema zapisa.")
    else:
        st.dataframe(df, use_container_width=True)

# -------------------------------------------------
# TAB 3: UREDI
# -------------------------------------------------

with tabs[2]:
    st.subheader("✏️ Uredi zapis")

    if df.empty:
        st.info("Nema zapisa.")
    else:
        ids = df.index.tolist()

        record_id = st.selectbox(
            "Odaberi zapis",
            ids,
            format_func=lambda rid: f"{df.loc[rid,'datum']} – {df.loc[rid,'vrsta_unosa']} – {df.loc[rid,'trenutni_radni_sati']} h"
        )

        row = df.loc[record_id]

        # Datum
        try:
            datum_obj = datetime.strptime(row["datum"], "%d.%m.%Y").date()
        except:
            datum_obj = datetime.today().date()

        new_datum = st.date_input("Datum", datum_obj)

        # Radni sati
        new_sati = st.number_input(
            "Radni sati",
            min_value=0,
            value=int(row["trenutni_radni_sati"])
        )

        # Vrsta
        vrste = ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"]
        new_vrsta = st.selectbox(
        "Vrsta unosa",
        vrste,
        index=vrste.index(row["vrsta_unosa"]) if row["vrsta_unosa"] in vrste else 0,
        key=f"vrsta_{record_id}"
        )


        # Napomena
        new_napomena = st.text_input("Napomena", row["napomena"])

        # SERVIS LOGIKA
        if new_vrsta == "Servis":
            new_servis_raden = new_sati
        else:
            new_servis_raden = row["servis_raden_na"]

        new_ocekivani = new_servis_raden + 100
        new_do_servisa = new_ocekivani - new_sati

        if st.button("💾 Spremi izmjene"):
            update_zapis(
                record_id,
                new_datum.strftime("%d.%m.%Y"),
                int(new_sati),
                int(new_servis_raden),
                int(new_ocekivani),
                int(new_do_servisa),
                new_vrsta,
                new_napomena
            )
            st.success("Zapis izmijenjen.")
            st.rerun()

        if st.button("🗑️ Obriši zapis"):
            delete_zapis(record_id)
            st.success("Zapis obrisan.")
            st.rerun()

# -------------------------------------------------
# TAB 4: DOKUMENTI
# -------------------------------------------------

with tabs[3]:
    st.subheader("📎 Dokumenti")

    if df.empty:
        st.info("Nema zapisa.")
    else:
        rid = st.number_input("Odaberi zapis", min_value=int(df.index.min()), max_value=int(df.index.max()), step=1)
        if rid in df.index:
            folder = df.loc[rid, "attachments"]

            if folder and os.path.exists(folder):
                for f in os.listdir(folder):
                    path = os.path.join(folder, f)
                    st.download_button(f"Preuzmi {f}", open(path, "rb").read(), file_name=f)

            new_files = st.file_uploader("Dodaj dokumente", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

            if st.button("📥 Spremi nove dokumente"):
                if new_files:
                    add_files_to_record(folder, new_files)
                    st.success("Dokumenti dodani.")
                    st.rerun()

# -------------------------------------------------
# TAB 5: TEHNIČKI PREGLED
# -------------------------------------------------

with tabs[4]:
    st.subheader("🛠 Tehnički pregled")

    expiry, days_left = calculate_tech_info(df)

    if expiry:
        st.success(f"Vrijedi do: {expiry.strftime('%d.%m.%Y')}")
        st.info(f"Preostalo dana: {days_left}")
    else:
        st.warning("Nema tehničkog pregleda.")

# -------------------------------------------------
# TAB 6: PDF
# -------------------------------------------------

with tabs[5]:
    st.subheader("📄 PDF izvještaj")

    if st.button("Generiraj PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for rid, row in df.iterrows():
            pdf.cell(0, 10, txt=str(row), ln=True)

        pdf.output("report.pdf")
        st.download_button("Preuzmi PDF", open("report.pdf", "rb"), file_name="report.pdf")

# -------------------------------------------------
# TAB 7: BAZA
# -------------------------------------------------

with tabs[6]:
    st.subheader("🧹 Administracija baze")

    if st.button("Prikaži sve vrijednosti vrsta_unosa"):
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        rows = c.execute("SELECT id, vrsta_unosa FROM zapisi").fetchall()
        conn.close()
        st.write(rows)

    if st.button("⚠️ PRISILNO očisti prazne vrijednosti"):
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
            UPDATE zapisi
            SET vrsta_unosa = 'Ostalo'
            WHERE vrsta_unosa IS NULL
               OR vrsta_unosa = ''
               OR TRIM(vrsta_unosa) = ''
        """)
        conn.commit()
        conn.close()
        st.success("Prazne vrijednosti su sada 'Ostalo'. Restartaj aplikaciju.")

    st.markdown("---")
    st.subheader("🛠 SQL konzola (napredno)")

    sql_query = st.text_area("SQL upit", height=150, placeholder="PRAGMA table_info(zapisi);")

    if st.button("Pokreni SQL"):
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute(sql_query)
            result = c.fetchall()
            conn.commit()
            conn.close()
            st.success("SQL izvršen.")
            st.write(result)
        except Exception as e:
            st.error(f"Greška: {e}")
