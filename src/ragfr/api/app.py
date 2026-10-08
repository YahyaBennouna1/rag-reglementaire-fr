"""API web du RAG : les mêmes fonctions que l'évaluation et le serveur MCP, derrière HTTP.

    uv run uvicorn ragfr.api.app:app --port 8000
    puis ouvrir http://localhost:8000/docs (documentation interactive générée automatiquement)

Routes :
- POST /ask    : question -> réponse citée (ou abstention), durée
- POST /search : question -> passages, sans génération
- GET /health  : le programme répond (sonde « liveness » de Kubernetes)
- GET /ready   : le programme peut servir : config chargée, index présent (sonde « readiness »)
"""

import os
import time
from collections import defaultdict, deque
from functools import cache
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from ragfr.index import collection_name, get_client
from ragfr.ingestion.corpus import load_corpus
from ragfr.pipeline import ROOT, answer_question, make_search, production_config

app = FastAPI(
    title="RAG ANSSI",
    description="Questions-réponses sourcées sur 45 guides de cybersécurité de l'ANSSI.",
    version="0.1.0",
)

# --- Schémas d'entrée et de sortie (validés par Pydantic) ---------------------------------------

Theme = Literal["administration", "authentification", "conteneurs", "journalisation"]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class CitationOut(BaseModel):
    phrase: str
    doc_ref: str
    page: int
    verdict: str | None = None


class AskResponse(BaseModel):
    reponse: str
    abstention: bool
    citations: list[CitationOut]
    duree_s: float


class SearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    k: int = Field(5, ge=1, le=20)
    theme: Theme | None = None


class PassageOut(BaseModel):
    doc_ref: str
    titre: str
    page: int
    section: str
    extrait: str
    score: float


# --- Sécurité : clé d'API facultative et limite de débit -----------------------------------------

RATE_LIMIT = int(os.environ.get("RAGFR_RATE_LIMIT", "30"))  # requêtes par minute et par client
_requests: dict[str, deque] = defaultdict(deque)


def check_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Si RAGFR_API_KEY est définie, chaque requête doit envoyer la même valeur dans l'en-tête X-API-Key."""
    expected = os.environ.get("RAGFR_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="clé d'API manquante ou invalide")


def rate_limit(request: Request) -> None:
    """Fenêtre glissante d'une minute par adresse IP : au-delà de RATE_LIMIT requêtes, réponse 429."""
    client = request.client.host if request.client else "inconnu"
    now = time.monotonic()
    window = _requests[client]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="trop de requêtes, réessayez dans une minute")
    window.append(now)


protected = [Depends(check_api_key), Depends(rate_limit)]

# --- Routes ---------------------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    # Ouvrir l'adresse de l'API dans un navigateur mène directement à sa documentation interactive.
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    try:
        cfg = production_config()
        name = collection_name(cfg)
        if not get_client().collection_exists(name):
            raise RuntimeError(f"index absent : {name}")
    except Exception as e:  # toute erreur = pas prêt ; Kubernetes n'envoie pas de trafic
        raise HTTPException(status_code=503, detail=f"pas prêt : {e}") from e
    return {"status": "ready", "config": cfg.name, "collection": name}


@app.post("/ask", response_model=AskResponse, dependencies=protected)
def ask(body: AskRequest) -> AskResponse:
    start = time.perf_counter()
    answer = answer_question(production_config(), body.question)
    return AskResponse(
        reponse=answer.text,
        abstention=answer.abstained,
        citations=[
            CitationOut(phrase=c.phrase, doc_ref=c.doc_ref, page=c.page, verdict=c.verdict)
            for c in answer.citations
        ],
        duree_s=round(time.perf_counter() - start, 2),
    )


@app.post("/search", response_model=list[PassageOut], dependencies=protected)
def search(body: SearchRequest) -> list[PassageOut]:
    cfg = production_config()
    passages = make_search(cfg).search(body.question, 50 if body.theme else body.k)
    if body.theme:
        passages = [p for p in passages if themes().get(p.doc_ref) == body.theme]
    return [
        PassageOut(
            doc_ref=p.doc_ref, titre=p.titre, page=p.page, section=p.section, extrait=p.text, score=p.score
        )
        for p in passages[: body.k]
    ]


@cache
def themes() -> dict[str, str]:
    """doc_ref -> thème, lu une seule fois dans data/corpus.csv."""
    return {e.doc_ref: e.theme for e in load_corpus(ROOT / "data" / "corpus.csv")}
