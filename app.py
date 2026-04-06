import streamlit as st
import hashlib

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
from utils import setup_logging
setup_logging()
from database import backup_excel
backup_excel()

import streamlit as st
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False
import pandas as pd
from datetime import datetime

from utils import (
    get_boats,
    create_new_boat,
    load_sheet,
    append_row,
    backup_excel,
    calculate_service_info,
    calculate_tech_info,
)
with st.sidebar.expander("⚙️ Postavke"):
    st.write("Ovdje će ići konfiguracija aplikacije.")

st.set_page_config(page_title="Servis plovila", layout="wide")

# ---------------- SIDEBAR ----------------

st.sidebar.title("⚙️ Postavke")

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
df = load_sheet(plovilo)
inicijalni = st.number_input("Inicijalni unos (ako postoji)", min_value=0, step=1)


# ---------------- INFO ----------------

st.subheader("📌 Informacije o servisu")

zadnji, sljedeci, do_servisa = calculate_service_info(df, inicijalni)


col1, col2, col3 = st.columns(3)
col1.metric("Zadnji servis", f"{zadnji} h")
col2.metric("Sljedeći servis", f"{sljedeci} h")
col3.metric("Preostalo do servisa", f"{do_servisa} h")

# ---------------- TEHNIČKI ----------------

# Zadnji tehnički pregled
df_tech = df[df["vrsta unosa"] == "Tehnički pregled"]

if not df_tech.empty:
    zadnji_tech = df_tech.iloc[-1]["datum"]
    st.info(f"📅 Zadnji tehnički pregled: **{zadnji_tech}**")
else:
    st.info("📅 Zadnji tehnički pregled: nije evidentiran.")


st.subheader("📌 Tehnički pregled")

istek, dana = calculate_tech_info(df)

if istek is None:
    st.info("Tehnički pregled nije evidentiran.")
else:
    if dana < 0:
        st.error(f"Tehnički istekao prije {abs(dana)} dana!")
    elif dana < 30:
        st.warning(f"Tehnički istječe za {dana} dana.")
    else:
        st.success(f"Tehnički vrijedi do {istek.strftime('%d.%m.%Y')} ({dana} dana).")

# ---------------- UNOS ----------------

st.subheader("➕ Dodaj novi zapis")

col1, col2 = st.columns(2)

with col1:
    datum = st.date_input("Datum")
    sati = st.number_input("Trenutni radni sati", min_value=0, step=1)
    vrsta = st.selectbox(
    "Vrsta unosa",
    [
        "Servis",
        "Tehnički pregled",
        "Popravak",
        "Havarija",
        "Remont",
        "Izlaz",
        "Ostalo"
    ]
)



with col2:
    napomena = st.text_input("Napomena")

if st.button("Spremi zapis"):
    if vrsta == "Servis":
        servis_raden = sati
    else:
        servis_raden = zadnji

    data = {
        "datum": datum.strftime("%d.%m.%Y"),
        "trenutni radni sati": sati,
        "servis rađen na": servis_raden,
        "očekivani servis": sljedeci,
        "do servisa": sljedeci - sati,
        "vrsta unosa": vrsta,
        "Napomena": napomena,
    }

    append_row(plovilo, data)
    st.success("Zapis spremljen!")
    st.rerun()

# ---------------- PREGLED ----------------

st.subheader("📑 Pregled zapisa")

search = st.text_input("Pretraga")

if search:
    df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
else:
    df_filtered = df

def highlight_servis(row):
    if row["vrsta unosa"] == "Servis":
        return ["background-color: #ffcccc"] * len(row)   # svijetlo crvena
    return [""] * len(row)

st.dataframe(
    df_filtered.style.apply(highlight_servis, axis=1),
    use_container_width=True
)
st.subheader("✏️ Uredi zapis")
st.subheader("🗑️ Obriši zapis")

if df.empty:
    st.info("Nema zapisa za brisanje.")
else:
    index_to_delete = st.selectbox(
        "Odaberi zapis za brisanje",
        df.index,
        format_func=lambda i: f"{df.loc[i, 'datum']} – {df.loc[i, 'vrsta unosa']} – {df.loc[i, 'trenutni radni sati']} h"
    )

    # 1) Klik na "Obriši" samo aktivira popup
    if st.button("Obriši odabrani zapis"):
        st.session_state.confirm_delete = True

    # 2) Ako je popup aktivan — prikaži upozorenje i gumbe
    if st.session_state.confirm_delete:
        st.warning("⚠️ Jeste li sigurni da želite obrisati ovaj zapis? Ova radnja je nepovratna.")

        st.write(f"**Datum:** {df.loc[index_to_delete, 'datum']}")
        st.write(f"**Vrsta unosa:** {df.loc[index_to_delete, 'vrsta unosa']}")
        st.write(f"**Radni sati:** {df.loc[index_to_delete, 'trenutni radni sati']} h")
        st.write(f"**Napomena:** {df.loc[index_to_delete, 'Napomena']}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Da, obriši"):
                df = df.drop(index_to_delete).reset_index(drop=True)
                save_sheet(plovilo, df)
                st.session_state.confirm_delete = False
                st.success("Zapis je obrisan.")
                st.rerun()

        with col2:
            if st.button("Odustani"):
                st.session_state.confirm_delete = False

