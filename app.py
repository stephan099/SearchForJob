import streamlit as st
import pandas as pd
from parsers import karriere_at, metajob_at, jobviertel_at, stepstone_at  # <--- Stepstone importieren

# --- CSV mit ;-Trenner einlesen und Spalten trimmen/umbenennen ---
plz_df = pd.read_csv("PLZ_Niederoesterreich.csv", sep=";")

# Falls am Ende noch eine leere Spalte kommt, lösche sie
plz_df = plz_df.loc[:, plz_df.columns.str.strip() != ""]

# Spalten umbenennen und trimmen
plz_df = plz_df.rename(columns={
    "ORT": "Ort",
    "PLZ": "PLZ",
    "Bezirk": "Bezirk"
})
plz_df["Ort"] = plz_df["Ort"].str.strip()
plz_df["PLZ"] = plz_df["PLZ"].astype(str).str.strip()
plz_df["Bezirk"] = plz_df["Bezirk"].str.strip()
plz_df = plz_df[["Ort", "PLZ", "Bezirk"]].drop_duplicates()

# Mapping: Nur erste PLZ pro Ort
unique_plz_map = plz_df.drop_duplicates(subset="Ort").set_index("Ort")["PLZ"]

# Einzigartige Bezirke und Ortschaften
bezirke = sorted(plz_df["Bezirk"].dropna().unique())
ortschaften = sorted(plz_df["Ort"].dropna().unique())

st.title("Job-Suche")

# Eingaben
query = st.text_input("Jobtitel", "softwareentwickler")
selected_bezirke = st.multiselect("Bezirke", bezirke)
selected_orte = st.multiselect("Ortschaften", ortschaften)
radius = st.slider("Umkreis (km)", 0, 50, 20)
engines = st.multiselect(
    "Suchmaschinen",
    ["karriere.at", "metajob.at", "jobviertel.at", "stepstone.at"],  # <--- Stepstone ergänzt
    default=["karriere.at"]
)

# Ortschaften aus Bezirken erweitern
aus_bezirk = plz_df[plz_df["Bezirk"].isin(selected_bezirke)]["Ort"].tolist() if selected_bezirke else []
searched_orte = sorted(set(selected_orte + aus_bezirk))

if st.button("Suche starten"):
    if not searched_orte:
        st.warning("Bitte wähle mindestens eine Ortschaft oder einen Bezirk.")
    else:
        all_results = []

        for ort in searched_orte:
            try:
                if "karriere.at" in engines:
                    df = karriere_at.search(query, ort)
                    if not df.empty:
                        df["Postleitzahl"] = df["Ort"].map(unique_plz_map)
                        all_results.append(df)

                if "metajob.at" in engines:
                    df = metajob_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"] = df["Ort"].map(unique_plz_map)
                        all_results.append(df)

                if "jobviertel.at" in engines:
                    df = jobviertel_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"] = df["Ort"].map(unique_plz_map)
                        all_results.append(df)

                if "stepstone.at" in engines:  # <--- Stepstone ergänzen
                    df = stepstone_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"] = df["Ort"].map(unique_plz_map)
                        all_results.append(df)

            except Exception as e:
                st.warning(f"Fehler bei {', '.join(engines)} ({ort}): {e}")

        if all_results:
            result_df = pd.concat(all_results, ignore_index=True)
            result_df = result_df[["Titel", "Firma", "Postleitzahl", "Ort", "Link"]]
            result_df["Link"] = result_df["Link"].apply(lambda u: f'<a href="{u}" target="_blank">Zum Inserat</a>')
            st.write("Gefundene Jobs:")
            st.write(result_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.warning("Keine Jobs gefunden.")
