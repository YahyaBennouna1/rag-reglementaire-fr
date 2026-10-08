# RAG agentique sur les guides de cybersécurité de l'ANSSI

Assistant de questions-réponses sur un corpus de **45 guides de l'ANSSI** (1 951 pages). Il cite la source de chaque phrase, répond « je ne sais pas » quand le corpus ne contient pas la réponse, et **mesure** l'apport de chaque technique sur un jeu d'évaluation vérifié à la main.

> 🚧 **Projet en cours.** Cette page décrit l'état actuel ; les résultats chiffrés seront publiés au fil des étapes dans [`results/`](results/).

## Pourquoi ce projet

Un RAG naïf se code en 50 lignes. Ce projet s'intéresse à ce qui fait la différence en production :

- **Des données propres** : parsing structurel des PDF (tableaux, sections, pages) plutôt qu'une extraction de texte brute.
- **Une évaluation d'abord** : 200 questions vérifiées, construites *avant* toute optimisation, et une **ablation** qui chiffre chaque technique.
- **Un système qui sait s'abstenir** : un agent juge la qualité des passages trouvés, relance la recherche ou refuse de répondre.
- **Des citations vérifiées** : chaque phrase de la réponse renvoie à un passage, et un juge vérifie que le passage dit bien ce que la phrase affirme.

## Technologies et techniques

**Implémenté**

