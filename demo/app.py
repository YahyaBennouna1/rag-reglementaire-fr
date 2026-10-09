"""Point d'entrée de la démo sur Streamlit Community Cloud (leçon 25).

Streamlit Cloud lance ce fichier depuis le dépôt GitHub. Il règle la démo (index embarqué dans ce
dossier, limites de questions), puis exécute l'interface du projet.

On EXÉCUTE l'interface à chaque passage (runpy) au lieu de l'importer : Streamlit relance ce script à
chaque clic, alors qu'un module importé une fois n'est plus jamais réexécuté (la page resterait vide).
"""

import os
import runpy
from pathlib import Path

DEMO = Path(__file__).resolve().parent
# setdefault : une valeur réglée dans les secrets de Streamlit Cloud reste prioritaire.
os.environ.setdefault("RAGFR_QDRANT_PATH", str(DEMO / "qdrant"))
os.environ.setdefault("RAGFR_MAX_QUESTIONS", "10")
os.environ.setdefault("RAGFR_MAX_QUESTIONS_PER_DAY", "200")

import ragfr.ui  # noqa: E402  (après les variables : le package lit RAGFR_QDRANT_PATH à l'import)

runpy.run_path(str(Path(ragfr.ui.__file__).parent / "streamlit_app.py"), run_name="__main__")
