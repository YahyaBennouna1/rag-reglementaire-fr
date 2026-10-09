# Image de la démo en ligne (Hugging Face Spaces) : l'interface Streamlit, avec l'index inclus.
# Assemblée et envoyée par scripts/deploy_space.py ; même construction que le Dockerfile du projet
# (leçon 20), avec ce que demande Hugging Face : port 7860, utilisateur d'identifiant 1000.

FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-default-groups --no-install-project
COPY src ./src
RUN uv sync --locked --no-default-groups

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=build --chown=app:app /app/.venv ./.venv
COPY --from=build --chown=app:app /app/src ./src
COPY --chown=app:app configs ./configs
COPY --chown=app:app data ./data
RUN mkdir -p data/cache .cache && chown -R app:app data .cache

USER app
# Pas de clé ici : GEMINI_API_KEY et GROQ_API_KEY sont des « secrets » réglés dans le Space.
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 \
    RAGFR_MAX_QUESTIONS=10 RAGFR_MAX_QUESTIONS_PER_DAY=200
EXPOSE 7860
CMD ["streamlit", "run", "src/ragfr/ui/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true", "--browser.gatherUsageStats=false"]
