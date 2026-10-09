"""Évaluation des réponses par un juge LLM : fidélité, exactitude, pertinence.

Un seul appel au juge par question, qui renvoie les trois verdicts : moins d'appels, donc moins
de quota consommé. Le juge est d'une autre famille que le générateur (biais d'auto-préférence).

Le juge ne reçoit que les passages CITÉS par la réponse : une information appuyée sur un passage
non cité n'est pas vérifiable par l'utilisateur, donc pas fidèle. Et la requête est 3 fois plus
courte (environ 2 000 tokens au lieu de 6 000).
"""

from pydantic import BaseModel

from ragfr.eval.dataset import EvalQuestion
from ragfr.generation import Answer, format_passages
from ragfr.llm import complete_json

JUDGE_MAX_TOKENS = 500  # un verdict JSON court ; voir judge_answer


class AnswerJudgement(BaseModel):
    fidele: bool  # tout ce que dit la réponse est dans les passages
    exacte: bool  # la réponse est correcte par rapport à la réponse de référence
    pertinente: bool  # la réponse répond bien à la question posée
    explication: str = ""


JUDGE_PROMPT = """Tu évalues la réponse d'un assistant sur les guides de l'ANSSI.

Passages cités par l'assistant :
{passages}

Question : {question}
Réponse de référence (validée) : {reference}
Réponse de l'assistant : {answer}

Réponds à trois questions par vrai ou faux :
- "fidele" : chaque information de la réponse de l'assistant se trouve-t-elle dans les passages cités ?
- "exacte" : contient-elle l'essentiel de la réponse de référence, sans la contredire ?
- "pertinente" : la réponse de l'assistant répond-elle à la question posée ?
Réponds en JSON : {{"fidele": true, "exacte": true, "pertinente": true, "explication": "une phrase"}}"""


def judge_answer(question: EvalQuestion, answer: Answer, model: str) -> AnswerJudgement:
    # On garde les numéros d'origine : la réponse cite « [P3] », le juge doit voir un passage P3.
    cited_ids = {c.passage_id for c in answer.citations}
    numbered = [(i, p) for i, p in enumerate(answer.passages, start=1) if p.id in cited_ids]
    numbers = [i for i, _ in numbered]
    cited = [p for _, p in numbered]
    prompt = JUDGE_PROMPT.format(
        passages=format_passages(cited, numbers) if cited else "(aucun passage cité)",
        question=question.question,
        reference=question.reponse_reference,
        answer=answer.text,
    )
    # max_tokens explicite : sans lui, Groq réserve une sortie par défaut qui dépasse la limite
    # de tokens de sortie par minute de certains comptes (OTPM 1 000), et refuse la requête.
    messages = [{"role": "user", "content": prompt}]
    return complete_json(messages, model=model, schema=AnswerJudgement, max_tokens=JUDGE_MAX_TOKENS)
