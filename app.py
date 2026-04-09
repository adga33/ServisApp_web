from database import (
    init_tables,
    add_zapis,
    get_zapisi,
    update_zapis,
    delete_zapis,
    save_uploaded_files,
    add_files_to_record,
    migrate_database
)

import streamlit as st
import hashlib
import os
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import sqlite3

from utils import (
    setup_logging,
    get_boats,
    calculate_service_info,
    calculate_tech_info,
)

# -----------------------------
# INIT
# -----------------------------

init_tables()
migrate_database()
setup_logging()
st.set_page_config(page_title="Servis plovila", layout="wide")

# -----------------------------
# LOGIN
# -----------------------------

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

# -----------------------------
# MAIN UI
# -----------------------------

st.title("⛵ Evidencija servisa plovila")

boats = get_boats()
if not boats:
    st.info("Nema plovila u bazi.")
    st.stop()

plovilo = st.selectbox("Odaberi plovilo", boats)

# -----------------------------
# LOAD DATA
# -----------------------------

rows = get_zapisi(plovilo)
df = pd.DataFrame(rows)

required_cols = [
    "id", "plovilo", "datum", "trenutni_radni_sati", "servis_raden_na",
    "ocekivani_servis", "do_servisa", "vrsta_unosa", "napomena", "attachments"
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

    # KLJUČNO: index = ID
    df = df.sort_values("trenutni_radni_sati", ascending=False)
    df = df.set_index("id")

# -----------------------------
# SERVICE CALCULATION
# -----------------------------

inicijalni = st.number_input("Inicijalni unos (ako postoji)", min_value=0, step=1)
zadnji, sljedeci, do_servisa = calculate_service_info(df, inicijalni)

st.markdown(f"""
<div style="
    background-color:#fff3cd;
    border-left: 10px solid #ff9800;
    padding: 20px;
    font-size: 24px;
    font-weight: 700;
    border-radius: 8px;
    margin-top: 15px;
    margin-bottom: 25px;
    line-height: 1.6;
">
🔧 Zadnji servis: {zadnji} h<br>
➡️ Sljedeći servis: {sljedeci} h<br>
⏳ Preostalo: {do_servisa} h
</div>
""", unsafe_allow_html=True)

# -----------------------------
# TABS
# -----------------------------

tabs = st.tabs(["Novi zapis", "Pregled", "Uredi", "Dokumenti", "Tehnički pregled", "PDF", "Baza"])

# ---------------- TAB 1: NOVI ZAPIS ----------------

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
    vrsta = st.selectbox("Vrsta unosa", vrste, key="novi_vrsta")

    napomena = st.text_input("Napomena", key="novi_napomena")

    files = st.file_uploader("📎 Priloži dokumente", type=["jpg","jpeg","png","pdf"], accept_multiple_files=True)

    if st.button("💾 Spremi zapis"):
        if sati is None:
            st.error("Unesi radne sate.")
            st.stop()

        datum_str = datum.strftime("%d.%m.%Y")

        if vrsta == "Servis":
            servis_raden = sati
        else:
            servis_raden = zadnji

        ocekivani = sljedeci
        do_servisa_val = sljedeci - sati

        record_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        attachments = ""

        if files:
            folder, saved = save_uploaded_files(plovilo, record_id, files)
            attachments = folder

        add_zapis(plovilo, datum_str, sati, servis_raden, ocekivani, do_servisa_val, vrsta, napomena, attachments)

        st.success("Zapis spremljen.")
        st.rerun()

# ---------------- TAB 2: PREGLED ----------------

with tabs[1]:
    st.subheader("📑 Pregled zapisa")
    if df.empty:
        st.info("Nema zapisa.")
    else:
        st.dataframe(df, use_container_width=True)

# ---------------- TAB 3: UREDI ----------------
with tabs[2]:
    st.subheader("✏️ Uredi zapis")

    if df.empty:
        st.info("Nema zapisa.")
    else:
        # LISTA ID-eva
        ids = df.index.tolist()

        # ODABIR PREMA ID-u
        record_id = st.selectbox(
            "Odaberi zapis",
            ids,
            format_func=lambda rid: f"{df.loc[rid,'datum']} – {df.loc[rid,'vrsta_unosa']} – {df.loc[rid,'trenutni_radni_sati']} h",
            key="edit_odabir"
        )

        # PRAVI RED
        row = df.loc[record_id]

        new_datum = st.date_input(
            "Datum",
            datetime.strptime(row["datum"], "%d.%m.%Y"),
            key=f"edit_datum_{record_id}"
        )

        new_sati = st.number_input(
            "Radni sati",
            min_value=0,
            value=int(row["trenutni_radni_sati"]),
            key=f"edit_sati_{record_id}"
        )

        vrste = ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"]

        # NORMALIZACIJA
        raw = str(row["vrsta_unosa"]).strip().lower()
        mapa = {
            "servis": "Servis",
            "tehnički pregled": "Tehnički pregled",
            "popravak": "Popravak",
            "havarija": "Havarija",
            "remont": "Remont",
            "izlaz": "Izlaz",
            "ostalo": "Ostalo"
        }
        current_vrsta = mapa.get(raw, "Ostalo")

        new_vrsta = st.selectbox(
            "Vrsta unosa",
            vrste,
            index=vrste.index(current_vrsta),
            key=f"edit_vrsta_{record_id}"
        )

        new_napomena = st.text_input(
            "Napomena",
            row["napomena"],
            key=f"edit_napomena_{record_id}"
        )

        if new_vrsta == "Servis":
            new_servis_raden = new_sati
        else:
            new_servis_raden = row["servis_raden_na"]

        new_ocekivani = int(row["ocekivani_servis"])
        new_do_servisa = new_ocekivani - int(new_sati)

        if st.button("💾 Spremi izmjene", key="edit_spremi"):
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

        if st.button("🗑️ Obriši zapis", key="edit_obrisi"):
            delete_zapis(record_id)
            st.success("Zapis obrisan.")
            st.rerun()
       

# ---------------- TAB 4: DOKUMENTI ----------------

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

            new_files = st.file_uploader("Dodaj dokumente", type=["jpg","jpeg","png","pdf"], accept_multiple_files=True)

            if st.button("📥 Spremi nove dokumente"):
                if new_files:
                    add_files_to_record(folder, new_files)
                    st.success("Dokumenti dodani.")
                    st.rerun()

# ---------------- TAB 5: TEHNIČKI ----------------

with tabs[4]:
    st.subheader("🛠 Tehnički pregled")

    expiry, days_left = calculate_tech_info(df)

    if expiry:
        st.success(f"Vrijedi do: {expiry.strftime('%d.%m.%Y')}")
        st.info(f"Preostalo dana: {days_left}")
    else:
        st.warning("Nema tehničkog pregleda.")

# ---------------- TAB 6: PDF ----------------

with tabs[5]:
    st.subheader("📄 PDF izvještaj")

    if st.button("Generiraj PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for rid, row in df.iterrows():
            pdf.cell(0, 10, txt=str(row), ln=True)

        pdf.output("report.pdf")
        st.download_button("Preuzmi PDF", open("report.pdf","rb"), file_name="report.pdf")

# ---------------- TAB 7: BAZA ----------------

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
