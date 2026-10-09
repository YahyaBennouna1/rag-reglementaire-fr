"""Construit le vocabulaire du corpus : chaque mot présent dans les 45 guides.

    uv run python scripts/build_vocabulary.py

Sert au masquage des données personnelles (leçon 23) : un mot qui figure dans les guides de l'ANSSI
(« Sysmon », « spraying »…) n'est pas une donnée personnelle de l'utilisateur, même si le modèle
de langue le prend pour un nom de personne. Le fichier produit est petit et versionné : l'image
Docker, qui ne contient pas les guides, peut l'embarquer.
"""

import re
from collections import Counter
from pathlib import Path

from ragfr.index import load_parsed_documents

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "vocabulaire_corpus.txt"
MIN_COUNT = 1  # « spraying » n'apparaît qu'une fois dans les guides (mesuré, leçon 23)


def words(text: str) -> list[str]:
    return re.findall(r"[a-zà-ÿ][a-zà-ÿ0-9-]+", text.lower())


def main() -> None:
    counts = Counter()
    for doc in load_parsed_documents():
        for element in doc.elements:
            counts.update(words(element.text))
    vocabulary = sorted(w for w, n in counts.items() if n >= MIN_COUNT)
    OUT.write_text("\n".join(vocabulary) + "\n", encoding="utf-8")
    print(f"{len(vocabulary)} mots -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
