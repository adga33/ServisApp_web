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

init_tables()
migrate_database()

import streamlit as st
import hashlib
import os
import pandas as pd
from datetime import datetime
from fpdf import FPDF

from utils import (
    setup_logging,
    get_boats,
    create_new_boat,
    calculate_service_info,
    calculate_tech_info,
)

# -----------------------------
#  LOGIN SISTEM
# -----------------------------

PLAIN_PASSWORD = "servis123"
PASSWORD_HASH = hashlib.sha256(PLAIN_PASSWORD.encode()).hexdigest()

def check_password(password):
    return hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH

def login_screen():
    st.title("🔐 Prijava u ServisApp")
    password = st.text_input("Lozinka", type="password")
    if st.button("Prijavi se"):
        if check_password(password):
            st.session_state["logged_in"] = True
            st.success("Prijava uspješna!")
        else:
            st.error("Pogrešna lozinka.")

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# -----------------------------
#  INICIJALNA PODEŠAVANJA
# -----------------------------

setup_logging()
st.set_page_config(page_title="Servis plovila", layout="wide")

# ---------------- MAIN ----------------

st.title("⛵ Evidencija servisa plovila")

boats = get_boats()
if not boats:
    st.info("Nema plovila. Dodaj prvo novo plovilo u sidebaru.")
    st.stop()

plovilo = st.selectbox("Odaberi plovilo", boats)

# --- UČITAVANJE IZ SQLITE ---
rows = get_zapisi(plovilo)
df = pd.DataFrame(rows)

# SIGURNOSNO: osiguraj sve stupce
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

    # SIGURNO PRETVARANJE BROJEVA
    for col in ["trenutni_radni_sati", "servis_raden_na", "ocekivani_servis", "do_servisa"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # SORTIRANJE PO RADNIM SATIMA
    df = df.sort_values("trenutni_radni_sati", ascending=False).reset_index(drop=True)

# -----------------------------
#  SERVISNI IZRAČUNI
# -----------------------------

inicijalni = st.number_input("Inicijalni unos (ako postoji)", min_value=0, step=1)

zadnji, sljedeci, do_servisa = calculate_service_info(df, inicijalni)

# -----------------------------
#  VELIKI ISTAKNUTI BANNER
# -----------------------------

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

# ---------------- TABOVI ----------------

tabs = st.tabs([
    "Novi zapis",
    "Pregled",
    "Uredi",
    "Dokumenti",
    "Tehnički pregled",
    "PDF"
])

# ---------------- TAB 1: NOVI ZAPIS ----------------

with tabs[0]:
    st.subheader("➕ Dodaj novi zapis")

    datum = st.date_input("Datum")

    # POLJE ZA RADNE SATE BEZ 0
    sati_input = st.text_input("Radni sati", placeholder="Unesi radne sate")

    if sati_input.strip() == "":
        sati = None
    else:
        try:
            sati = int(sati_input)
        except:
            st.error("Unesi ispravan broj radnih sati.")
            st.stop()

    vrsta = st.selectbox(
        "Vrsta unosa",
        ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"],
        key="novi_vrsta_unosa"
    )

    napomena = st.text_input("Napomena")

    uploaded_files = st.file_uploader(
        "📎 Priloži slike ili dokumente",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True
    )

    if st.button("💾 Spremi zapis"):

        if sati is None:
            st.error("Unesi radne sate.")
            st.stop()

        datum_str = datum.strftime("%d.%m.%Y")

        # SIGURNOSNO: provjera duplikata
        if not df.empty:
            duplikat = df[
                (df["datum"] == datum_str) &
                (df["trenutni_radni_sati"] == sati) &
                (df["vrsta_unosa"] == vrsta)
            ]
            if not duplikat.empty:
                st.error("⚠️ Ovaj zapis već postoji!")
                st.stop()

        record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        if vrsta == "Servis":
            servis_raden = sati
        else:
            servis_raden = zadnji

        ocekivani = sljedeci
        do_servisa_val = sljedeci - sati

        attachments = ""
        if uploaded_files:
            folder, saved_files = save_uploaded_files(plovilo, record_id, uploaded_files)
            attachments = folder

        add_zapis(
            plovilo,
            datum_str,
            sati,
            servis_raden,
            ocekivani,
            do_servisa_val,
            vrsta,
            napomena,
            attachments
        )

        st.success("Zapis spremljen!")
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
        index_to_edit = st.selectbox(
            "Odaberi zapis",
            df.index,
            format_func=lambda i: f"{df.loc[i,'datum']} – {df.loc[i,'vrsta_unosa']} – {df.loc[i,'trenutni_radni_sati']} h",
            key="edit_odabir_zapisa"
        )

        edit_row = df.loc[index_to_edit]
        record_id = int(edit_row["id"])

        new_datum = st.date_input(
            "Datum",
            datetime.strptime(edit_row["datum"], "%d.%m.%Y"),
            key=f"edit_datum_{record_id}"
        )

        new_sati = st.number_input(
            "Radni sati",
            min_value=0,
            value=int(edit_row["trenutni_radni_sati"]),
            key=f"edit_sati_{record_id}"
        )

        # --- VRSTA UNOSA (s normalizacijom) ---
        vrste = ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"]

        raw_vrsta = str(edit_row["vrsta_unosa"]).strip().lower()

mapa = {
    "servis": "Servis",
    "tehnički pregled": "Tehnički pregled",
    "popravak": "Popravak",
    "havarija": "Havarija",
    "remont": "Remont",
    "izlaz": "Izlaz",
    "ostalo": "Ostalo"
}

current_vrsta = mapa.get(raw_vrsta, "Ostalo")


        new_vrsta = st.selectbox(
            "Vrsta unosa",
            vrste,
            index=vrste.index(current_vrsta),
            key=f"edit_vrsta_{record_id}"
        )

        new_napomena = st.text_input(
            "Napomena",
            edit_row["napomena"],
            key=f"edit_napomena_{record_id}"
        )

        if new_vrsta == "Servis":
            new_servis_raden = new_sati
        else:
            new_servis_raden = edit_row["servis_raden_na"]

        new_ocekivani = edit_row["ocekivani_servis"]

        # SIGURNO PRETVARANJE
        try:
            new_ocekivani = int(new_ocekivani)
        except:
            new_ocekivani = 0

        try:
            new_sati = int(new_sati)
        except:
            new_sati = 0

        new_do_servisa = new_ocekivani - new_sati

        if st.button("💾 Spremi izmjene", key=f"edit_spremi_{record_id}"):
            update_zapis(
                record_id,
                new_datum.strftime("%d.%m.%Y"),
                new_sati,
                new_servis_raden,
                new_ocekivani,
                new_do_servisa,
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
        index_to_update = st.number_input("Odaberi zapis", min_value=0, max_value=len(df)-1, step=1)
        folder = df.loc[index_to_update, "attachments"]
        record_id = df.loc[index_to_update, "id"]

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

# ---------------- TAB 5: TEHNIČKI PREGLED ----------------

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
