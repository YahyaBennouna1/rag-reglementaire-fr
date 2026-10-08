"""Collecte la liste des guides ANSSI du catalogue vers data/candidats.csv.

La machine collecte, l'humain choisit : on recopie ensuite dans data/corpus.csv
les guides retenus pour le projet.
"""

import csv
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "data" / "candidats.csv"

BASE_URL = "https://messervices.cyber.gouv.fr"
CATALOGUE_URL = f"{BASE_URL}/catalogue"
PAUSE_SECONDS = 0.5  # politesse envers le serveur

MOIS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}


def parse_date_fr(text: str) -> str:
    """'Publié le 23 janvier 2014' -> '2014-01-23' (chaîne vide si absent)."""
    m = re.search(r"(\d{1,2})(?:er)? (\w+) (\d{4})", text)
    if not m or m.group(2).lower() not in MOIS:
        return ""
    day, month, year = int(m.group(1)), MOIS[m.group(2).lower()], int(m.group(3))
    return f"{year:04d}-{month:02d}-{day:02d}"


def list_guide_pages(client: httpx.Client) -> list[str]:
    html = client.get(CATALOGUE_URL).raise_for_status().text
    soup = BeautifulSoup(html, "html.parser")
    paths = {a["href"] for a in soup.select('a[href^="/guides/"]')}
    return sorted(paths)


def read_guide_page(client: httpx.Client, path: str) -> dict | None:
    soup = BeautifulSoup(client.get(BASE_URL + path).raise_for_status().text, "html.parser")
    pdf_links = [a["href"] for a in soup.select('a[href$=".pdf"]')]
    if not pdf_links:
        return None
    h1 = soup.find("h1")
    published = soup.find(string=re.compile(r"Publié le"))
    return {
        "slug": path.removeprefix("/guides/"),
        "titre": h1.get_text(strip=True) if h1 else "",
        "url": pdf_links[0],
        "date_maj": parse_date_fr(published) if published else "",
    }


def main() -> None:
    rows = []
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        paths = list_guide_pages(client)
        print(f"{len(paths)} pages de guides dans le catalogue")
        for path in paths:
            try:
                row = read_guide_page(client, path)
            except httpx.HTTPError as e:
                print(f"[ERREUR] {path} : {e}")
                continue
            if row:
                rows.append(row)
            time.sleep(PAUSE_SECONDS)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["slug", "titre", "url", "date_maj"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} guides avec un PDF écrits dans {OUT_CSV}")


if __name__ == "__main__":
    main()
