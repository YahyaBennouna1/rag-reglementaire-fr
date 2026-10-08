"""Prépare la mesure du parsing : 20 tableaux tirés au hasard, vus par Docling et par PyMuPDF.

Écrit results/parsing_tableaux.md. Pour chaque tableau, un humain note si chaque sortie est
lisible et complète (✅ / ❌). Le résultat attendu par le guide :
« X / 20 tableaux corrects avec Docling contre Y / 20 avec PyMuPDF ».
"""

import random
from pathlib import Path

import pymupdf
from docling_core.types.doc import DoclingDocument, TableItem

ROOT = Path(__file__).resolve().parent.parent
PARSED_DIR = ROOT / "data" / "parsed"
RAW_DIR = ROOT / "data" / "raw"
OUT = ROOT / "results" / "parsing_tableaux.md"
N_TABLES = 20
SEED = 42


def pymupdf_text(pdf: Path, page_no: int, bbox, page_height: float) -> str:
    """Texte brut de PyMuPDF dans le rectangle du tableau (même zone que Docling)."""
    # Docling compte y depuis le BAS de la page, PyMuPDF depuis le HAUT : on convertit.
    top, bottom = page_height - bbox.t, page_height - bbox.b
    with pymupdf.open(pdf) as doc:
        return doc[page_no - 1].get_text(clip=pymupdf.Rect(bbox.l, top, bbox.r, bottom)).strip()


def main() -> None:
    candidates = []
    for path in sorted(PARSED_DIR.glob("*.docling.json")):
        doc_ref = path.name.removesuffix(".docling.json")
        doc = DoclingDocument.load_from_json(path)
        for item, _ in doc.iterate_items():
            # Au moins 3 lignes de données : on ne mesure pas les petits cartouches de 2 cases.
            if isinstance(item, TableItem) and item.prov and item.data.num_rows >= 4:
                candidates.append((doc_ref, doc, item))

    rng = random.Random(SEED)
    chosen = rng.sample(candidates, min(N_TABLES, len(candidates)))
    lines = [
        "# Mesure du parsing des tableaux : Docling contre PyMuPDF",
        "",
        f"{len(chosen)} tableaux tirés au hasard (graine {SEED}) parmi {len(candidates)} tableaux "
        "d'au moins 3 lignes de données.",
        "Pour chaque tableau : la sortie est-elle **lisible et complète** (lignes et colonnes justes) ?",
        "",
        "| # | Guide | Page | Docling | PyMuPDF | Remarque |",
        "|---|---|---|---|---|---|",
    ]
    details = []
    for i, (doc_ref, doc, table) in enumerate(chosen, start=1):
        prov = table.prov[0]
        page_height = doc.pages[prov.page_no].size.height
        raw = pymupdf_text(RAW_DIR / f"{doc_ref}.pdf", prov.page_no, prov.bbox, page_height)
        lines.append(f"| {i} | {doc_ref} | {prov.page_no} | ? | ? | |")
        details += [
            f"## Tableau {i} — {doc_ref}, page {prov.page_no}",
            "",
            "### Docling",
            "",
            table.export_to_markdown(doc=doc),
            "",
            "### PyMuPDF (texte brut de la même zone)",
            "",
            "```",
            raw,
            "```",
            "",
        ]

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines + ["", "---", ""] + details), encoding="utf-8")
    print(f"{len(chosen)} tableaux écrits dans {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
