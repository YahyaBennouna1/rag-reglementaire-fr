"""Porte de qualité : refuser un changement qui fait baisser la recherche de production.

    RAGFR_QDRANT_PATH=data/index_reference uv run python scripts/quality_gate.py

Relance la recherche de production (BM25, sans LLM) sur les 145 questions de développement, avec
l'index de référence versionné, et échoue (code de sortie 1) si une mesure passe sous son seuil.
La CI l'exécute à chaque pull request : une modification qui casse la recherche en silence (l'analyseur
BM25, le découpage, la fusion…) est bloquée avant d'arriver dans main.

Seuils : les valeurs mesurées (recall@10 0,842, MRR 0,711), moins une marge de 0,02 pour ne pas
bloquer pour un écart d'une ou deux questions.
"""

import sys
from pathlib import Path

from run_eval import evaluate_retrieval

from ragfr.eval.dataset import load_questions
from ragfr.pipeline import production_config

ROOT = Path(__file__).resolve().parent.parent
THRESHOLDS = {"recall@10": 0.82, "mrr": 0.69}


def main() -> None:
    questions = [q for q in load_questions(ROOT / "data" / "eval" / "questions.jsonl") if q.split == "dev"]
    summary = evaluate_retrieval(production_config(), questions)["resume"]
    failures = []
    for metric, minimum in THRESHOLDS.items():
        status = "OK" if summary[metric] >= minimum else "ÉCHEC"
        print(f"{metric:<10} {summary[metric]:.3f}  (seuil {minimum:.2f})  {status}")
        if summary[metric] < minimum:
            failures.append(metric)
    if failures:
        print(f"Porte de qualité fermée : {', '.join(failures)} sous le seuil.")
        sys.exit(1)
    print("Porte de qualité ouverte.")


if __name__ == "__main__":
    main()
