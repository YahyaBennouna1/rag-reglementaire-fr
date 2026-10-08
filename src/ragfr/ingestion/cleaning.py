"""Nettoyage du texte extrait des PDF de l'ANSSI.

Chaque règle corrige un défaut observé dans les guides (voir tests/test_cleaning.py).
"""

import re
import unicodedata

# Zone Unicode « à usage privé » : glyphes de polices décoratives, illisibles hors du PDF.
PRIVATE_USE = re.compile(r"[-]")
# « Figure » est écrit dans une police décorative : F + glyphes privés.
FIGURE_GLYPHS = re.compile(r"^F[-]+")
# Césure de fin de ligne : « applica- tions » -> « applications ».
HYPHENATION = re.compile(r"(\w)-\s+([a-zà-ÿ])")
# Puce carrée (police Wingdings) extraite comme la lettre « n ».
WINGDINGS_BULLET = re.compile(r"^n\s+")
# Points décoratifs en tête des encadrés de recommandation : « . . . Chaque conteneur… »
LEADING_DOTS = re.compile(r"^(?:\.\s*)+")
SPACES = re.compile(r"[ \t ]+")
# Étiquette d'encadré seule (« R2 », « R12 - - », « R5 + ») : Docling la place souvent
# loin de sa recommandation, donc on la retire plutôt que de mal l'attribuer.
ORPHAN_RECO_LABEL = re.compile(r"^R\d+(?:\s*[+-])*$")


def fix_hyphenation(text: str) -> str:
    return HYPHENATION.sub(r"\1\2", text)


def clean_text(text: str, kind: str = "paragraph") -> str:
    text = FIGURE_GLYPHS.sub("Figure", text)
    text = PRIVATE_USE.sub("", text)
    # NFKC remplace les ligatures typographiques (ﬁ, ﬀ) par des lettres normales.
    text = unicodedata.normalize("NFKC", text)
    text = fix_hyphenation(text)
    if kind == "list_item":
        text = WINGDINGS_BULLET.sub("", text)
    text = LEADING_DOTS.sub("", text)
    text = SPACES.sub(" ", text)
    # On garde les retours à la ligne (utiles dans les tableaux), sans espaces autour.
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def is_noise(text: str) -> bool:
    """Vrai si le bloc est à jeter : rien de lisible (« . ») ou étiquette orpheline (« R2 »)."""
    return not any(ch.isalnum() for ch in text) or bool(ORPHAN_RECO_LABEL.match(text))
