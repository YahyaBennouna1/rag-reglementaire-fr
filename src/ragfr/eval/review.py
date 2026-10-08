"""Ce qui sert à relire une question : la grille de critères et le passage source.

Utilisé par la relecture humaine (scripts/review_questions.py) ET par la relecture automatique
(scripts/auto_review.py) : les deux jugent avec exactement la même grille et la même source.
"""

import re
from pathlib import Path

from ragfr.eval.retrieval_metrics import normalize
from ragfr.ingestion.models import ParsedDocument

ROOT = Path(__file__).resolve().parents[3]
PARSED_DIR = ROOT / "data" / "parsed"

# On ne juge pas si la réponse est vraie dans l'absolu : on juge si elle est FIDÈLE AU GUIDE.
CRITERIA = [
    ("extrait_prouve", "1. L'extrait (ou sa ligne de tableau) PROUVE-t-il la réponse ?"),
    ("reponse_complete", "2. La réponse est-elle COMPLÈTE (le passage ne dit pas plus) ?"),
    ("question_claire", "3. La question se comprend-elle SEULE, sans le guide sous les yeux ?"),
    ("une_seule_reponse", "4. N'y a-t-il qu'UNE bonne réponse (pas d'autre passage contradictoire) ?"),
]
UNANSWERABLE_CRITERIA = [
    ("hors_corpus", "1. Les guides ne répondent-ils VRAIMENT pas (cherche dans data/parsed/*.md) ?"),
    ("question_claire", "2. La question se comprend-elle seule et reste-t-elle proche des thèmes ?"),
]

_docs: dict[str, ParsedDocument] = {}


def source_context(doc_ref: str, extrait: str, width: int = 1500) -> str:
    """Le texte du guide autour de l'extrait : c'est la référence pour juger."""
    if doc_ref not in _docs:
        _docs[doc_ref] = ParsedDocument.model_validate_json(
            (PARSED_DIR / f"{doc_ref}.json").read_text(encoding="utf-8")
        )
    elements = _docs[doc_ref].elements
    target = normalize(extrait)
    for i, el in enumerate(elements):
        if target and target in normalize(el.text):
            around = elements[max(0, i - 2) : i + 3]
            # Les tableaux Markdown ont de très longues lignes de tirets et d'espaces : on les raccourcit.
            text = "\n".join(e.text for e in around)
            text = re.sub(r"-{4,}", "---", text)
            text = re.sub(r" {2,}", " ", text)
            section = " > ".join(el.section_path)
            return f"[{section}]\n{text[:width]}{'…' if len(text) > width else ''}"
    return "(passage source introuvable)"
