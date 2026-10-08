from ragfr.chunking.fixed import chunk_fixed
from ragfr.chunking.tables import split_table
from ragfr.ingestion.models import Element, ParsedDocument
from ragfr.tokens import count_tokens


def words(text: str) -> int:
    return len(text.split())


TABLE = "TABLE 1 - Niveaux\n\n| Mesure | Niveau |\n|---|---|\n| a | 1 |\n| b | 2 |\n| c | 3 |"


def test_petit_tableau_garde_entier():
    assert split_table(TABLE, max_tokens=100, count=words) == [TABLE]


def test_grand_tableau_coupe_par_lignes_avec_en_tete():
    pieces = split_table(TABLE, max_tokens=13, count=words)
    assert len(pieces) > 1
    for piece in pieces:
        assert piece.startswith("TABLE 1 - Niveaux\n\n| Mesure | Niveau |\n|---|---|")
    rows = [line for piece in pieces for line in piece.split("\n")[4:]]
    assert rows == ["| a | 1 |", "| b | 2 |", "| c | 3 |"]  # aucune ligne perdue ni dupliquée


def make_doc(elements: list[Element]) -> ParsedDocument:
    return ParsedDocument(
        doc_ref="test",
        titre="Guide de test",
        theme="administration",
        url="https://exemple.fr/test.pdf",
        date_maj="2026-01-01",
        source_sha256="0" * 64,
        n_pages=3,
        elements=elements,
    )


def test_fenetres_de_taille_fixe_avec_chevauchement():
    paragraphs = [
        Element(
            kind="paragraph",
            text=f"Phrase numéro {i} sur la sécurité.",
            page=1 + i // 40,
            page_end=1 + i // 40,
        )
        for i in range(120)
    ]
    passages = chunk_fixed(make_doc(paragraphs), size=64, overlap=16)

    assert len(passages) > 3
    assert all(count_tokens(p.text) <= 64 + 2 for p in passages)  # +2 : bords de mots retokenisés
    # Le début de chaque passage reprend la fin du précédent (chevauchement).
    for prev, nxt in zip(passages, passages[1:], strict=False):
        assert nxt.text[:15] in prev.text
    assert passages[0].page == 1 and passages[-1].page_end == 3


def test_tableau_jamais_mele_au_texte():
    elements = [
        Element(kind="paragraph", text="Introduction.", page=1, page_end=1, section_path=["1 Intro"]),
        Element(kind="table", text=TABLE, page=2, page_end=2, section_path=["2 Mesures"]),
    ]
    passages = chunk_fixed(make_doc(elements), size=512, overlap=64)
    tables = [p for p in passages if p.is_table]
    assert len(tables) == 1
    assert tables[0].text == TABLE
    assert tables[0].section == "2 Mesures" and tables[0].page == 2
    assert "| Mesure |" not in passages[0].text