| Domaine | Mots-clés |
|---|---|
| RAG et recherche | RAG, **agentic RAG**, **Corrective RAG (CRAG)**, **recherche hybride**, **BM25** (analyseur français, racinisation Snowball), **embeddings denses** (multilingual-e5, bge-m3), **Reciprocal Rank Fusion (RRF)**, **reranking cross-encoder**, chunking à taille fixe avec chevauchement |
| Requêtes et agent | **LangGraph**, query routing, **multi-query**, **query decomposition**, **HyDE**, reformulation guidée, abstention (« je ne sais pas ») |
| LLM | **LiteLLM** (Gemini, Groq, OpenAI), sorties JSON structurées validées par Pydantic, cache disque des appels, retry avec backoff exponentiel, gestion des quotas, **citations vérifiées** phrase par phrase |
| Évaluation | **LLM-as-a-judge**, jeu d'évaluation synthétique validé, **recall@k, MRR, nDCG**, fidélité / exactitude / pertinence, **kappa de Cohen**, intervalles de confiance, **ablation**, découpage dev / test figé, coût pour 1 000 requêtes |
| Données | **Docling** (parsing PDF, tableaux), PyMuPDF, web scraping (httpx, BeautifulSoup), nettoyage par regex, normalisation Unicode, hiérarchie des sections |
| Stockage | **Qdrant** (vecteurs denses et creux), SQLite (cache d'embeddings et de reranking), empreintes SHA-256 |
| Service | **FastAPI** (validation Pydantic, sondes health / ready, clé d'API, limite de débit), serveur **MCP** (Model Context Protocol : outils et ressource pour Claude Desktop ou un IDE) |
| Ingénierie | **Python 3.12**, **uv**, **Pydantic**, **pytest** (tests unitaires, d'intégration, mocks), **ruff**, configuration YAML, Git (Conventional Commits, pull requests) |

**Prévu** : GraphRAG (Neo4j), contextual retrieval, garde-fous (injection de prompt, **Presidio**), **Docker**, **Kubernetes** (kind), **Terraform**, **GitHub Actions** (CI avec seuil de régression), **Langfuse**, démo Hugging Face Spaces.

## Architecture

```
INDEXATION (hors ligne)                                RÉPONSE (à chaque question)
corpus.csv → PDF → Docling → éléments nettoyés         question → garde-fous → routeur
          → chunks (+ contexte) → embeddings + BM25             → recherche hybride (BM25 + dense, RRF)
          → Qdrant  (+ graphe Neo4j)                            → reranker → agent correctif (LangGraph)
                                                                → génération citée → vérification
```

## Avancement

| Étape | État |
|---|---|
| Collecte du corpus (scraping du catalogue ANSSI, 45 guides sur 4 thèmes) | ✅ |
| Ingestion : parsing Docling, nettoyage, hiérarchie des sections, cache | ✅ |
| Mesure du parsing des tableaux (Docling contre PyMuPDF) | ✅ |
| Jeu d'évaluation : 194 questions validées (145 dev, 49 test figé) | ✅ |
| RAG de référence : découpage fixe, embeddings, Qdrant | ✅ |
| Recherche hybride BM25 français + dense, RRF (pondéré), reranker | ✅ mesuré |
| Routeur, multi-query, décomposition, HyDE | ✅ (à mesurer) |
| Agent correctif LangGraph, citations vérifiées par un juge | ✅ (à mesurer) |
| Chunking sémantique et contextual retrieval | ⬜ |
| Serveur MCP (recherche, réponse citée, description d'un guide) | ✅ |
| GraphRAG, garde-fous | ⬜ |
| API FastAPI (ask, search, health, ready) | ✅ |
| Docker, Kubernetes (kind) + Terraform, CI qui bloque les régressions | ⬜ |

## Évaluation

**Le jeu de questions.** Les questions sont générées à partir de passages tirés au hasard, en 5 types : factuelles, réponse dans un tableau, multi-documents, vagues et sans réponse dans le corpus. Chaque question garde la référence de sa source (guide, page, extrait exact), indépendante du découpage. Elles sont ensuite :
- **filtrées automatiquement** : extrait vérifié mot pour mot dans le guide, question qui ne recopie pas le texte, pas de doublon ;
- **validées selon une grille de 4 critères fondée sur le document source** : l'extrait prouve la réponse, la réponse est complète, la question se comprend seule, une seule bonne réponse possible. Pour les questions sans réponse, on vérifie que les passages les plus proches ne répondent pas.
- **Validation semi-automatique** : j'ai d'abord audité manuellement un échantillon tiré au hasard. Cet audit a montré qu'une relecture rapide laissait passer beaucoup d'erreurs (questions qui parlent du document au lieu du sujet, réponses incomplètes). J'ai donc mis en place un LLM juge appliquant la même grille, et mesuré son accord avec mes jugements (kappa de Cohen) avant de l'appliquer à toutes les questions.

Le jeu final (200 questions) est découpé en 150 questions de développement et 50 questions de test ; le jeu de test est figé et son empreinte SHA-256 est publiée.

**Les mesures.** Recherche : recall@5, recall@10, MRR et nDCG@10, comptés par référence (et non par chunk). Réponses : fidélité, exactitude et pertinence notées par un LLM juge d'une autre famille que le générateur ; abstention correcte ; coût pour 1 000 requêtes au tarif public.

**Premier résultat (parsing des tableaux, 20 tableaux tirés au hasard).** Docling 15/20 contre PyMuPDF 13/20, et 14/16 contre 10/16 sur les vrais tableaux de données ([détail](results/parsing_tableaux.md)).

## Choix techniques notables

- **Docling plutôt qu'une extraction de texte simple** : les guides sont riches en tableaux, qu'une extraction ligne à ligne détruit. L'OCR est désactivé (PDF natifs).
- **Hiérarchie reconstruite à partir de la numérotation** : Docling place tous les titres au même niveau ; la numérotation (`2`, `2.1`, `2.1.3`) et une pile reconstruisent le chemin de section de chaque passage.
- **Pages physiques** pour les citations, et non les numéros imprimés (décalés par les pages de garde).
- **Étiquettes de recommandation (R1, R2…) écartées au parsing** : Docling les place hors de leur ordre de lecture ; une citation fausse est pire qu'une citation absente. Elles sont reconstruites à partir de la liste des recommandations de chaque guide.
- **Cache de l'étape coûteuse** : la sortie brute de Docling est indexée par l'empreinte SHA-256 du PDF ; le nettoyage est rejoué en moins d'une seconde au lieu de plusieurs minutes de parsing par guide.

## Lancer le projet

Prérequis : [uv](https://docs.astral.sh/uv/) (installe Python 3.12 et les dépendances).

```bash
uv sync
uv run python scripts/download_corpus.py   # télécharge les 45 PDF dans data/raw/
uv run python scripts/ingest.py            # parsing Docling + nettoyage -> data/parsed/
uv run pytest                              # tests rapides
uv run pytest -m slow                      # test de non-régression du parsing
```

Le corpus est reconstruit à partir de [`data/corpus.csv`](data/corpus.csv) ; les PDF ne sont pas versionnés. Pour régénérer la liste depuis le catalogue : `scripts/scrape_catalogue.py` puis `scripts/build_corpus.py`.

## Structure

```
configs/          configurations YAML (une par ligne du tableau d'ablation)
data/             corpus.csv, candidats.csv ; raw/ et parsed/ sont générés
scripts/          points d'entrée : collecte, téléchargement, ingestion
src/ragfr/        le package : ingestion/, puis chunking/, retrieval/, agent/...
tests/            tests pytest
```

## Source des données

Guides publiés par l'**Agence nationale de la sécurité des systèmes d'information (ANSSI)** sur [messervices.cyber.gouv.fr](https://messervices.cyber.gouv.fr/catalogue), réutilisés sous [Licence Ouverte 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/). La date de mise à jour de chaque guide figure dans [`data/corpus.csv`](data/corpus.csv). Ce projet n'est ni affilié à l'ANSSI ni approuvé par elle.

## Auteur

Yahya Bennouna
