from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    # Refuse les clés inconnues : une faute de frappe dans le YAML fait planter.
    model_config = ConfigDict(extra="forbid")


class ChunkingConfig(StrictModel):
    method: Literal["fixed", "semantic", "contextual"] = "fixed"
    size: int = Field(512, gt=0)
    overlap: int = Field(64, ge=0)

    @model_validator(mode="after")
    def check_overlap(self) -> "ChunkingConfig":
        if self.overlap >= self.size:
            raise ValueError("overlap doit être strictement plus petit que size")
        return self


class RetrievalConfig(StrictModel):
    mode: Literal["dense", "bm25", "hybrid"] = "dense"
    # Modèle d'embedding. bge-m3 (meilleur, 2,2 Go) ne tient pas dans 8 Go de RAM avec le reste du système.
    embedding_model: str = "intfloat/multilingual-e5-base"
    top_k: int = Field(10, gt=0)
    # Hybride : nombre de résultats demandés à BM25 et au dense avant la fusion RRF.
    candidates: int = Field(50, gt=0)
    rrf_k: int = Field(60, gt=0)
    # Poids de BM25 dans la fusion (le dense garde 1) : > 1 = plus de confiance aux mots exacts.
    bm25_weight: float = Field(1.0, gt=0)
    reranker: bool = False
    # Reranker léger par défaut : bge-reranker-v2-m3 (2,2 Go) ferait swapper un PC à 8 Go de RAM.
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    # Le reranker renote N candidats pour en garder top_k : il en faut au moins top_k.
    rerank_candidates: int = Field(30, gt=0)

    @model_validator(mode="after")
    def check_rerank_candidates(self) -> "RetrievalConfig":
        if self.rerank_candidates < self.top_k:
            raise ValueError("rerank_candidates doit être >= top_k")
        return self


class LLMConfig(StrictModel):
    # Génère les réponses. Les noms suivent LiteLLM : "fournisseur/modèle".
    model: str = "gemini/gemini-3.5-flash-lite"
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    # Note les réponses : une autre famille que le générateur, pour qu'un modèle ne se juge pas lui-même.
    judge_model: str = "groq/openai/gpt-oss-120b"
    # Petites tâches rapides et fréquentes (routeur, juge de l'agent, reformulation).
    # Gratuit : Qwen sur Groq épuisait son quota de 200 000 tokens par jour.
    fast_model: str = "gemini/gemini-3.5-flash-lite"


class QueryConfig(StrictModel):
    # Le routeur classe la question (simple / vague / multi_documents) et choisit la transformation.
    router: bool = False
    # HyDE : chercher avec une réponse hypothétique (recherche dense seulement).
    hyde: bool = False


class AgentConfig(StrictModel):
    # Agent correctif : juge les passages, reformule et recherche à nouveau, ou s'abstient.
    enabled: bool = False
    max_rewrites: int = Field(2, ge=0)


class CitationsConfig(StrictModel):
    # Un juge vérifie chaque phrase ; les phrases non soutenues sont retirées.
    verify: bool = False


class Config(StrictModel):
    name: str
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    query: QueryConfig = Field(default_factory=QueryConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    citations: CitationsConfig = Field(default_factory=CitationsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


def load_config(path: str | Path) -> Config:
    """Lit un fichier YAML et renvoie une Config validée."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)
