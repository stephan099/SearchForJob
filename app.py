import streamlit as st
import pandas as pd
from parsers import karriere_at, metajob_at, jobviertel_at, stepstone_at, willhaben_at
import openai
from typing import List

openai.api_key = st.secrets["openai_api_key"]

# --- CSV einlesen und vorbereiten ---
plz_df = pd.read_csv("PLZ_Niederoesterreich.csv", sep=";")
plz_df = plz_df.loc[:, plz_df.columns.str.strip() != ""]
plz_df = plz_df.rename(columns={"ORT": "Ort", "PLZ": "PLZ", "Bezirk": "Bezirk"})
plz_df["Ort"] = plz_df["Ort"].str.strip()
plz_df["PLZ"] = plz_df["PLZ"].astype(str).str.strip()
plz_df["Bezirk"] = plz_df["Bezirk"].str.strip()
plz_df = plz_df[["Ort", "PLZ", "Bezirk"]].drop_duplicates()
unique_plz_map = plz_df.drop_duplicates(subset="Ort").set_index("Ort")["PLZ"]

bezirke = sorted(plz_df["Bezirk"].dropna().unique())
ortschaften = sorted(plz_df["Ort"].dropna().unique())

st.title("Job-Suche")

def get_alternative_titles(search_term: str) -> List[str]:
    prompt = (
        f"Gib mir 5 alternative Bezeichnungen oder Synonyme für den Jobtitel '{search_term}'. "
        "Antworte nur mit einer durch Kommas getrennten Liste, ohne Erklärungen."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein Assistent für berufliche Alternativen."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.5,
        )
        text = response.choices[0].message.content.strip()
        return [alt.strip() for alt in text.split(",") if alt.strip()]
    except Exception as e:
        st.warning(f"Fehler bei der Begriffserweiterung: {e}")
        return []

# Eingabe Jobtitel
query = st.text_input("Jobtitel", "")

# Expander mit reinen Vorschlägen
if query:
    with st.expander("Alternative Suchbegriffe als Anregung"):
        alt_titles = get_alternative_titles(query)
        if alt_titles:
            for alt in alt_titles:
                st.write(f"• {alt}")
        else:
            st.write("Keine Vorschläge gefunden.")

# Filter-Auswahl
selected_bezirke = st.multiselect("Bezirke", bezirke)
selected_orte    = st.multiselect("Ortschaften", ortschaften)
radius           = st.slider("Umkreis (km)", 0, 50, 20)
engines          = st.multiselect(
    "Suchmaschinen",
    ["karriere.at", "metajob.at", "jobviertel.at", "stepstone.at", "willhaben.at"],
    default=["karriere.at"]
)

# Orte aus Bezirken ergänzen
aus_bezirk    = plz_df[plz_df["Bezirk"].isin(selected_bezirke)]["Ort"].tolist() if selected_bezirke else []
searched_orte = sorted(set(selected_orte + aus_bezirk))

if st.button("Suche starten"):
    if not searched_orte:
        st.warning("Bitte wähle mindestens eine Ortschaft oder einen Bezirk.")
    else:
        all_results = []

        for ort in searched_orte:
            try:
                # karriere.at
                if "karriere.at" in engines:
                    df = karriere_at.search(query, ort)
                    if not df.empty:
                        df["Postleitzahl"]   = df["Ort"].map(unique_plz_map)
                        df["Suchmaschine"]   = "karriere.at"
                        all_results.append(df)

                # metajob.at
                if "metajob.at" in engines:
                    df = metajob_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"]   = df["Ort"].map(unique_plz_map)
                        df["Suchmaschine"]   = "metajob.at"
                        all_results.append(df)

                # jobviertel.at
                if "jobviertel.at" in engines:
                    df = jobviertel_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"]   = df["Ort"].map(unique_plz_map)
                        df["Suchmaschine"]   = "jobviertel.at"
                        all_results.append(df)

                # stepstone.at
                if "stepstone.at" in engines:
                    df = stepstone_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"]   = df["Ort"].map(unique_plz_map)
                        df["Suchmaschine"]   = "stepstone.at"
                        all_results.append(df)

                # willhaben.at
                if "willhaben.at" in engines:
                    df = willhaben_at.search(query, ort, radius)
                    if not df.empty:
                        df["Postleitzahl"]   = df["Ort"].map(unique_plz_map)
                        df["Suchmaschine"]   = "willhaben.at"
                        all_results.append(df)

            except Exception as e:
                st.warning(f"Fehler bei {', '.join(engines)} ({ort}): {e}")

        if all_results:
            result_df = pd.concat(all_results, ignore_index=True)
            # gewünschte Spaltenreihenfolge inkl. Suchmaschine
            result_df = result_df[["Titel", "Firma", "Postleitzahl", "Ort", "Link", "Suchmaschine"]]
            # klickbare Links
            result_df["Link"] = result_df["Link"].apply(
                lambda u: f'<a href="{u}" target="_blank">Zum Inserat</a>'
            )
            st.write("Gefundene Jobs:")
            st.write(result_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.warning("Keine Jobs gefunden.")
