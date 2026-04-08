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

from utils import (
    setup_logging,
    get_boats,
    calculate_service_info,
    calculate_tech_info,
)

# -----------------------------
#  INIT
# -----------------------------

init_tables()
migrate_database()
setup_logging()
st.set_page_config(page_title="Servis plovila", layout="wide")

# -----------------------------
#  LOGIN
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
#  MAIN UI
# -----------------------------

st.title("⛵ Evidencija servisa plovila")

boats = get_boats()
if not boats:
    st.info("Nema plovila u bazi.")
    st.stop()

plovilo = st.selectbox("Odaberi plovilo", boats)

# -----------------------------
#  LOAD DATA
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
    df["id"] = df["id"].astype(int)
    df["napomena"] = df["napomena"].astype(str)

    numeric_cols = ["trenutni_radni_sati", "servis_raden_na", "ocekivani_servis", "do_servisa"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df.sort_values("trenutni_radni_sati", ascending=False).reset_index(drop=True)

# -----------------------------
#  SERVICE CALCULATION
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
#  TABS
# -----------------------------

tabs = st.tabs(["Novi zapis", "Pregled", "Uredi", "Dokumenti", "Tehnički pregled", "PDF"])

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

    napomena = st.text_input("Napomena")

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
        idx = st.selectbox(
            "Odaberi zapis",
            df.index,
            format_func=lambda i: f"{df.loc[i,'datum']} – {df.loc[i,'vrsta_unosa']} – {df.loc[i,'trenutni_radni_sati']} h"
        )

        row = df.loc[idx]
        record_id = int(row["id"])

        new_datum = st.date_input("Datum", datetime.strptime(row["datum"], "%d.%m.%Y"))
        new_sati = st.number_input("Radni sati", min_value=0, value=int(row["trenutni_radni_sati"]))

        # --- VRSTE UNOSA (lokalno definirano, ne dijeli se s TAB 1) ---
        vrste = ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"]

        # --- NORMALIZACIJA ---
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

        if st.button("💾 Spremi izmjene", key=f"edit_spremi_{record_id}"):
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

        if st.button("🗑️ Obriši zapis", key=f"edit_obrisi_{record_id}"):
            delete_zapis(record_id)
            st.success("Zapis obrisan.")
            st.rerun()



# ---------------- TAB 4: DOKUMENTI ----------------

with tabs[3]:
    st.subheader("📎 Dokumenti")

    if df.empty:
        st.info("Nema zapisa.")
    else:
        idx = st.number_input("Odaberi zapis", min_value=0, max_value=len(df)-1, step=1)
        folder = df.loc[idx, "attachments"]
        record_id = df.loc[idx, "id"]

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

        for _, row in df.iterrows():
            pdf.cell(0, 10, txt=str(row), ln=True)

        pdf.output("report.pdf")
        st.download_button("Preuzmi PDF", open("report.pdf","rb"), file_name="report.pdf")
