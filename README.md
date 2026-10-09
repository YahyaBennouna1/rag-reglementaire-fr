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
| Requêtes et agent | **LangGraph**, **query routing** (routage logique par LLM), **query translation** : **multi-query**, **query decomposition** (fusion par alternance), **HyDE** ; reformulation guidée, abstention (« je ne sais pas ») |
| LLM | **LiteLLM** (Gemini, Groq, OpenAI), sorties JSON structurées validées par Pydantic, cache disque des appels, retry avec backoff exponentiel, gestion des quotas, **citations vérifiées** phrase par phrase |
| Évaluation | **LLM-as-a-judge**, jeu d'évaluation synthétique validé, **recall@k, MRR, nDCG**, fidélité / exactitude / pertinence, **kappa de Cohen**, intervalles de confiance, **ablation**, découpage dev / test figé, coût pour 1 000 requêtes |
| Données | **Docling** (parsing PDF, tableaux), PyMuPDF, web scraping (httpx, BeautifulSoup), nettoyage par regex, normalisation Unicode, hiérarchie des sections |
| Stockage | **Qdrant** (vecteurs denses et creux, mode local ou serveur), SQLite (cache d'embeddings et de reranking), empreintes SHA-256 |
| Service | **Streamlit** (interface avec sources citées), **FastAPI** (validation Pydantic, sondes health / ready, clé d'API, limite de débit), serveur **MCP** (Model Context Protocol : outils et ressource pour Claude Desktop ou un IDE) |
| Ingénierie | **Python 3.12**, **uv**, **Pydantic**, **pytest** (tests unitaires, d'intégration, mocks), **ruff**, configuration YAML, Git (Conventional Commits, pull requests), **GitHub Actions** (CI), **Docker** (image multi-étapes, non root), Docker Compose |

**Prévu** : GraphRAG (Neo4j), contextual retrieval, garde-fous (injection de prompt, **Presidio**), **Kubernetes** (kind), **Terraform**, porte de qualité en CI (seuil de régression), **Langfuse**, démo Hugging Face Spaces.

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
| Routeur, multi-query, décomposition, HyDE | ✅ routeur mesuré (multi-query utile sur les questions vagues ; décomposition corrigée par une fusion par alternance) |
| Agent correctif LangGraph, citations vérifiées par un juge | ✅ mesuré sur un premier échantillon (validation du juge à faire) |
| Chunking sémantique et contextual retrieval | ⬜ |
| Serveur MCP (recherche, réponse citée, description d'un guide) | ✅ |
| GraphRAG, garde-fous | ⬜ |
| API FastAPI (ask, search, health, ready) | ✅ |
| Interface web Streamlit (réponse, sources citées, abstention) | ✅ |
| CI GitHub Actions (ruff, tests) | ✅ |
| Image Docker de service, construite et testée par la CI | ✅ |
| Kubernetes (kind) + Terraform, porte de qualité sur le recall en CI | ⬜ |

## Évaluation

**Le jeu de questions.** Les questions sont générées à partir de passages tirés au hasard, en 5 types : factuelles, réponse dans un tableau, multi-documents, vagues et sans réponse dans le corpus. Chaque question garde la référence de sa source (guide, page, extrait exact), indépendante du découpage. Elles sont ensuite :
- **filtrées automatiquement** : extrait vérifié mot pour mot dans le guide, question qui ne recopie pas le texte, pas de doublon ;
- **validées selon une grille de 4 critères fondée sur le document source** : l'extrait prouve la réponse, la réponse est complète, la question se comprend seule, une seule bonne réponse possible. Pour les questions sans réponse, on vérifie que les passages les plus proches ne répondent pas.
- **Validation semi-automatique** : j'ai d'abord audité manuellement un échantillon tiré au hasard. Cet audit a montré qu'une relecture rapide laissait passer beaucoup d'erreurs (questions qui parlent du document au lieu du sujet, réponses incomplètes). J'ai donc mis en place un LLM juge appliquant la même grille, et mesuré son accord avec mes jugements (kappa de Cohen) avant de l'appliquer à toutes les questions.

Le jeu final (200 questions) est découpé en 150 questions de développement et 50 questions de test ; le jeu de test est figé et son empreinte SHA-256 est publiée.

**Les mesures.** Recherche : recall@5, recall@10, MRR et nDCG@10, comptés par référence (et non par chunk). Réponses : fidélité, exactitude et pertinence notées par un LLM juge d'une autre famille que le générateur ; abstention correcte ; coût pour 1 000 requêtes au tarif public.

**Premier résultat (parsing des tableaux, 20 tableaux tirés au hasard).** Docling 15/20 contre PyMuPDF 13/20, et 14/16 contre 10/16 sur les vrais tableaux de données ([détail](results/parsing_tableaux.md)).

**Premières mesures des réponses (20 questions de développement, 4 par type, juge qwen3.8-27b).** Abstention correcte sur 4/4 questions hors corpus ; les 2 fausses abstentions sur 16 viennent de la recherche (source absente des 10 premiers passages). L'agent correctif fait passer l'exactitude de 86 % à 93 % pour un coût multiplié par 1,8 (1,96 $ → 3,57 $ pour 1 000 questions au tarif public). Échantillon réduit et juge pas encore validé contre des annotations humaines : ces chiffres sont indicatifs.

**Validation du juge des citations (65 cas).** 45 phrases réelles du système et 20 phrases faussées exprès (chiffre changé, négation, inversion, ajout inventé). Annotations RÉALISÉES PAR LLM (QUI DEVAIENT ÊTRE RÉALISÉES PAR MOI). Accord juge / annotations sur la décision « retirer la phrase » : kappa de Cohen 0,86 ; 18/18 phrases fausses détectées ; 2 fausses alertes sur 45, toutes deux sur une phrase tirée d'un tableau à cellules fusionnées (faiblesse identifiée du juge sur les tableaux).

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

Une fois l'index construit (`scripts/build_index.py`) et les clés d'API dans `.env` (voir `.env.example`) :

```bash
uv run streamlit run src/ragfr/ui/streamlit_app.py   # interface web : http://localhost:8501
uv run uvicorn ragfr.api.app:app --port 8000          # API : documentation sur http://localhost:8000/docs
uv run python -m ragfr.mcp_server.server              # serveur MCP (Claude Desktop, IDE)
```

Sans Docker, Qdrant est utilisé en mode local : un seul de ces programmes à la fois peut ouvrir l'index.

Avec Docker (image de service de 907 Mo sans Docling ni PyTorch, construite et testée par la CI ; Qdrant en mode serveur) :

```bash
docker compose up -d qdrant
uv run python scripts/migrate_qdrant.py      # première fois : copie l'index local dans le serveur
docker compose up -d --build                 # Qdrant + API (:8000/docs) + interface (:8501)
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

## Répartition du travail

| Tâche | Réalisation |
|---|---|
| Écriture du code et des tests | RÉALISÉ PAR LLM (QUI DEVAIT ÊTRE RÉALISÉ PAR MOI) |
| Audit manuel des questions (18 questions tirées au hasard) | Réalisé par moi |
| Validation des autres questions du jeu d'évaluation (grille de 4 critères) | RÉALISÉ PAR LLM (QUI DEVAIT ÊTRE RÉALISÉ PAR MOI), calibré sur mon audit (kappa de Cohen) |
| Annotation des cas de validation du juge des citations | RÉALISÉ PAR LLM (QUI DEVAIT ÊTRE RÉALISÉ PAR MOI) |
| Lancement des mesures et analyse des résultats (ablations) | RÉALISÉ PAR LLM (QUI DEVAIT ÊTRE RÉALISÉ PAR MOI) |

## Auteur

Yahya Bennouna
