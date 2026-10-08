"""Le serveur MCP expose ses outils et sa ressource (le guide demande un test de la liste des outils)."""

import asyncio

from ragfr.mcp_server.server import server


def test_liste_des_outils():
    tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == {"search_regulations", "ask_regulations", "get_document"}
    for tool in tools:
        assert tool.description  # le modèle client choisit l'outil grâce à sa description


def test_ressource_corpus():
    resources = asyncio.run(server.list_resources())
    assert "corpus://documents" in {str(r.uri) for r in resources}
