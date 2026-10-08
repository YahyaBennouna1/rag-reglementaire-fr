"""Relecture humaine des questions candidates, une par une, dans le terminal.

Pour chaque question : [v] valider, [c] corriger, [r] rejeter, [s] passer, [q] quitter.
La progression est enregistrée après chaque décision : on peut s'arrêter et reprendre plus tard.
"""

import textwrap
from pathlib import Path

from ragfr.eval.dataset import load_questions, save_questions

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "candidates.jsonl"


def show(q, index: int, total: int) -> None:
    print("\n" + "=" * 80)
    print(f"[{index}/{total}]  {q.id}  type={q.type}")
    print(textwrap.fill(f"QUESTION : {q.question}", 80))
    print(textwrap.fill(f"RÉPONSE  : {q.reponse_reference}", 80))
    for ref in q.references:
        print(textwrap.fill(f"EXTRAIT  ({ref.doc_ref}, p. {ref.page}) : « {ref.extrait} »", 80))
    if q.type == "sans_reponse":
        print("⚠ Vérifie que les guides ne répondent VRAIMENT pas à cette question.")


def main() -> None:
    questions = load_questions(CANDIDATES)
    todo = [q for q in questions if q.statut == "genere"]
    print(f"{len(todo)} questions à relire sur {len(questions)}.")
    print("Critères : réponse exacte et complète, question naturelle et compréhensible seule,")
    print("pas de copie mot pour mot du guide, extrait qui justifie bien la réponse.")

    for i, q in enumerate(todo, start=1):
        show(q, i, len(todo))
        choice = input("[v]alider [c]orriger [r]ejeter [s]auter [q]uitter > ").strip().lower()
        if choice == "q":
            break
        if choice == "v":
            q.statut = "valide"
        elif choice == "r":
            q.statut = "rejete"
        elif choice == "c":
            new_q = input("Nouvelle question (Entrée = garder) : ").strip()
            new_a = input("Nouvelle réponse (Entrée = garder) : ").strip()
            q.question = new_q or q.question
            q.reponse_reference = new_a or q.reponse_reference
            q.statut = "corrige"
        save_questions(questions, CANDIDATES)  # sauvegarde après chaque décision

    counts = {s: sum(q.statut == s for q in questions) for s in ("valide", "corrige", "rejete", "genere")}
    print(f"\nBilan : {counts}")


if __name__ == "__main__":
    main()
