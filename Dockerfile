# Image de service : l'API (par défaut) ou l'interface Streamlit.
# Seul le cœur est installé (pas de Docling ni de PyTorch) : la recherche de production est BM25.
#
#   docker build -t ragfr .
#   docker run --rm -p 8000:8000 --env-file .env -v ./data/qdrant:/app/data/qdrant ragfr
#
# L'index Qdrant n'est pas dans l'image : il est monté depuis le disque (données séparées du code).

# --- Étape 1 : construire l'environnement Python ------------------------------------------------
FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/uv
WORKDIR /app
# Compiler les .py à l'installation (démarrage plus rapide) ; copier les fichiers au lieu de liens.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# D'abord les dépendances seules : cette couche ne change que si uv.lock change,
# donc Docker la réutilise (cache) quand on ne modifie que le code.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-default-groups --no-install-project

# Puis le code du projet.
COPY src ./src
RUN uv sync --locked --no-default-groups

# --- Étape 2 : l'image finale, sans uv ni fichiers de construction -------------------------------
FROM python:3.12-slim

# Un utilisateur sans droits d'administrateur : si l'application est attaquée, l'attaquant
# n'a pas les droits root dans le conteneur.
RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY --from=build --chown=app:app /app/.venv ./.venv
COPY --from=build --chown=app:app /app/src ./src
COPY --chown=app:app configs ./configs
COPY --chown=app:app data/corpus.csv ./data/corpus.csv
COPY --chown=app:app data/vocabulaire_corpus.txt ./data/vocabulaire_corpus.txt
RUN mkdir -p data/qdrant data/cache && chown -R app:app data

USER app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
EXPOSE 8000

# Docker vérifie toutes les 30 s que l'API répond (la même sonde que Kubernetes, leçon 17).
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "ragfr.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
