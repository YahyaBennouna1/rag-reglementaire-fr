"""Chaque phrase de la réponse est-elle vraiment soutenue par les passages qu'elle cite ?

Règle de sortie (guide du projet) :
- une phrase « non_soutenu » est retirée de la réponse ;
- si plus d'un tiers des phrases sont retirées, la réponse n'est pas fiable : l'agent recherche
  à nouveau ou s'abstient.
"""

from typing import Literal

from pydantic import BaseModel

from ragfr.generation import Answer, Citation, Sentence
from ragfr.llm import complete_json

Verdict = Literal["soutenu", "partiel", "non_soutenu"]
MAX_REMOVED_SHARE = 1 / 3


class Judgement(BaseModel):
    verdict: Verdict
    explication: str = ""


JUDGE_PROMPT = """Tu vérifies une citation. Voici un ou plusieurs passages d'un guide de l'ANSSI :
{passages}

Phrase à vérifier : « {phrase} »

- "soutenu" : les passages disent clairement ce que la phrase affirme ;
- "partiel" : les passages soutiennent une partie seulement, ou la phrase exagère un peu ;
- "non_soutenu" : les passages ne disent pas cela (ou disent autre chose).
Juge seulement à partir des passages, pas de tes connaissances.
Réponds en JSON : {{"verdict": "...", "explication": "une phrase"}}"""


def judge_sentence(sentence: Sentence, passages_text: str, model: str) -> Verdict:
    if not passages_text:
        return "non_soutenu"  # une phrase sans source valide n'est pas prouvée
    prompt = JUDGE_PROMPT.format(passages=passages_text, phrase=sentence.phrase)
    return complete_json([{"role": "user", "content": prompt}], model=model, schema=Judgement).verdict


def verify_answer(answer: Answer, model: str) -> tuple[Answer, bool]:
    """Renvoie (réponse nettoyée, fiable ?). Les citations reçoivent leur verdict."""
    if answer.abstained:
        return answer, True

    by_label = {f"P{i}": p for i, p in enumerate(answer.passages, start=1)}
    kept: list[Sentence] = []
    citations: list[Citation] = []
    for sentence in answer.sentences:
        cited = [by_label[s] for s in sentence.sources if s in by_label]
        passages_text = "\n\n".join(f"[{p.titre}, p. {p.page}]\n{p.text}" for p in cited)
        verdict = judge_sentence(sentence, passages_text, model)
        if verdict != "non_soutenu":
            kept.append(sentence)
        for p in cited:
            citations.append(
                Citation(
                    phrase=sentence.phrase, passage_id=p.id, doc_ref=p.doc_ref, page=p.page, verdict=verdict
                )
            )

    removed = len(answer.sentences) - len(kept)
    reliable = bool(kept) and removed <= MAX_REMOVED_SHARE * len(answer.sentences)
    text = " ".join(f"{s.phrase} [{', '.join(s.sources)}]" for s in kept)
    cleaned = answer.model_copy(update={"text": text, "sentences": kept, "citations": citations})
    return cleaned, reliable
