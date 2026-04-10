import streamlit as st
from database import init_tables, get_plovila, add_plovilo, get_plovilo
from database import get_zapisi, add_zapis

st.set_page_config(page_title="ServisApp", layout="wide")
init_tables()

# ---------------- NAVIGACIJA ----------------

if "page" not in st.session_state:
    st.session_state.page = "plovila"

if "selected_plovilo" not in st.session_state:
    st.session_state.selected_plovilo = None


def go(page, plovilo_id=None):
    st.session_state.page = page
    st.session_state.selected_plovilo = plovilo_id
    st.rerun()


# ---------------- STRANICA 1: PLOVILA ----------------

if st.session_state.page == "plovila":
    st.title("🚤 Popis plovila")

    st.subheader("Dodaj novo plovilo")
    col1, col2 = st.columns(2)

    with col1:
        registracija = st.text_input("Registracija")

    with col2:
        inicijalni_sati = st.number_input("Inicijalni radni sati", min_value=0, value=0)

    if st.button("➕ Dodaj plovilo"):
        if not registracija.strip():
            st.error("Unesi registraciju.")
        else:
            add_plovilo(registracija.strip(), int(inicijalni_sati))
            st.success("Plovilo dodano.")
            st.rerun()

    st.subheader("Plovila")

    plovila = get_plovila()
    if not plovila:
        st.info("Nema unesenih plovila.")
    else:
        for pid, reg, sati in plovila:
            if st.button(f"{reg}", key=pid):
                go("zapisi", pid)


# ---------------- STRANICA 2: SERVISNI ZAPISI ----------------

elif st.session_state.page == "zapisi":
    plovilo = get_plovilo(st.session_state.selected_plovilo)
    pid, reg, inic_sati = plovilo

    st.title(f"📄 Servisni zapisi — {reg}")

    # Mali gumb u desnom kutu
    st.markdown("""
        <div style='text-align:right; margin-top:-40px;'>
            <button onclick="window.location.href='?page=dodaj_zapis'" 
            style='background-color:#0d6efd; color:white; border:none; padding:8px 14px;
            border-radius:6px; cursor:pointer;'>➕ Dodaj zapis</button>
        </div>
    """, unsafe_allow_html=True)

    zapisi = get_zapisi(pid)

    if not zapisi:
        st.info("Nema unesenih zapisa.")
    else:
        st.subheader("Popis zapisa")

        # Tablica u traženom redoslijedu
        table_data = []
        for zid, datum, sati, vrsta, do_servisa in zapisi:
            table_data.append({
                "Datum": datum,
                "Radni sati": sati,
                "Vrsta unosa": vrsta,
                "Do servisa": do_servisa,
                "Uredi": f"Uredi ({zid})",
                "Dokumenti": f"Dokumenti ({zid})"
            })

        st.table(table_data)


# ---------------- STRANICA 3: DODAJ ZAPIS ----------------

elif st.session_state.page == "dodaj_zapis":
    plovilo = get_plovilo(st.session_state.selected_plovilo)
    pid, reg, inic_sati = plovilo

    st.title(f"➕ Novi zapis — {reg}")

    # --- Sekcija 1: Osnovni podaci ---
    st.header("Osnovni podaci")
    col1, col2 = st.columns(2)

    with col1:
        datum = st.date_input("Datum")

    with col2:
        vrsta_unosa = st.selectbox("Vrsta unosa", [
            "Servis", "Tehnički pregled", "Popravak", "Havarija", "Remont", "Izlaz", "Ostalo"
        ])

    napomena = st.text_area("Napomena")

    # --- Sekcija 2: Radni sati ---
    st.header("Radni sati")

    col1, col2 = st.columns(2)

    with col1:
        trenutni_sati = st.number_input("Trenutni radni sati", min_value=0, value=0)

    # Izračuni
    if vrsta_unosa == "Servis":
        servis_raden_na = trenutni_sati
    else:
        servis_raden_na = trenutni_sati - (trenutni_sati % 100)

    ocekivani_servis = servis_raden_na + 100
    do_servisa = ocekivani_servis - trenutni_sati

    # Custom tooltip HTML
    tooltip_html = f"""
    <span style='color:#0d6efd; font-weight:bold; cursor:pointer;'
          title='Očekivani servis: {ocekivani_servis} h'>
        ⓘ
    </span>
    """

    with col2:
        st.text_input("Servis rađen na", value=str(servis_raden_na), disabled=True)
        st.markdown(
            f"**Do servisa:** {do_servisa} h {tooltip_html}",
            unsafe_allow_html=True
        )

    # --- Sekcija 3: Dokumenti ---
    st.header("Dokumenti")
    attachments = st.text_input("Putanja dokumenata (placeholder)")

    if st.button("💾 Spremi zapis"):
        add_zapis(
            pid,
            str(datum),
            int(trenutni_sati),
            int(servis_raden_na),
            int(ocekivani_servis),
            int(do_servisa),
            vrsta_unosa,
            napomena,
            attachments
        )
        st.success("Zapis dodan.")
        go("zapisi", pid)
