"""Relire les annotations des cas de validation du juge, dans le terminal.

    uv run python scripts/review_judge_cases.py

Pour chaque cas pas encore relu : la phrase, les passages cités, et l'étiquette proposée.
[Entrée] confirmer, [s] soutenu, [p] partiel, [n] non_soutenu, [q] quitter.
La progression est enregistrée après chaque décision : on peut s'arrêter et reprendre.

On juge seulement : « les passages affichés disent-ils ce que dit la phrase ? »
Pas besoin d'être expert en cybersécurité, le texte de la preuve est à l'écran.
"""

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "eval" / "judge_cases.jsonl"
LABELS = ROOT / "data" / "eval" / "judge_labels.jsonl"
KEYS = {"s": "soutenu", "p": "partiel", "n": "non_soutenu"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(labels: list[dict]) -> None:
    LABELS.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in labels), encoding="utf-8")


def main() -> None:
    cases = {c["id"]: c for c in read_jsonl(CASES)}
    labels = read_jsonl(LABELS)
    todo = [row for row in labels if not row.get("relu")]
    print(f"{len(todo)} cas à relire sur {len(labels)}.")

    for index, row in enumerate(todo, start=1):
        case = cases[row["id"]]
        print("\n" + "=" * 90)
        print(f"[{index}/{len(todo)}]  {case['id']}")
        print(textwrap.fill(f"PHRASE : « {case['phrase']} »", 90))
        print("-" * 90 + "\nPASSAGES CITÉS (la preuve) :")
        print(case["passages"])
        print("-" * 90)
        print(f"Étiquette proposée : {row['etiquette'].upper()}  ({row.get('raison', '')})")
        choice = input("[Entrée] confirmer · [s] soutenu · [p] partiel · [n] non_soutenu · [q] quitter > ")
        choice = choice.strip().lower()
        if choice == "q":
            break
        if choice in KEYS:
            row["etiquette"] = KEYS[choice]
        row["relu"] = True
        save(labels)  # après chaque décision : rien n'est perdu si on quitte

    print(f"\nRelus : {sum(r.get('relu', False) for r in labels)}/{len(labels)}")


if __name__ == "__main__":
    main()
