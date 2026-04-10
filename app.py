import streamlit as st
from database import init_tables, add_plovilo, get_plovila

st.set_page_config(page_title="ServisApp", layout="wide")

init_tables()

st.title("🚤 Unos plovila")

col1, col2 = st.columns(2)

with col1:
    registracija = st.text_input("Registracija plovila")

with col2:
    inicijalni_sati = st.number_input("Inicijalni radni sati", min_value=0, value=0)

if st.button("➕ Dodaj plovilo"):
    if not registracija.strip():
        st.error("Unesi registraciju.")
    else:
        add_plovilo(registracija.strip(), int(inicijalni_sati))
        st.success("Plovilo dodano.")
        st.rerun()

st.subheader("📋 Popis plovila")

plovila = get_plovila()

if not plovila:
    st.info("Još nema unesenih plovila.")
else:
    st.table(plovila)
