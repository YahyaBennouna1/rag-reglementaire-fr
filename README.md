# RAG agentique sur les guides de cybersécurité de l'ANSSI

Assistant de questions-réponses sur un corpus de **45 guides de l'ANSSI** (1 951 pages). Il cite la source de chaque phrase, répond « je ne sais pas » quand le corpus ne contient pas la réponse, et **mesure** l'apport de chaque technique sur un jeu d'évaluation de 194 questions validées, dont 49 mises de côté pour l'évaluation finale.

![Démonstration : une question, la réponse citée avec sa source, une question hors des guides, une tentative d'injection refusée](docs/demo.gif)

**Résultats sur 49 questions de test jamais utilisées pendant le développement** : recherche BM25 recall@10 0,81 [IC 95 % 0,69 – 0,91] ; 35 réponses exactes sur 44 ; abstention correcte sur 4 questions hors corpus sur 5 ; 0 question bloquée à tort par les garde-fous. Détail plus bas et dans [`results/`](results/).

## Pourquoi ce projet

Un RAG naïf se code en 50 lignes. Ce projet s'intéresse à ce qui fait la différence en production :

- **Des données propres** : parsing structurel des PDF (tableaux, sections, pages) plutôt qu'une extraction de texte brute.
- **Une évaluation d'abord** : 194 questions validées, construites *avant* toute optimisation, et une **ablation** qui chiffre chaque technique.
- **Un système qui sait s'abstenir** : un agent juge la qualité des passages trouvés, relance la recherche ou refuse de répondre.
- **Des citations vérifiées** : chaque phrase de la réponse renvoie à un passage, et un juge vérifie que le passage dit bien ce que la phrase affirme.

## Technologies et techniques

**Implémenté**

| Domaine | Mots-clés |
|---|---|
| RAG et recherche | RAG, **agentic RAG**, **Corrective RAG (CRAG)**, **recherche hybride**, **BM25** (analyseur français, racinisation Snowball), **embeddings denses** (multilingual-e5, bge-m3), **Reciprocal Rank Fusion (RRF)**, **reranking cross-encoder**, chunking à taille fixe avec chevauchement |
| Sécurité | **Garde-fous contre l'injection de prompt** : neutralisation des balises, **Llama Prompt Guard 2** puis un LLM classifieur (défense en profondeur), jeu d'attaques par famille ; **masquage des données personnelles** avec **Presidio** (spaCy français) avant tout appel à un LLM |
| Requêtes et agent | **LangGraph**, **query routing** (routage logique par LLM), **query translation** : **multi-query**, **query decomposition** (fusion par alternance), **HyDE** ; reformulation guidée, abstention (« je ne sais pas ») |
| LLM | **LiteLLM** (Gemini, Groq, OpenAI), sorties JSON structurées validées par Pydantic, cache disque des appels, retry avec backoff exponentiel, gestion des quotas, **citations vérifiées** phrase par phrase |
| Évaluation | **LLM-as-a-judge**, jeu d'évaluation synthétique validé, **recall@k, MRR, nDCG**, fidélité / exactitude / pertinence, **kappa de Cohen**, intervalles de confiance, **ablation**, découpage dev / test figé, coût pour 1 000 requêtes |
| Données | **Docling** (parsing PDF, tableaux), PyMuPDF, web scraping (httpx, BeautifulSoup), nettoyage par regex, normalisation Unicode, hiérarchie des sections |
| Stockage | **Qdrant** (vecteurs denses et creux, mode local ou serveur), SQLite (cache d'embeddings et de reranking), empreintes SHA-256 |
| Service | **Streamlit** (interface avec sources citées), **FastAPI** (validation Pydantic, sondes health / ready, clé d'API, limite de débit), serveur **MCP** (Model Context Protocol : outils et ressource pour Claude Desktop ou un IDE) |
| Ingénierie | **Python 3.12**, **uv**, **Pydantic**, **pytest** (tests unitaires, d'intégration, mocks), **ruff**, configuration YAML, Git (Conventional Commits, pull requests), **GitHub Actions** (CI), **Docker** (image multi-étapes, non root), Docker Compose, **Kubernetes** (kind : Deployment, StatefulSet, Service, Secret, sondes readiness / liveness) |

**Prévu** : GraphRAG (Neo4j), contextual retrieval, **Terraform**, porte de qualité en CI (seuil de régression), **Langfuse**, démo Hugging Face Spaces.

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
| Évaluation finale sur le jeu de test figé, intervalles de confiance | ✅ |
| RAG de référence : découpage fixe, embeddings, Qdrant | ✅ |
| Recherche hybride BM25 français + dense, RRF (pondéré), reranker | ✅ mesuré |
| Routeur, multi-query, décomposition, HyDE | ✅ routeur mesuré (multi-query utile sur les questions vagues ; décomposition corrigée par une fusion par alternance) |
| Agent correctif LangGraph, citations vérifiées par un juge | ✅ mesuré sur le jeu de test ; juge des citations validé (kappa 0,86) |
| Chunking sémantique et contextual retrieval | ⬜ |
| Serveur MCP (recherche, réponse citée, description d'un guide) | ✅ |
| Garde-fous : détection d'injection de prompt en deux couches, mesurée | ✅ |
| Masquage des données personnelles (Presidio), mesuré | ✅ |
| GraphRAG | ⬜ |
| API FastAPI (ask, search, health, ready) | ✅ |
| Interface web Streamlit (réponse, sources citées, abstention) | ✅ |
| CI GitHub Actions (ruff, tests) | ✅ |
| Image Docker de service, construite et testée par la CI | ✅ |
| Kubernetes en local (kind) : 2 copies de l'API, sondes, auto-réparation testée | ✅ |
| Terraform, porte de qualité sur le recall en CI | ⬜ |

## Évaluation

**Le jeu de questions.** Les questions sont générées à partir de passages tirés au hasard, en 5 types : factuelles, réponse dans un tableau, multi-documents, vagues et sans réponse dans le corpus. Chaque question garde la référence de sa source (guide, page, extrait exact), indépendante du découpage. Elles sont ensuite :
- **filtrées automatiquement** : extrait vérifié mot pour mot dans le guide, question qui ne recopie pas le texte, pas de doublon ;
- **validées selon une grille de 4 critères fondée sur le document source** : l'extrait prouve la réponse, la réponse est complète, la question se comprend seule, une seule bonne réponse possible. Pour les questions sans réponse, on vérifie que les passages les plus proches ne répondent pas.
- **Validation semi-automatique** : j'ai d'abord audité manuellement un échantillon tiré au hasard. Cet audit a montré qu'une relecture rapide laissait passer beaucoup d'erreurs (questions qui parlent du document au lieu du sujet, réponses incomplètes). J'ai donc mis en place un LLM juge appliquant la même grille, et mesuré son accord avec mes jugements (kappa de Cohen) avant de l'appliquer à toutes les questions.

Le jeu final (194 questions) est découpé, par type, en 145 questions de développement et 49 questions de test. Le jeu de test a été figé avant toute optimisation et n'a servi qu'une fois, pour les résultats ci-dessous. Empreinte SHA-256 de `data/eval/questions_test.jsonl` : `16584fbb91b915c11a53c249b9dc0bfadbdb2106be935f4fbc739e3612530117`.

**Les mesures.** Recherche : recall@5, recall@10, MRR et nDCG@10, comptés par référence (et non par chunk). Réponses : fidélité, exactitude et pertinence notées par un LLM juge d'une autre famille que le générateur ; abstention correcte ; coût pour 1 000 requêtes au tarif public.

### Résultats sur le jeu de test figé (49 questions jamais utilisées)

**Recherche.** Intervalles de confiance à 95 % par bootstrap (10 000 tirages, `scripts/intervalles.py`).

| Recherche | recall@10 | MRR | Latence médiane |
|---|---|---|---|
| **BM25, analyseur français (production)** | **0,807** [0,693 – 0,909] | **0,739** [0,616 – 0,851] | 141 ms |
| Dense (multilingual-e5-base) | 0,693 [0,568 – 0,818] | 0,542 [0,413 – 0,670] | — |
| Hybride (RRF) | 0,795 [0,693 – 0,886] | 0,658 [0,536 – 0,772] | 138 ms |
| Hybride, RRF pondérée | 0,773 [0,659 – 0,875] | 0,701 [0,578 – 0,812] | 156 ms |
| Hybride + routeur (multi-query, décomposition) | 0,807 [0,705 – 0,898] | 0,662 [0,542 – 0,777] | 4,5 s |

Même classement que sur le jeu de développement. Différences appariées : BM25 est significativement meilleure que la recherche dense (MRR +0,197, IC [0,070 ; 0,327]) ; aucune différence n'est démontrée entre BM25 et l'hybride pondéré ou le routeur. BM25 est retenue car aussi bonne, plus simple et plus rapide.

**Réponses** (juge qwen3.8-27b, d'une autre famille que le générateur Gemini).

| Configuration | Réponses exactes (44 questions avec réponse) | Abstentions à tort | Abstention correcte (5 sans réponse) | Coût / 1 000 questions |
|---|---|---|---|---|
| **RAG simple (production)** | **35 (79,5 %)** | 4 | 4/5 | **1,94 $** |
| + agent correctif | 30 (68,2 %) | 10 | 4/5 | 3,41 $ |
| + agent + vérification des citations | 30 (68,2 %) | 10 | 4/5 | 4,24 $ |

Fidélité aux passages cités : 100 % ; phrases soutenues par leur citation : 100 %. L'agent s'abstient à tort sur des questions multi-documents et vagues (sa note « passages insuffisants » est trop stricte) : différence -0,114 [IC 95 % -0,227 ; 0,000], à la limite de la significativité. Le résultat contredit la première mesure sur 20 questions de développement (agent : 86 % → 93 % d'exactitude, calculée sur les seules questions répondues) ; la production reste le RAG simple. Le jeu de test n'a pas servi à corriger l'agent.

**Garde-fous.** 0 question de test sur 49 bloquée à tort. Le masquage des données personnelles modifiait 2 questions sur 49 (« Sysmon », « password spraying » pris pour des noms de personne) ; correction conçue et mesurée sans le jeu de test (vocabulaire des guides, voir plus bas).

### Mesures sur le jeu de développement et validations

**Parsing des tableaux (20 tableaux tirés au hasard).** Docling 15/20 contre PyMuPDF 13/20, et 14/16 contre 10/16 sur les vrais tableaux de données ([détail](results/parsing_tableaux.md)).

**Premières mesures des réponses (20 questions de développement, 4 par type).** Abstention correcte sur 4/4 questions hors corpus ; les 2 fausses abstentions sur 16 viennent de la recherche (source absente des 10 premiers passages). L'agent semblait améliorer l'exactitude (86 % → 93 %) : non confirmé sur le jeu de test (voir ci-dessus).

**Validation du juge des citations (65 cas).** 45 phrases réelles du système et 20 phrases faussées exprès (chiffre changé, négation, inversion, ajout inventé). Accord juge / annotations sur la décision « retirer la phrase » : kappa de Cohen 0,86 ; 18/18 phrases fausses détectées ; 2 fausses alertes sur 45, toutes deux sur une phrase tirée d'un tableau à cellules fusionnées (faiblesse identifiée du juge sur les tableaux).

**Garde-fous contre l'injection de prompt (40 attaques en 6 familles, 15 questions pièges, 145 questions réelles).** Le classifieur spécialisé Llama Prompt Guard 2 seul détecte 35 % des attaques ; avec un LLM classifieur en deuxième couche, 95 %, pour 0 fausse alerte sur les questions pièges et 2,1 % sur les questions réelles. Les attaques non détectées restent sans effet de bout en bout : le système ne répond qu'à partir des guides et s'abstient. Sur les mêmes attaques, un RAG naïf (passages collés sans règles) écrit le texte demandé par l'attaquant et recopie une fausse recommandation attribuée à l'ANSSI ; ce RAG, même sans garde-fous, s'abstient (`scripts/demo_injection.py`).

**Données personnelles.** Masquées par Presidio avant tout appel à un LLM : 24 données sur 24 trouvées (noms, e-mails, téléphones, IBAN, carte, IP), 0 question réelle modifiée sur 145. Un nom dont tous les mots figurent dans les guides et qui ne ressemble pas à un nom complet est traité comme un terme du domaine : 1 question technique sur 18 encore modifiée (« Fail2ban », absent des guides).

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

Avec Kubernetes en local ([kind](https://kind.sigs.k8s.io/)) : Qdrant (StatefulSet), l'API en 2 copies avec sondes `/ready` et `/health`, l'interface, et les clés dans un Secret créé depuis `.env` :

```bash
kind create cluster --name ragfr --config k8s/kind.yaml
docker build -t ragfr:0.1.0 . && kind load docker-image ragfr:0.1.0 --name ragfr
kubectl apply -f k8s/namespace.yaml
kubectl -n ragfr create secret generic ragfr-cles --from-env-file=.env
kubectl apply -f k8s/qdrant.yaml -f k8s/api.yaml -f k8s/ui.yaml
kubectl -n ragfr port-forward svc/qdrant 16333:6333   # puis : uv run python scripts/migrate_qdrant.py --url http://127.0.0.1:16333
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
