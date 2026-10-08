"""Serveur MCP : le RAG utilisable depuis n'importe quel client MCP (Claude Desktop, Claude Code, un IDE).

Il appelle exactement le même code que l'évaluation (ragfr.pipeline) : aucune logique en double.
La configuration utilisée se choisit avec la variable d'environnement RAGFR_CONFIG.

    uv run python -m ragfr.mcp_server.server            # transport stdio (Claude Desktop)
"""

import json
import os
from functools import cache
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from ragfr.config import Config, load_config
from ragfr.ingestion.corpus import load_corpus
from ragfr.ingestion.models import CorpusEntry, ParsedDocument
from ragfr.ingestion.sections import ANNEX, heading_depth
from ragfr.pipeline import answer_question, make_search

ROOT = Path(__file__).resolve().parents[3]
CORPUS_CSV = ROOT / "data" / "corpus.csv"
PARSED_DIR = ROOT / "data" / "parsed"
DEFAULT_CONFIG = ROOT / "configs" / "production.yaml"

# Les descriptions sont courtes et précises : c'est ce que lit le modèle client pour choisir l'outil.
server = MCPServer(
    name="ragfr",
    instructions=(
        "Recherche et réponses sourcées sur 45 guides de cybersécurité de l'ANSSI "
        "(administration, authentification, cloud et conteneurs, journalisation)."
    ),
)


@cache
def config() -> Config:
    return load_config(os.environ.get("RAGFR_CONFIG", DEFAULT_CONFIG))


@cache
def corpus() -> dict[str, CorpusEntry]:
    return {entry.doc_ref: entry for entry in load_corpus(CORPUS_CSV)}


@server.tool()
def search_regulations(question: str, k: int = 5, theme: str | None = None) -> list[dict]:
    """Cherche les passages des guides ANSSI les plus pertinents pour une question, sans générer de réponse.

    theme (optionnel) : administration, authentification, conteneurs ou journalisation.
    """
    k = max(1, min(k, 20))
    passages = make_search(config()).search(question, 50 if theme else k)
    if theme:
        passages = [p for p in passages if corpus()[p.doc_ref].theme == theme]
    return [
        {"doc_ref": p.doc_ref, "titre": p.titre, "page": p.page, "section": p.section, "extrait": p.text}
        for p in passages[:k]
    ]


@server.tool()
def ask_regulations(question: str) -> dict:
    """Répond à une question avec les guides ANSSI : chaque phrase cite sa source (guide, page).

    Répond « je ne sais pas » si les guides ne contiennent pas la réponse.
    """
    answer = answer_question(config(), question)
    return {
        "reponse": answer.text,
        "abstention": answer.abstained,
        "citations": [
            {"phrase": c.phrase, "doc_ref": c.doc_ref, "page": c.page, "verdict": c.verdict}
            for c in answer.citations
        ],
    }


@server.tool()
def get_document(doc_ref: str) -> dict:
    """Donne le titre, le thème, la date de mise à jour, l'URL officielle et le sommaire d'un guide."""
    if doc_ref not in corpus():
        return {"erreur": f"guide inconnu : {doc_ref}", "guides_disponibles": sorted(corpus())}
    entry = corpus()[doc_ref]
    parsed = ParsedDocument.model_validate_json((PARSED_DIR / f"{doc_ref}.json").read_text(encoding="utf-8"))
    # Sommaire : seulement les titres NUMÉROTÉS de niveau 1 et 2 (« 2 … », « 2.1 … »). On écarte le titre
    # du guide, les références internes et « Table des matières », qui ne sont pas des sections.
    sommaire = [
        e.text
        for e in parsed.elements
        if e.kind == "heading" and (heading_depth(e.text) or 0) in (1, 2) and not ANNEX.match(e.text)
    ]
    return {**entry.model_dump(), "pages": parsed.n_pages, "sommaire": sommaire[:60]}


@server.resource("corpus://documents", mime_type="application/json")
def list_documents() -> str:
    """La liste des 45 guides du corpus (référence, titre, thème, date de mise à jour)."""
    return json.dumps([e.model_dump() for e in corpus().values()], ensure_ascii=False)


if __name__ == "__main__":
    server.run("stdio")
