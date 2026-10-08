"""Parse les PDF de data/raw/ avec Docling et écrit le résultat dans data/parsed/.

Pour chaque guide, trois fichiers :
- <doc_ref>.docling.json : la sortie brute de Docling (l'étape lente, gardée en cache) ;
- <doc_ref>.md           : un export Markdown, pour relire à l'œil ;
- <doc_ref>.json         : nos éléments nettoyés, lus par le chunking.

Docling n'est relancé que si le PDF a changé (empreinte SHA-256) ou avec --force.
Le nettoyage, rapide, est refait à chaque lancement à partir du cache :
une amélioration du nettoyage ne coûte donc pas un nouveau parsing.
"""

import argparse
import hashlib
import json
import time
from pathlib import Path

from docling_core.types.doc import DoclingDocument

from ragfr.ingestion.corpus import load_corpus
from ragfr.ingestion.docling_parser import convert, make_converter, to_elements
from ragfr.ingestion.models import ParsedDocument

ROOT = Path(__file__).resolve().parent.parent
CORPUS_CSV = ROOT / "data" / "corpus.csv"
RAW_DIR = ROOT / "data" / "raw"
PARSED_DIR = ROOT / "data" / "parsed"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_hash(out_path: Path) -> str | None:
    if not out_path.exists():
        return None
    return json.loads(out_path.read_text(encoding="utf-8")).get("source_sha256")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="*", help="doc_ref à traiter (par défaut : tous)")
    parser.add_argument("--force", action="store_true", help="relance Docling même si le PDF n'a pas changé")
    args = parser.parse_args()

    entries = load_corpus(CORPUS_CSV)
    if args.only:
        entries = [e for e in entries if e.doc_ref in args.only]
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    converter = None  # créé à la première conversion seulement (chargement des modèles)
    failures = []
    for entry in entries:
        pdf = RAW_DIR / f"{entry.doc_ref}.pdf"
        out = PARSED_DIR / f"{entry.doc_ref}.json"
        docling_cache = PARSED_DIR / f"{entry.doc_ref}.docling.json"
        if not pdf.exists():
            print(f"[ERREUR]  {entry.doc_ref} : PDF absent (lancer download_corpus.py)")
            failures.append(entry.doc_ref)
            continue

        pdf_hash = sha256(pdf)
        use_cache = not args.force and docling_cache.exists() and previous_hash(out) == pdf_hash
        start = time.perf_counter()
        try:
            if use_cache:
                doc = DoclingDocument.load_from_json(docling_cache)
            else:
                converter = converter or make_converter()
                doc = convert(converter, pdf)
                doc.save_as_json(docling_cache)
                (PARSED_DIR / f"{entry.doc_ref}.md").write_text(doc.export_to_markdown(), encoding="utf-8")
            elements = to_elements(doc)
        except Exception as e:  # un PDF illisible ne doit pas arrêter les autres
            print(f"[ERREUR]  {entry.doc_ref} : {type(e).__name__}: {e}")
            failures.append(entry.doc_ref)
            continue

        parsed = ParsedDocument(
            **entry.model_dump(),
            source_sha256=pdf_hash,
            n_pages=doc.num_pages(),
            elements=elements,
        )
        out.write_text(parsed.model_dump_json(indent=1), encoding="utf-8")

        secs = time.perf_counter() - start
        label = "[cache]  " if use_cache else "[docling]"
        print(
            f"{label} {entry.doc_ref} : {parsed.n_pages} pages, {len(elements)} éléments, "
            f"{parsed.n_tables} tableaux, {secs:.0f} s"
        )

    print(f"\n{len(entries) - len(failures)}/{len(entries)} guides traités")
    if failures:
        print("Échecs :", ", ".join(failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
