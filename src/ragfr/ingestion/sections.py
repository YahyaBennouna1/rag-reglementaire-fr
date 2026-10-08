"""Reconstruit la hiérarchie des sections à partir de la numérotation des titres.

Docling donne le même niveau à tous les titres des guides ANSSI. On s'appuie donc
sur leur numéro : « 2 » est une section, « 2.1 » une sous-section de « 2 ».
Un titre non numéroté (souvent le titre d'une recommandation) est rattaché
à la dernière section numérotée.
"""

import re

from ragfr.ingestion.models import Element

NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")
ANNEX = re.compile(r"^([A-Z])\s+[A-ZÀ-Ý]")
LONE_NUMBER = re.compile(r"^\d+(?:\.\d+)*\.?$")


def heading_depth(title: str) -> int | None:
    """« 2.1 Titre » -> 2, « A Annexe » -> 1, titre non numéroté -> None."""
    if m := NUMBERED.match(title):
        return m.group(1).count(".") + 1
    if ANNEX.match(title):
        return 1
    return None


def merge_lone_numbers(elements: list[Element]) -> list[Element]:
    """Fusionne un titre « 2 » isolé avec le titre qui le suit : « 2 Recommandations »."""
    merged: list[Element] = []
    pending: Element | None = None
    for el in elements:
        if el.kind == "heading" and LONE_NUMBER.match(el.text):
            pending = el
            continue
        if pending is not None:
            if el.kind == "heading":
                el = el.model_copy(update={"text": f"{pending.text.rstrip('.')} {el.text}"})
            else:
                merged.append(pending)
            pending = None
        merged.append(el)
    if pending is not None:
        merged.append(pending)
    return merged


def assign_sections(elements: list[Element]) -> list[Element]:
    """Renvoie les éléments avec leur chemin de section rempli."""
    numbered: list[tuple[int, str]] = []  # pile des sections numérotées ouvertes
    leaf: str | None = None  # dernier titre non numéroté
    result = []
    for el in merge_lone_numbers(elements):
        if el.kind == "heading":
            depth = heading_depth(el.text)
            if depth is None:
                leaf = el.text
            else:
                while numbered and numbered[-1][0] >= depth:
                    numbered.pop()
                numbered.append((depth, el.text))
                leaf = None
        path = [title for _, title in numbered] + ([leaf] if leaf else [])
        result.append(el.model_copy(update={"section_path": path}))
    return result
