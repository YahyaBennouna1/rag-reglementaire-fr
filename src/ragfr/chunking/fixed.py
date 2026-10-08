"""Découpage à taille fixe : une fenêtre de N tokens qui glisse avec un chevauchement.

C'est la méthode de référence (baseline). Le texte d'un document est mis bout à bout,
puis coupé tous les `size` tokens. Les tableaux sont traités à part et restent entiers.
"""

from bisect import bisect_right

from ragfr.chunking.tables import split_table
from ragfr.ingestion.models import Element, ParsedDocument
from ragfr.models import Passage
from ragfr.tokens import count_tokens, get_tokenizer

SEPARATOR = "\n\n"


def _page_range(elements: list[Element]) -> tuple[int, int]:
    return min(e.page for e in elements), max(e.page_end for e in elements)


def chunk_fixed(doc: ParsedDocument, size: int = 512, overlap: int = 64) -> list[Passage]:
    texts = [e for e in doc.elements if e.kind != "table"]
    tables = [e for e in doc.elements if e.kind == "table"]

    # 1. Mettre le texte bout à bout, en notant où commence chaque élément.
    full_text = ""
    starts = []  # position (en caractères) du début de chaque élément dans full_text
    for el in texts:
        starts.append(len(full_text))
        full_text += el.text + SEPARATOR

    # 2. Tokeniser une seule fois, en gardant la position de chaque token dans le texte.
    encoding = get_tokenizer()(full_text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoding["offset_mapping"]  # [(début, fin), ...] en caractères, un par token

    passages = []

    def add(text, elements, is_table=False):
        page, page_end = _page_range(elements)
        passages.append(
            Passage(
                id=f"{doc.doc_ref}:{len(passages):04d}",
                doc_ref=doc.doc_ref,
                titre=doc.titre,
                page=page,
                page_end=page_end,
                section=" > ".join(elements[0].section_path),
                text=text.strip(),
                is_table=is_table,
            )
        )

    # 3. Faire glisser une fenêtre de `size` tokens, en reculant de `overlap` à chaque pas.
    start = 0
    while start < len(offsets):
        end = min(start + size, len(offsets))
        char_start, char_end = offsets[start][0], offsets[end - 1][1]
        # Les éléments touchés par la fenêtre donnent les pages et la section.
        first = bisect_right(starts, char_start) - 1
        last = bisect_right(starts, char_end - 1) - 1
        add(full_text[char_start:char_end], texts[first : last + 1])
        if end == len(offsets):
            break
        start = end - overlap

    # 4. Les tableaux : un chunk par tableau (ou par groupe de lignes s'il est trop long).
    for table in tables:
        for piece in split_table(table.text, size, count_tokens):
            add(piece, [table], is_table=True)

    return passages