if df.empty:
    st.info("Nema zapisa za uređivanje.")
else:
    # Odaberi red za uređivanje
    index_to_edit = st.selectbox(
        "Odaberi zapis za uređivanje",
        df.index,
        format_func=lambda i: f"{df.loc[i, 'datum']} – {df.loc[i, 'vrsta unosa']} – {df.loc[i, 'trenutni radni sati']} h"
    )

    # Učitaj postojeće vrijednosti
    edit_row = df.loc[index_to_edit]

    col1, col2 = st.columns(2)

    with col1:
        new_datum = st.date_input(
            "Datum",
            datetime.strptime(edit_row["datum"], "%d.%m.%Y")
        )
        new_sati = st.number_input(
            "Trenutni radni sati",
            min_value=0,
            value=int(edit_row["trenutni radni sati"])
        )
        new_vrsta = st.selectbox(
            "Vrsta unosa",
            ["Servis", "Tehnički pregled", "Popravak", "Izlaz", "Ostalo"],
            index=["Servis", "Tehnički pregled", "Popravak", "Izlaz", "Ostalo"].index(edit_row["vrsta unosa"])
        )

    with col2:
        new_napomena = st.text_input("Napomena", edit_row["Napomena"])

    # Spremi izmjene
    if st.button("Spremi izmjene"):
        df.loc[index_to_edit, "datum"] = new_datum.strftime("%d.%m.%Y")
        df.loc[index_to_edit, "trenutni radni sati"] = new_sati
        df.loc[index_to_edit, "vrsta unosa"] = new_vrsta
        df.loc[index_to_edit, "Napomena"] = new_napomena

        # Ponovni izračun servisa
        zadnji, sljedeci, _ = calculate_service_info(df)
        df.loc[index_to_edit, "servis rađen na"] = zadnji
        df.loc[index_to_edit, "očekivani servis"] = sljedeci
        df.loc[index_to_edit, "do servisa"] = sljedeci - new_sati

        save_sheet(plovilo, df)

        st.success("Zapis je uspješno izmijenjen.")
        st.rerun()


# ---------------- BACKUP ----------------

st.subheader("💾 Backup")

if st.button("Napravi backup"):
    file = backup_excel()
    st.success(f"Backup spremljen kao: {file}")

# ---------------- PDF IZVJEŠTAJ ----------------

# ---------------- PDF IZVJEŠTAJ ----------------

from fpdf import FPDF

st.subheader("📄 Izvještaj za sva plovila")

if st.button("Generiraj PDF izvještaj"):
    boats = get_boats()
    rows = []

    for boat in boats:
        df_boat = load_sheet(boat)
        zadnji, sljedeci, do_servisa = calculate_service_info(df_boat, 0)
        rows.append((boat, zadnji, do_servisa))

    pdf = FPDF()
    pdf.add_page()

    # Unicode font
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 14)

    pdf.cell(0, 10, txt="Izvještaj o zadnjim radnim satima i preostalom vremenu do servisa", ln=True, align='C')

    # Datum generiranja
    datum_generiranja = datetime.now().strftime("%d.%m.%Y")
    pdf.ln(5)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 10, txt=f"Datum generiranja: {datum_generiranja}", ln=True, align='L')
    pdf.ln(10)

    # Tablica
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(60, 8, "Plovilo", 1)
    pdf.cell(60, 8, "Zadnji radni sati", 1)
    pdf.cell(60, 8, "Do servisa", 1)
    pdf.ln()

    for boat, zadnji_sati, do_servisa in rows:
        pdf.cell(60, 8, boat, 1)
        pdf.cell(60, 8, str(zadnji_sati), 1)
        pdf.cell(60, 8, str(do_servisa), 1)
        pdf.ln()

    pdf.output("servisi_report.pdf")

    with open("servisi_report.pdf", "rb") as f:
        st.download_button("📥 Preuzmi PDF", f, file_name="servisi_report.pdf")
from database import cleanup_old_backups
cleanup_old_backups()
from database import ensure_excel_exists
ensure_excel_exists()



