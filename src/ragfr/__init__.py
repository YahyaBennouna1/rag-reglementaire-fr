"""ragfr : RAG agentique sur les guides de cybersécurité de l'ANSSI."""

import os
from pathlib import Path

# Les modèles d'IA (Docling, embeddings, reranker) sont rangés DANS le projet, et pas sur le
# disque système : le disque C: s'est rempli pendant le téléchargement d'un modèle (voir le journal
# de bord du cours). setdefault : une valeur déjà définie par l'utilisateur reste prioritaire.
# Ce code s'exécute avant tout import de Hugging Face, puisque tout passe par le package ragfr.
os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[2] / ".cache" / "huggingface"))
