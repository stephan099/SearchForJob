import streamlit as st
import pandas as pd
from parsers import karriere_at

# Lade PLZ-Daten aus CSV
plz_df = pd.read_csv("PLZ_Niederoesterreich.csv", delimiter=';', dtype=str)

# Bereinigung der Spaltennamen
plz_df.columns = plz_df.columns.str.strip().str.lower()

st.title("Job-Suche auf karriere.at")

query = st.text_input("Jobtitel", "softwareentwickler")

# Ortschaften und Bezirke alphabetisch sortiert anzeigen
ortschaften = sorted(plz_df["ort"].unique())
bezirke = sorted(plz_df["bezirk"].unique())

selected_orte = st.multiselect("Ortschaften wählen (Suche unterstützt):", options=ortschaften)
selected_bezirke = st.multiselect("Bezirke wählen (Suche unterstützt):", options=bezirke)

if st.button("Suche starten"):
    all_jobs = []

    search_orte = set(selected_orte)

    for bezirk in selected_bezirke:
        bezirk_orte = plz_df[plz_df["bezirk"] == bezirk]["ort"].tolist()
        search_orte.update(bezirk_orte)

    if search_orte:
        for ort in search_orte:
            try:
                jobs_df = karriere_at.search(query, ort)

                if not jobs_df.empty:
                    plz_list = plz_df.loc[plz_df["ort"] == ort, "plz"].tolist()
                    plz = plz_list[0] if plz_list else "N/A"

                    jobs_df["Postleitzahl"] = plz
                    jobs_df["Ort"] = ort
                    all_jobs.append(jobs_df)

            except Exception as e:
                st.error(f"Fehler bei der Suche für {ort}: {e}")

        if all_jobs:
            result_df = pd.concat(all_jobs, ignore_index=True)
            result_df = result_df[["Titel", "Firma", "Postleitzahl", "Ort", "Link"]]
            result_df["Link"] = result_df["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Zum Inserat</a>')

            st.markdown("### Gefundene Jobs:")
            st.write(result_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.warning("Keine Jobs gefunden.")
    else:
        st.warning("Bitte mindestens eine Ortschaft oder einen Bezirk auswählen.")
