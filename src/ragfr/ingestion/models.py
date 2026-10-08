from typing import Literal

from pydantic import BaseModel, Field

ElementKind = Literal["heading", "paragraph", "list_item", "table", "caption", "footnote", "code"]


class CorpusEntry(BaseModel):
    """Une ligne de data/corpus.csv."""

    doc_ref: str
    titre: str
    theme: str
    url: str
    date_maj: str


class Element(BaseModel):
    """Un bloc du document : titre, paragraphe, tableau..."""

    kind: ElementKind
    text: str
    page: int  # page physique du PDF (1 = première feuille), pas le numéro imprimé
    page_end: int
    section_path: list[str] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    """Sortie de la Partie 1, lue par le chunking (Partie 2)."""

    doc_ref: str
    titre: str
    theme: str
    url: str
    date_maj: str
    source_sha256: str  # empreinte du PDF : on ne re-parse que s'il change
    n_pages: int
    elements: list[Element]

    @property
    def n_tables(self) -> int:
        return sum(e.kind == "table" for e in self.elements)

    @property
    def n_headings(self) -> int:
        return sum(e.kind == "heading" for e in self.elements)
