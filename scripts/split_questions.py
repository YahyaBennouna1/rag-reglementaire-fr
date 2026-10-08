"""Construit le jeu final de 200 questions et le découpe en développement (150) et test (50).

- Quotas par type (guide du projet) : 80 factuelles, 40 tableau, 40 multi-documents,
  20 vagues, 20 sans réponse.
- Découpage stratifié : chaque type est réparti 75 % / 25 % entre dev et test.
- Le fichier de test est ensuite GELÉ : son empreinte SHA-256 est affichée pour le README.
  On règle tous les paramètres sur dev ; test ne sert qu'aux résultats finaux.
"""

import hashlib
import random
from pathlib import Path

from ragfr.eval.dataset import load_questions, save_questions

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "candidates.jsonl"
QUESTIONS = ROOT / "data" / "eval" / "questions.jsonl"
TEST_FILE = ROOT / "data" / "eval" / "questions_test.jsonl"

QUOTAS = {"factuelle": 80, "tableau": 40, "multi_documents": 40, "vague": 20, "sans_reponse": 20}
TEST_SHARE = 0.25
SEED = 42


def main() -> None:
    if TEST_FILE.exists():
        raise SystemExit(f"{TEST_FILE.name} existe déjà : le jeu de test est gelé, on ne le refait pas.")

    rng = random.Random(SEED)
    accepted = [q for q in load_questions(CANDIDATES) if q.statut in ("valide", "corrige")]
    final = []
    for kind, quota in QUOTAS.items():
        pool = [q for q in accepted if q.type == kind]
        if len(pool) < quota:
            print(f"⚠ {kind} : {len(pool)} validées pour un quota de {quota}")
        chosen = rng.sample(pool, min(quota, len(pool)))
        n_test = round(len(chosen) * TEST_SHARE)
        for i, q in enumerate(chosen):
            q.split = "test" if i < n_test else "dev"
        final.extend(chosen)

    final.sort(key=lambda q: q.id)
    save_questions(final, QUESTIONS)
    save_questions([q for q in final if q.split == "test"], TEST_FILE)
    digest = hashlib.sha256(TEST_FILE.read_bytes()).hexdigest()
    n_dev = sum(q.split == "dev" for q in final)
    print(f"{len(final)} questions : {n_dev} dev, {len(final) - n_dev} test")
    print(f"SHA-256 du jeu de test gelé : {digest}")


if __name__ == "__main__":
    main()
