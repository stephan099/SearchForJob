from bs4 import BeautifulSoup
import pandas as pd
from utils.request_utils import fetch_html  # ← angepasst

def search(query: str, location: str, radius: int = 0) -> pd.DataFrame:
    base_url = "https://www.jobviertel.at/search.php"
    params = {
        "search_company": query,
        "search_city": location,
        "quan": "",
        "num_page": 0,
        "id_ort": 0,
        "sortierung": "datum"
    }

    full_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    html = fetch_html(full_url)

    soup = BeautifulSoup(html, "html.parser")
    job_blocks = soup.select("div.column-middle.middle-happy")

    jobs = []

    for block in job_blocks:
        title_elem = block.find("h1")
        info_elem = block.find("p", class_="job-info")
        parent_link = block.find_parent("a", href=True)

        if title_elem and info_elem and parent_link:
            title = title_elem.get_text(strip=True)
            parts = [p.strip() for p in info_elem.get_text(separator="|", strip=True).split("|") if p.strip()]
            firma = parts[0] if len(parts) > 0 else ""
            ort_raw = parts[1] if len(parts) > 1 else ""
            ort = ort_raw.split("(")[0].strip()
            link = parent_link["href"]
            if not link.startswith("http"):
                link = f"https://www.jobviertel.at{link}"

            jobs.append({
                "Titel": title,
                "Firma": firma,
                "Ort": ort,
                "Link": link
            })

    return pd.DataFrame(jobs)
