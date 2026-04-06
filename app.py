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
from database import save_sheet

backup_excel()

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
# Osiguraj da postoji stupac attachments
if "attachments" not in df.columns:
    df["attachments"] = ""


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
uploaded_files = st.file_uploader(
    "Dodaj slike ili dokumente",
    type=["jpg", "jpeg", "png", "pdf"],
    accept_multiple_files=True,
    key="upload_new_record"
)
new_files = st.file_uploader(
    "📎 Dodaj dodatne dokumente",
    type=["jpg", "jpeg", "png", "pdf"],
    accept_multiple_files=True,
    key=f"upload_existing_record_block_{index_to_update}"
)

if st.button("Spremi zapis"):

    # 1) Generiraj ID zapisa
    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2) Odredi servis_raden
    if vrsta == "Servis":
        servis_raden = sati
    else:
        servis_raden = zadnji

    # 3) Kreiraj osnovni zapis
    data = {
        "datum": datum.strftime("%d.%m.%Y"),
        "trenutni radni sati": sati,
        "servis rađen na": servis_raden,
        "očekivani servis": sljedeci,
        "do servisa": sljedeci - sati,
        "vrsta unosa": vrsta,
        "Napomena": napomena,
        "attachments": ""
    }

    # 4) Spremi fajlove
    if uploaded_files:
        from database import save_uploaded_files
        folder, saved_files = save_uploaded_files(plovilo, record_id, uploaded_files)
        data["attachments"] = folder

    # 5) Spremi red u Excel
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
st.subheader("📎 Priloženi dokumenti")

if "attachments" in df.columns:
    for i, row in df.iterrows():
        if row["attachments"]:
            st.write(f"**Zapis {i}:**")
            folder = row["attachments"]
            files = os.listdir(folder)

            for f in files:
                path = os.path.join(folder, f)
                if f.lower().endswith((".jpg", ".jpeg", ".png")):
                    st.image(path, width=200)
                st.download_button(
                    label=f"Preuzmi {f}",
                    data=open(path, "rb").read(),
                    file_name=f
                )


# ---------------- UREĐIVANJE I BRISANJE ----------------

st.subheader("✏️ Uredi ili obriši zapise")
st.subheader("📎 Dodaj dokumente postojećem zapisu")

if not df.empty:
    # Odaberi zapis
    index_to_update = st.number_input(
        "Broj zapisa (redni broj)", 
        min_value=0, 
        max_value=len(df)-1, 
        step=1
    )

    st.write("Odabrani zapis:")
    st.write(df.iloc[index_to_update])

    # JEDINSTVENI KEY – sprječava DuplicateElementKey
    new_files = st.file_uploader(
        "Dodaj nove slike/dokumente",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key=f"upload_existing_record_block_{index_to_update}"
    )

    if st.button("📥 Spremi nove dokumente", key=f"save_docs_block_{index_to_update}"):
        from database import add_files_to_record

        # Ako zapis nema folder → kreiraj ga
        folder = df.loc[index_to_update, "attachments"]

        if not folder or folder.strip() == "":
            record_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder = f"uploads/{plovilo}/{record_id}"
            df.loc[index_to_update, "attachments"] = folder

        # Spremi nove fajlove
        if new_files:
            add_files_to_record(folder, new_files)

        # Spremi ažurirani Excel
        save_sheet(plovilo, df)

        st.success("Dokumenti dodani!")
        st.rerun()

if df.empty:
    st.info("Nema zapisa za prikaz.")
else:
    st.write("Klikni na bilo koju ćeliju da je uredi. Za brisanje označi red i klikni 'Spremi promjene'.")

    # Dodaj checkbox za brisanje
    df_edit = df.copy()
    df_edit["Obriši"] = False

    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
    )
st.subheader("📎 Dodaj dokumente postojećem zapisu")

# Osiguraj da postoji stupac attachments
if "attachments" not in df.columns:
    df["attachments"] = ""

if not df.empty:

    index_to_update = st.number_input(
        "Odaberi zapis (redni broj)",
        min_value=0,
        max_value=len(df)-1,
        step=1
    )

    st.write("Odabrani zapis:")
    st.write(df.iloc[index_to_update])

    folder = df.loc[index_to_update, "attachments"]

    # Prikaz postojećih dokumenata
    if folder and folder.strip() != "" and os.path.exists(folder):
        st.write("📂 Postojeći dokumenti:")
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                st.image(path, width=200)
            st.download_button(
                label=f"Preuzmi {f}",
                data=open(path, "rb").read(),
                file_name=f
            )
    else:
        st.info("Nema dokumenata za ovaj zapis.")

    # Upload novih dokumenata
    new_files = st.file_uploader(
        "Dodaj nove slike/dokumente",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key=f"upload_existing_record_block_{index_to_update}"
    )

    if st.button("📥 Spremi nove dokumente"):
        from database import add_files_to_record

        # Ako zapis nema folder → kreiraj ga
        if not folder or folder.strip() == "":
            record_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder = f"uploads/{plovilo}/{record_id}"
            df.loc[index_to_update, "attachments"] = folder

        # Spremi nove fajlove
        add_files_to_record(folder, new_files)

        # Spremi ažurirani Excel
        save_sheet(plovilo, df)

        st.success("Dokumenti dodani!")
        st.rerun()

    if st.button("💾 Spremi promjene"):
        # Obrisi označene redove
        edited_df = edited_df[edited_df["Obriši"] == False].drop(columns=["Obriši"])

        # Reset index
        edited_df = edited_df.reset_index(drop=True)

        # Ponovni izračun servisa nakon uređivanja
        for i in range(len(edited_df)):
            zadnji, sljedeci, _ = calculate_service_info(edited_df, 0)
            edited_df.loc[i, "servis rađen na"] = zadnji
            edited_df.loc[i, "očekivani servis"] = sljedeci
            edited_df.loc[i, "do servisa"] = sljedeci - int(edited_df.loc[i, "trenutni radni sati"])

        # Spremi u Excel
        save_sheet(plovilo, edited_df)

        st.success("Promjene su spremljene.")
        st.rerun()
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



