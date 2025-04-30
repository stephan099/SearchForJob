import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote

# PLZ-Mapping nur einmal laden
_plz_df = (
    pd.read_csv("PLZ_Niederoesterreich.csv", sep=";")
      .rename(columns={"ORT": "Ort", "PLZ": "PLZ", "Bezirk": "Bezirk"})
      .assign(Ort=lambda df: df["Ort"].str.strip(),
              PLZ=lambda df: df["PLZ"].astype(str).str.strip())
      .drop_duplicates(subset="Ort")
)
_PLZ_MAP = _plz_df.set_index("Ort")["PLZ"].to_dict()

# Der Standard-User-Agent
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

def search(query: str, location: str, radius: int = 30) -> pd.DataFrame:
    """
    Suche auf Stepstone.at nach Stellenbezeichnung, Ort und Radius.
    Gibt DataFrame mit [Titel, Firma, Ort, Link] zurück.
    """
    base_url = "https://www.stepstone.at/jobs/"
    # query und Ort sluggen, Umlaute etc. percent-encoden
    q_slug = quote(query.lower().replace(" ", "-"), safe='')
    loc_clean = location.strip()
    loc_slug = quote(loc_clean.lower().replace(" ", "-"), safe='')
    plz = _PLZ_MAP.get(loc_clean)

    if plz:
        path = f"{q_slug}-in-{plz}-{loc_slug}"
    else:
        # Falls Ort nicht in PLZ-Liste, einfach ohne PLZ
        path = f"{q_slug}-in-{loc_slug}"

    url = f"{base_url}{path}"
    params = {
        "radius": radius,
        "searchOrigin": "Resultlist_top-search",
        "whereType": "autosuggest"
    }

    resp = requests.get(url, headers=_HEADERS, params=params, timeout=40)
    if resp.status_code != 200:
        raise Exception(f"Fehler beim Abruf von stepstone.at: Status {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("article[data-genesis-element='CARD']")

    jobs = []
    for c in cards:
        t = c.select_one("h2 a")
        f = c.select_one("span[data-at='job-item-company-name']")
        l = c.select_one("span[data-at='job-item-location']")
        if not (t and f and l):
            continue

        title = t.get_text(strip=True)
        firma = f.get_text(strip=True)
        ort = l.get_text(strip=True)
        href = t.get("href", "")
        link = href if href.startswith("http") else f"https://www.stepstone.at{href}"

        jobs.append({
            "Titel": title,
            "Firma": firma,
            "Ort": ort,
            "Link": link
        })

    return pd.DataFrame(jobs)
