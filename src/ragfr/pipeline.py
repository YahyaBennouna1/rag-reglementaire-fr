"""Assemble les briques décrites dans la config (le YAML décide, le code exécute)."""

import os
from functools import cache
from pathlib import Path

from ragfr.agent.graph import build_agent
from ragfr.citations.verify import verify_answer
from ragfr.config import Config, load_config
from ragfr.embeddings import Embedder
from ragfr.generation import Answer, generate_answer
from ragfr.guardrails.injection import is_injection, neutralize_tags
from ragfr.guardrails.pii import mask_pii
from ragfr.index import collection_name, get_client
from ragfr.query.transforms import TransformingRetriever
from ragfr.retrieval.base import Retriever
from ragfr.retrieval.bm25 import BM25Retriever
from ragfr.retrieval.dense import DenseRetriever
from ragfr.retrieval.hybrid import HybridRetriever
from ragfr.retrieval.reranker import Reranker, RerankingRetriever

ROOT = Path(__file__).resolve().parents[2]


REFUSAL = (
    "Question refusée : elle ressemble à une tentative de détourner l'assistant. "
    "Posez une question sur les recommandations de l'ANSSI."
)


@cache
def production_config() -> Config:
    """La config utilisée en service (API, serveur MCP) : RAGFR_CONFIG, sinon configs/production.yaml."""
    return load_config(os.environ.get("RAGFR_CONFIG", ROOT / "configs" / "production.yaml"))


@cache
def get_embedder(model_name: str) -> Embedder:
    return Embedder(model_name)


@cache
def get_reranker(model_name: str) -> Reranker:
    return Reranker(model_name)


def make_retriever(cfg: Config) -> Retriever:
    client, collection = get_client(), collection_name(cfg)
    r = cfg.retrieval

    if r.mode == "dense":
        retriever = DenseRetriever(client, collection, get_embedder(r.embedding_model))
    elif r.mode == "bm25":
        retriever = BM25Retriever(client, collection)
    else:
        retriever = HybridRetriever(
            BM25Retriever(client, collection),
            DenseRetriever(client, collection, get_embedder(r.embedding_model)),
            candidates=r.candidates,
            rrf_k=r.rrf_k,
            bm25_weight=r.bm25_weight,
        )

    if r.reranker:
        reranker = get_reranker(r.reranker_model)
        retriever = RerankingRetriever(retriever, reranker, candidates=r.rerank_candidates)
    return retriever


def make_search(cfg: Config) -> Retriever:
    """La recherche complète hors agent : moteur + (option) routeur et HyDE."""
    retriever = make_retriever(cfg)
    if cfg.query.router or cfg.query.hyde:
        retriever = TransformingRetriever(
            retriever,
            cfg.query.router,
            cfg.query.hyde,
            cfg.llm.fast_model,
            cfg.query.original_weight,
            cfg.query.decomposition_fusion,
        )
    return retriever


def answer_question(cfg: Config, question: str) -> Answer:
    """Point d'entrée unique pour répondre (utilisé par l'évaluation, l'API et le serveur MCP)."""
    if cfg.guardrails.enabled:
        if cfg.guardrails.mask_pii:
            # En premier : aucune donnée personnelle ne part vers un LLM, ni ne finit dans le cache.
            question, _ = mask_pii(question)
        question = neutralize_tags(question)
        g = cfg.guardrails
        if is_injection(question, g.injection_model, g.injection_threshold, g.injection_classifier):
            # Ni recherche ni génération : on ne donne aucune prise à l'attaque.
            return Answer(text=REFUSAL, sentences=[], citations=[], abstained=True, passages=[], blocked=True)
    if cfg.agent.enabled:
        state = build_agent(cfg, make_retriever(cfg)).invoke({"question": question})
        return state["answer"]
    passages = make_search(cfg).search(question, cfg.retrieval.top_k)
    answer = generate_answer(question, passages, cfg.llm.model, cfg.llm.temperature)
    if cfg.citations.verify:
        answer, reliable = verify_answer(answer, cfg.llm.judge_model)
        if not reliable:  # sans agent, pas de nouvelle recherche : on s'abstient
            text = "Je ne sais pas : la réponse trouvée n'est pas assez soutenue par les guides."
            answer = answer.model_copy(update={"text": text, "abstained": True, "sentences": []})
    return answer
