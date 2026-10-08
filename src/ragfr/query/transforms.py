"""Adapter la recherche au type de question.

- simple           -> on cherche avec la question telle quelle ;
- vague            -> multi-query : 3 reformulations + la question d'origine, résultats fusionnés par RRF ;
- multi_documents  -> décomposition : une sous-question par document, résultats fusionnés par RRF.
HyDE (option) : la recherche dense utilise une réponse hypothétique, BM25 garde la question d'origine.
"""

from typing import Literal

from pydantic import BaseModel

from ragfr.llm import complete_json
from ragfr.models import Passage
from ragfr.retrieval.rrf import reciprocal_rank_fusion

RouteName = Literal["simple", "vague", "multi_documents"]


class Route(BaseModel):
    route: RouteName


class Queries(BaseModel):
    questions: list[str]


class Hypothetical(BaseModel):
    reponse: str


ROUTER_PROMPT = """Classe cette question posée à un assistant sur les guides de cybersécurité de l'ANSSI.
- "simple" : une question précise sur un seul sujet ;
- "vague" : une question courte, floue ou sans les termes techniques ;
- "multi_documents" : une question qui compare ou croise plusieurs sujets ou plusieurs guides.
Question : {question}
Réponds en JSON : {{"route": "simple" | "vague" | "multi_documents"}}"""

MULTI_QUERY_PROMPT = """Écris 3 reformulations de cette question, avec le vocabulaire technique
qu'utiliserait un guide de cybersécurité de l'ANSSI (termes précis, synonymes).
Question : {question}
Réponds en JSON : {{"questions": ["...", "...", "..."]}}"""

DECOMPOSE_PROMPT = """Découpe cette question en 2 à 4 sous-questions simples, chacune sur un seul sujet,
pour chercher chaque partie séparément dans les guides de l'ANSSI.
Question : {question}
Réponds en JSON : {{"questions": ["...", "..."]}}"""

HYDE_PROMPT = """Écris un court paragraphe (4 phrases maximum), dans le style d'un guide de l'ANSSI,
qui répondrait à cette question. Peu importe s'il n'est pas exact : il sert seulement à chercher.
Question : {question}
Réponds en JSON : {{"reponse": "..."}}"""


def ask(prompt: str, model: str, schema):
    return complete_json([{"role": "user", "content": prompt}], model=model, schema=schema)


def classify(question: str, model: str) -> RouteName:
    return ask(ROUTER_PROMPT.format(question=question), model, Route).route


def expand_queries(question: str, route: RouteName, model: str) -> list[str]:
    """Les requêtes à lancer pour cette question. La question d'origine est toujours gardée."""
    if route == "vague":
        return [question, *ask(MULTI_QUERY_PROMPT.format(question=question), model, Queries).questions]
    if route == "multi_documents":
        return [question, *ask(DECOMPOSE_PROMPT.format(question=question), model, Queries).questions]
    return [question]


def hypothetical_answer(question: str, model: str) -> str:
    return ask(HYDE_PROMPT.format(question=question), model, Hypothetical).reponse


def multi_search(retriever, queries: list[str], k: int, hyde_text: str | None = None) -> list[Passage]:
    """Lance une recherche par requête et fusionne les listes par RRF.

    HyDE ne remplace la recherche dense que pour la question d'origine (la première de la liste).
    """
    results = [
        retriever.search(q, k, dense_query=hyde_text if i == 0 else None) for i, q in enumerate(queries)
    ]
    if len(results) == 1:
        return results[0]
    return reciprocal_rank_fusion(results)[:k]


class TransformingRetriever:
    """Enveloppe un moteur de recherche : routeur, puis multi-query / décomposition / HyDE."""

    def __init__(self, base, router: bool, hyde: bool, model: str):
        self.base = base
        self.router = router
        self.hyde = hyde
        self.model = model
        self.last_route: RouteName = "simple"  # gardé pour mesurer l'exactitude du routeur

    def search(self, query: str, k: int, dense_query: str | None = None) -> list[Passage]:
        self.last_route = classify(query, self.model) if self.router else "simple"
        queries = expand_queries(query, self.last_route, self.model)
        hyde_text = hypothetical_answer(query, self.model) if self.hyde else dense_query
        return multi_search(self.base, queries, k, hyde_text)
