"""Télécharge les PDF listés dans data/corpus.csv vers data/raw/."""

import csv
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
CORPUS_CSV = ROOT / "data" / "corpus.csv"
RAW_DIR = ROOT / "data" / "raw"


def download_pdf(url: str) -> bytes:
    """Télécharge un PDF et renvoie son contenu. Lève une erreur si ce n'en est pas un."""
    response = httpx.get(url, follow_redirects=True, timeout=60)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF-"):
        raise ValueError("le fichier reçu n'est pas un PDF")
    return response.content


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    failures = []
    for row in rows:
        dest = RAW_DIR / f"{row['doc_ref']}.pdf"

        if dest.exists():
            print(f"[déjà là] {row['doc_ref']}")
            continue

        try:
            content = download_pdf(row["url"])
        except (httpx.HTTPError, ValueError) as e:
            print(f"[ERREUR]  {row['doc_ref']} : {e}")
            failures.append(row["doc_ref"])
            continue

        dest.write_bytes(content)
        print(f"[ok]      {row['doc_ref']}")

    print(f"\n{len(rows) - len(failures)}/{len(rows)} PDF disponibles")
    if failures:
        print("Échecs :", ", ".join(failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()