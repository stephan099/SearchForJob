import pandas as pd
from bs4 import BeautifulSoup
from utils.request_utils import fetch_html

def search(query: str, location: str, radius: int = 0) -> pd.DataFrame:
    """
    Suche auf Stepstone.at nach der gegebenen Stellenbezeichnung und Ort.
    Gibt ein DataFrame mit den Spalten Titel, Firma, Ort und Link zurück.
    Radius wird ignoriert.
    """
    base_url = "https://www.stepstone.at/jobs/"
    query_encoded = query.replace(" ", "-")
    location_encoded = location.replace(" ", "-")
    url = f"{base_url}{query_encoded}-in-{location_encoded}/"

    print(f"url: {url}")

    html = fetch_html(url, timeout=15)
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.select("article[data-genesis-element='CARD']")

    jobs = []

    for card in job_cards:
        title_elem = card.select_one("h2 a")
        company_elem = card.select_one("span[data-at='job-item-company-name']")
        location_elem = card.select_one("span[data-at='job-item-location']")

        if title_elem and company_elem and location_elem:
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True)
            ort = location_elem.get_text(strip=True)

            href = title_elem.get("href")
            link = f"https://www.stepstone.at{href}" if href and href.startswith("/") else href

            jobs.append({
                "Titel": title,
                "Firma": company,
                "Ort": ort,
                "Link": link
            })

    return pd.DataFrame(jobs)
