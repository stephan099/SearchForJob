import pandas as pd
from bs4 import BeautifulSoup
from utils.request_utils import fetch_html


def search(query: str, location: str, radius: int = 0) -> pd.DataFrame:
    base_url = "https://www.willhaben.at/jobs/suche"
    query_param = query.replace(" ", "%20")
    location_param = location.replace(" ", "%20")
    url = f"{base_url}?keyword={query_param}&location={location_param}&radius={radius}&employment_type=110&region=13863"

    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    results_container = soup.find("div", id="skip-to-resultlist")
    if not results_container:
        return pd.DataFrame()

    job_cards = results_container.select("div[data-testid^='jobsresultlist-row']")
    jobs = []

    for card in job_cards:
        title_elem = card.select_one("span[data-testid$='title']")
        company_elem = card.select_one("span[data-testid$='company-name']")
        location_elem = card.select_one("span[data-testid$='details']")
        link_elem = card.find("a", href=True)

        if title_elem and company_elem and location_elem and link_elem:
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True)
            ort = location_elem.get_text(strip=True).split(",")[-1].strip()
            href = link_elem["href"]
            link = f"https://www.willhaben.at{href}" if href.startswith("/") else href

            jobs.append({
                "Titel": title,
                "Firma": company,
                "Ort": ort,
                "Link": link
            })

    return pd.DataFrame(jobs)
