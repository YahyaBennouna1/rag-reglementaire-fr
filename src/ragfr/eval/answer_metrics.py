"""Évaluation des réponses par un juge LLM : fidélité, exactitude, pertinence.

Un seul appel au juge par question, qui renvoie les trois verdicts : moins d'appels, donc moins
de quota consommé. Le juge est d'une autre famille que le générateur (biais d'auto-préférence).
"""

from pydantic import BaseModel

from ragfr.eval.dataset import EvalQuestion
from ragfr.generation import Answer, format_passages
from ragfr.llm import complete_json


class AnswerJudgement(BaseModel):
    fidele: bool  # tout ce que dit la réponse est dans les passages
    exacte: bool  # la réponse est correcte par rapport à la réponse de référence
    pertinente: bool  # la réponse répond bien à la question posée
    explication: str = ""


JUDGE_PROMPT = """Tu évalues la réponse d'un assistant sur les guides de l'ANSSI.

Passages fournis à l'assistant :
{passages}

Question : {question}
Réponse de référence (écrite par un humain) : {reference}
Réponse de l'assistant : {answer}

Réponds à trois questions par vrai ou faux :
- "fidele" : chaque information de la réponse de l'assistant se trouve-t-elle dans les passages ?
- "exacte" : contient-elle l'essentiel de la réponse de référence, sans la contredire ?
- "pertinente" : la réponse de l'assistant répond-elle à la question posée ?
Réponds en JSON : {{"fidele": true, "exacte": true, "pertinente": true, "explication": "une phrase"}}"""


def judge_answer(question: EvalQuestion, answer: Answer, model: str) -> AnswerJudgement:
    prompt = JUDGE_PROMPT.format(
        passages=format_passages(answer.passages),
        question=question.question,
        reference=question.reponse_reference,
        answer=answer.text,
    )
    return complete_json([{"role": "user", "content": prompt}], model=model, schema=AnswerJudgement)
