"""Assemble et envoie la démo en ligne vers un Space Hugging Face.

    uv run python scripts/deploy_space.py --space <utilisateur>/rag-anssi            # assembler + envoyer
    uv run python scripts/deploy_space.py --space <utilisateur>/rag-anssi --dry-run  # assembler seulement

Prérequis (à faire soi-même) : un compte Hugging Face, un jeton d'accès en écriture dans .env
(HF_TOKEN=…), puis, dans les réglages du Space, les secrets GEMINI_API_KEY et GROQ_API_KEY.
Le script n'envoie AUCUNE clé : ni .env, ni secret.

Le Space reçoit le strict nécessaire : le code, les configurations, la liste du corpus, le vocabulaire
des guides et l'index Qdrant (25 Mo). Pas les PDF ni les caches.
"""

import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent
BUILD = Path("D:/PROJET1/telechargements/space-build")  # hors du dépôt
GITHUB_URL = "https://github.com/YahyaBennouna1/rag-reglementaire-fr"

FILES = ["pyproject.toml", "uv.lock", "data/corpus.csv", "data/vocabulaire_corpus.txt"]
FOLDERS = ["src", "configs", "data/qdrant"]


def assemble() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    for name in FILES:
        (BUILD / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, BUILD / name)
    for name in FOLDERS:
        # Le fichier .lock de Qdrant et les caches Python ne servent à rien dans le Space.
        shutil.copytree(ROOT / name, BUILD / name, ignore=shutil.ignore_patterns(".lock", "__pycache__"))
    shutil.copy2(ROOT / "space" / "Dockerfile", BUILD / "Dockerfile")
    readme = (ROOT / "space" / "README.md").read_text(encoding="utf-8").replace("{GITHUB_URL}", GITHUB_URL)
    (BUILD / "README.md").write_text(readme, encoding="utf-8")
    size = sum(f.stat().st_size for f in BUILD.rglob("*") if f.is_file())
    print(f"Space assemblé dans {BUILD} ({size / 1e6:.1f} Mo)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--space", required=True, help="ex. mon-compte/rag-anssi")
    parser.add_argument("--dry-run", action="store_true", help="assembler sans envoyer")
    args = parser.parse_args()

    assemble()
    if args.dry_run:
        return
    load_dotenv(ROOT / ".env")
    api = HfApi(token=os.environ["HF_TOKEN"])
    api.create_repo(args.space, repo_type="space", space_sdk="docker", exist_ok=True)
    # upload_folder gère tout seul les gros fichiers (l'index) avec Git LFS.
    api.upload_folder(
        folder_path=BUILD, repo_id=args.space, repo_type="space", commit_message="Mise à jour de la démo"
    )
    print(f"Envoyé : https://huggingface.co/spaces/{args.space}")


if __name__ == "__main__":
    main()
