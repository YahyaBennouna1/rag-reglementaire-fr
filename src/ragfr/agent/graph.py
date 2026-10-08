"""Agent correctif : il ne génère une réponse qu'avec des passages jugés suffisants.

route -> retrieve -> grade --suffisant------------------------------> generate -> FIN
                       |---partiel/insuffisant (essais restants)--> rewrite -> retrieve
                       |---partiel/insuffisant (plus d'essais)----> abstain -> FIN
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from ragfr.config import Config
from ragfr.generation import Answer, format_passages, generate_answer
from ragfr.llm import complete_json
from ragfr.models import Passage
from ragfr.query.transforms import RouteName, classify, expand_queries, hypothetical_answer, multi_search

GradeName = Literal["suffisant", "partiel", "insuffisant"]


class RagState(TypedDict, total=False):
    question: str  # la question de l'utilisateur, jamais modifiée
    search_query: str  # la requête de recherche, reformulée si besoin
    route: RouteName
    passages: list[Passage]
    grade: GradeName
    missing: str  # ce qui manque, selon le juge : guide la reformulation
    rewrites: int
    answer: Answer


class Grade(BaseModel):
    grade: GradeName
    useful: list[str] = Field(default_factory=list)  # ex. ["P1", "P4"]
    missing: str = ""


class Rewrite(BaseModel):
    question: str


GRADE_PROMPT = """Tu évalues si des passages des guides de l'ANSSI permettent de répondre à une question.
{passages}

Question : {question}

- "suffisant" : les passages contiennent tout ce qu'il faut pour répondre ;
- "partiel" : ils répondent à une partie seulement ;
- "insuffisant" : ils ne permettent pas de répondre.
"useful" : les identifiants des passages utiles. "missing" : en une phrase, ce qui manque.
Réponds en JSON : {{"grade": "...", "useful": ["P1"], "missing": "..."}}"""

REWRITE_PROMPT = """Une recherche dans les guides de l'ANSSI n'a pas trouvé assez d'informations.
Question d'origine : {question}
Requête utilisée : {query}
Ce qui manquait : {missing}
Écris une nouvelle requête de recherche, avec d'autres mots, ciblée sur ce qui manque.
Réponds en JSON : {{"question": "..."}}"""


def build_agent(cfg: Config, retriever):
    k = cfg.retrieval.top_k
    fast = cfg.llm.fast_model

    def route(state: RagState) -> RagState:
        name = classify(state["question"], fast) if cfg.query.router else "simple"
        return {"route": name, "search_query": state["question"], "rewrites": 0}

    def retrieve(state: RagState) -> RagState:
        queries = expand_queries(state["search_query"], state["route"], fast)
        hyde_text = hypothetical_answer(state["search_query"], fast) if cfg.query.hyde else None
        return {"passages": multi_search(retriever, queries, k, hyde_text)}

    def grade(state: RagState) -> RagState:
        prompt = GRADE_PROMPT.format(passages=format_passages(state["passages"]), question=state["question"])
        out = complete_json([{"role": "user", "content": prompt}], model=fast, schema=Grade)
        labels = {f"P{i}": p for i, p in enumerate(state["passages"], start=1)}
        useful = [labels[u] for u in out.useful if u in labels]
        # On ne transmet à la génération que les passages jugés utiles (s'il y en a).
        return {"grade": out.grade, "missing": out.missing, "passages": useful or state["passages"]}

    def rewrite(state: RagState) -> RagState:
        prompt = REWRITE_PROMPT.format(
            question=state["question"], query=state["search_query"], missing=state.get("missing", "")
        )
        out = complete_json([{"role": "user", "content": prompt}], model=fast, schema=Rewrite)
        return {"search_query": out.question, "rewrites": state["rewrites"] + 1}

    def generate(state: RagState) -> RagState:
        answer = generate_answer(state["question"], state["passages"], cfg.llm.model, cfg.llm.temperature)
        return {"answer": answer}

    def abstain(state: RagState) -> RagState:
        guides = list(dict.fromkeys(p.titre for p in state["passages"]))[:3]  # sans doublons, dans l'ordre
        text = "Je ne sais pas : les guides ne contiennent pas de réponse suffisante à cette question."
        if guides:
            text += " Documents les plus proches : " + " ; ".join(guides) + "."
        answer = Answer(text=text, sentences=[], citations=[], abstained=True, passages=state["passages"])
        return {"answer": answer}

    def after_grade(state: RagState) -> str:
        if state["grade"] == "suffisant":
            return "generate"
        if state["rewrites"] < cfg.agent.max_rewrites:
            return "rewrite"
        return "abstain"

    graph = StateGraph(RagState)
    for name, node in [
        ("route", route),
        ("retrieve", retrieve),
        ("grade", grade),
        ("rewrite", rewrite),
        ("generate", generate),
        ("abstain", abstain),
    ]:
        graph.add_node(name, node)
    graph.add_edge(START, "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", after_grade, ["generate", "rewrite", "abstain"])
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("abstain", END)
    return graph.compile()
