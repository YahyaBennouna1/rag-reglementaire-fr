"""L'objet Passage : il circule de l'indexation jusqu'aux citations."""

from pydantic import BaseModel


class Passage(BaseModel):
    id: str  # "<doc_ref>:<numéro>", ex. "openssh:0042"
    doc_ref: str
    titre: str  # titre du guide, affiché dans les sources
    page: int  # page physique de début
    page_end: int
    section: str  # chemin de section, ex. "2 Recommandations > 2.1 Cloisonnement"
    text: str  # texte affiché et cité
    is_table: bool = False
    score: float = 0.0  # rempli par la recherche

    @property
    def index_text(self) -> str:
        """Texte indexé : le chemin de section donne le contexte que le passage seul n'a pas."""
        return f"{self.section}\n\n{self.text}" if self.section else self.text
