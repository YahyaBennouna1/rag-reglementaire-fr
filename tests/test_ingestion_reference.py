"""Test de non-régression du parsing sur un PDF de référence.

Lent (Docling sur 22 pages, environ 2 minutes) : lancé avec `uv run pytest -m slow`.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
REFERENCE_PDF = ROOT / "data" / "raw" / "guide-conteneurs.pdf"


@pytest.mark.slow
@pytest.mark.skipif(not REFERENCE_PDF.exists(), reason="lancer scripts/download_corpus.py")
def test_pdf_de_reference_stable():
    from ragfr.ingestion.docling_parser import convert, make_converter, to_elements

    elements = to_elements(convert(make_converter(), REFERENCE_PDF))
    tables = [e for e in elements if e.kind == "table"]
    headings = [e for e in elements if e.kind == "heading"]

    assert len(tables) == 2
    assert len(headings) == 47
    expected_path = ["2 Recommandations", "2.1 Cloisonnement du conteneur"]
    assert any(e.section_path[:2] == expected_path for e in elements)
