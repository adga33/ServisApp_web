from database import (
    init_tables,
    add_zapis,
    get_zapisi,
    update_zapis,
    delete_zapis,
    save_uploaded_files,
    add_files_to_record
)

init_tables()

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

if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False

st.set_page_config(page_title="Servis plovila", layout="wide")

st.markdown("""
<style>
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        max-width: 260px !important;
    }
    button[kind="primary"] {
        width: 100% !important;
    }
    .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------

st.sidebar.title("⚙️ Postavke")

with st.sidebar.expander("⚙️ Postavke aplikacije"):
    st.write("Ovdje će ići konfiguracija aplikacije.")

st.sidebar.subheader("➕ Dodaj novo plovilo")
novo_plovilo = st.sidebar.text_input("Naziv novog plovila")

boats = get_boats()

if st.sidebar.button("Dodaj plovilo"):
    if not novo_plovilo.strip():
        st.sidebar.error("Unesi ispravan naziv.")
    elif novo_plovilo in boats:
        st.sidebar.warning("Plovilo već postoji.")
    else:
        create_new_boat(novo_plovilo.strip())
        st.sidebar.success(f"Plovilo '{novo_plovilo}' je dodano.")
        st.rerun()

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

if not df.empty:
    df["id"] = df["id"].astype(int)
    df = df.sort_values("id", ascending=False).reset_index(drop=True)

# Osiguraj da je Napomena string
if "napomena" in df.columns:
    df["napomena"] = df["napomena"].astype(str)

# Osiguraj da postoji stupac attachments
if "attachments" not in df.columns:
    df["attachments"] = ""

inicijalni = st.number_input("Inicijalni unos (ako postoji)", min_value=0, step=1)
# ---------------- TAB 1: NOVI ZAPIS ----------------

tabs = st.tabs([
    "Novi zapis",
    "Pregled",
    "Uredi",
    "Dokumenti",
    "Tehnički pregled",
    "PDF"
])

with tabs[0]:
    st.subheader("➕ Dodaj novi zapis")

    colA, colB = st.columns(2)

    with colA:
        datum = st.date_input("Datum", key="new_record_date")
        sati = st.number_input("Radni sati", min_value=0, step=1, key="new_record_hours")

    with colB:
        vrsta = st.selectbox(
            "Vrsta unosa",
            ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"],
            key="new_record_type"
        )
        napomena = st.text_input("Napomena", key="new_record_note")

    uploaded_files = st.file_uploader(
        "📎 Priloži slike ili dokumente",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="upload_new_record"
    )

    if st.button("💾 Spremi zapis", key="save_new_record"):
        record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Izračuni kao prije
        if vrsta == "Servis":
            servis_raden = sati
        else:
            servis_raden = zadnji

        ocekivani = sljedeci
        do_servisa_val = sljedeci - sati

        # Formatiranje datuma
        datum_str = datum.strftime("%d.%m.%Y")

        # Upload dokumenata
        attachments = ""
        if uploaded_files:
            folder, saved_files = save_uploaded_files(plovilo, record_id, uploaded_files)
            attachments = folder

        # Spremanje u SQLite
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

def highlight_servis(row):
    if row["vrsta_unosa"] == "Servis":
        return ["background-color: #ffcccc"] * len(row)
    return [""] * len(row)

with tabs[1]:
    st.subheader("📑 Pregled zapisa")

    search = st.text_input("Pretraga", key="search_records")

    if search:
        df_filtered = df[df.apply(
            lambda row: row.astype(str).str.contains(search, case=False).any(),
            axis=1
        )]
    else:
        df_filtered = df

    st.dataframe(
        df_filtered.style.apply(highlight_servis, axis=1),
        use_container_width=True
    )
# ---------------- TAB 3: UREDI ----------------

with tabs[2]:
    st.subheader("✏️ Uredi zapis")

    if df.empty:
        st.info("Nema zapisa za uređivanje.")
    else:
        index_to_edit = st.selectbox(
            "Odaberi zapis za uređivanje",
            df.index,
            format_func=lambda i: f"{df.loc[i, 'datum']} – {df.loc[i, 'vrsta_unosa']} – {df.loc[i, 'trenutni_radni_sati']} h"
        )

        edit_row = df.loc[index_to_edit]
        record_id = int(edit_row["id"])

        col1, col2 = st.columns(2)

        with col1:
            new_datum = st.date_input(
                "Datum",
                datetime.strptime(edit_row["datum"], "%d.%m.%Y"),
                key="edit_record_date"
            )
            new_sati = st.number_input(
                "Trenutni radni sati",
                min_value=0,
                value=int(edit_row["trenutni_radni_sati"]),
                key="edit_record_hours"
            )
            new_vrsta = st.selectbox(
                "Vrsta unosa",
                ["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"],
                index=["Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"].index(edit_row["vrsta_unosa"]),
                key="edit_record_type"
            )

        with col2:
            new_napomena = st.text_input(
                "Napomena",
                edit_row["napomena"],
                key="edit_record_note"
            )

        # Ponovni izračuni
        if new_vrsta == "Servis":
            new_servis_raden = new_sati
        else:
            new_servis_raden = edit_row["servis_raden_na"]

        new_ocekivani = edit_row["ocekivani_servis"]
        new_do_servisa = new_ocekivani - new_sati

        if st.button("💾 Spremi izmjene", key="save_edit_record"):
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

            st.success("Zapis je uspješno izmijenjen.")
            st.rerun()

# ---------------- TAB 4: DOKUMENTI ----------------

with tabs[3]:
    st.subheader("📎 Dokumenti")

    if df.empty:
        st.info("Nema zapisa.")
    else:
        index_to_update = st.number_input(
            "Odaberi zapis (redni broj)",
            min_value=0,
            max_value=len(df) - 1,
            step=1,
            key="doc_record_index"
        )

        st.write("Odabrani zapis:")
        st.write(df.iloc[index_to_update])

        folder = df.loc[index_to_update, "attachments"]
        record_id = df.loc[index_to_update, "id"]

        if folder and folder.strip() != "" and os.path.exists(folder):
            st.write("📂 Postojeći dokumenti:")
            for f in os.listdir(folder):
                path = os.path.join(folder, f)
                if f.lower().endswith((".jpg", ".jpeg", ".png")):
                    st.image(path, width=200)
                st.download_button(
                    label=f"Preuzmi {f}",
                    data=open(path, "rb").read(),
                    file_name=f,
                    key=f"download_{index_to_update}_{f}"
                )
        else:
            st.info("Nema dokumenata za ovaj zapis.")

        new_files = st.file_uploader(
            "Dodaj nove slike/dokumente",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
            key="upload_existing_docs"
        )

        if st.button("📥 Spremi nove dokumente", key="save_new_docs"):
            if not folder or folder.strip() == "":
                folder = f"uploads/{plovilo}/{record_id}"
                os.makedirs(folder, exist_ok=True)

            if new_files:
                add_files_to_record(folder, new_files)

                # Ažuriraj putanju u bazi
                update_zapis(
                    record_id,
                    df.loc[index_to_update, "datum"],
                    df.loc[index_to_update, "trenutni_radni_sati"],
                    df.loc[index_to_update, "servis_raden_na"],
                    df.loc[index_to_update, "ocekivani_servis"],
                    df.loc[index_to_update, "do_servisa"],
                    df.loc[index_to_update, "vrsta_unosa"],
                    df.loc[index_to_update, "napomena"]
                )

                st.success("Dokumenti dodani!")
                st.rerun()
            else:
                st.warning("Nema odabranih dokumenata za spremanje.")

# ---------------- TAB 6: PDF IZVJEŠTAJ ----------------

with tabs[5]:
    st.subheader("📄 Izvještaj za sva plovila")

    if st.button("Generiraj PDF izvještaj", key="pdf_button"):
        boats_all = get_boats()
        rows = []

        for boat in boats_all:
            df_boat = pd.DataFrame(get_zapisi(boat))
            if df_boat.empty:
                rows.append((boat, "-", "-"))
                continue

            zadnji_b, sljedeci_b, do_servisa_b = calculate_service_info(df_boat, 0)
            rows.append((boat, zadnji_b, do_servisa_b))

        pdf = FPDF()
        pdf.add_page()

        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", "", 14)

        pdf.cell(0, 10, txt="Izvještaj o zadnjim radnim satima i preostalom vremenu do servisa", ln=True, align='C')

        datum_generiranja = datetime.now().strftime("%d.%m.%Y")
        pdf.ln(5)
        pdf.set_font("DejaVu", "", 12)
        pdf.cell(0, 10, txt=f"Datum generiranja: {datum_generiranja}", ln=True, align='L')
        pdf.ln(10)

        pdf.set_font("DejaVu", "", 11)
        pdf.cell(60, 8, "Plovilo", 1)
        pdf.cell(60, 8, "Zadnji radni sati", 1)
        pdf.cell(60, 8, "Do servisa", 1)
        pdf.ln()

        for boat, zadnji_sati, do_servisa_val in rows:
            pdf.cell(60, 8, boat, 1)
            pdf.cell(60, 8, str(zadnji_sati), 1)
            pdf.cell(60, 8, str(do_servisa_val), 1)
            pdf.ln()

        pdf_file = "servisi_report.pdf"
        pdf.output(pdf_file)

        with open(pdf_file, "rb") as f:
            st.download_button("📥 Preuzmi PDF", f, file_name=pdf_file)
