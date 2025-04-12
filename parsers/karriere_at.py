import requests
from bs4 import BeautifulSoup
import pandas as pd

def search(query: str, location: str) -> pd.DataFrame:
    url = f"https://www.karriere.at/jobs/{query}/{location}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Fehler beim Abruf: Status {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    job_elements = soup.select("div.m-jobsListItem")

    jobs = []

    for job in job_elements:
        title_elem = job.select_one("h2.m-jobsListItem__title a")
        company_elem = job.select_one("div.m-jobsListItem__company a")
        location_elem = job.select_one("a.m-jobsListItem__location")
        data_id = job.get("data-id")

        if title_elem and company_elem and location_elem and data_id:
            job_link = f"https://www.karriere.at/jobs/{data_id}"
            jobs.append({
                "Titel": title_elem.text.strip(),
                "Firma": company_elem.text.strip(),
                "Ort": location_elem.text.strip(),
                "Link": job_link
            })

    return pd.DataFrame(jobs)
