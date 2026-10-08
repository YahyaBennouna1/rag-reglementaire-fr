"""Construit les cas pour valider le juge des citations : des phrases réelles du système.

    uv run python scripts/build_judge_cases.py --per-type 8

Pour chaque question de développement (sauf « sans réponse »), on fait répondre le système, puis on
garde chaque phrase avec le texte exact de ses passages cités : exactement ce que voit le juge
(citations/verify.py). Les étiquettes « vraies » sont ajoutées ensuite (annotation, puis relecture).
"""

import argparse
import json
from pathlib import Path

from ragfr.config import load_config
from ragfr.eval.dataset import load_questions
from ragfr.pipeline import answer_question

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "eval" / "judge_cases.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=str(ROOT / "configs" / "ablation" / "reponses_2_agent.yaml"))
    parser.add_argument("--per-type", type=int, default=8)
    args = parser.parse_args()

    cfg = load_config(args.config)
    questions = [q for q in load_questions(ROOT / "data" / "eval" / "questions.jsonl") if q.split == "dev"]
    counts: dict[str, int] = {}
    cases = []
    for q in questions:
        if q.type == "sans_reponse":
            continue
        counts[q.type] = counts.get(q.type, 0) + 1
        if counts[q.type] > args.per_type:
            continue
        answer = answer_question(cfg, q.question)
        by_label = {f"P{i}": p for i, p in enumerate(answer.passages, start=1)}
        for n, sentence in enumerate(answer.sentences, start=1):
            cited = [by_label[s] for s in sentence.sources if s in by_label]
            if not cited:
                continue  # sans source valide, le juge n'est même pas appelé (verdict automatique)
            cases.append(
                {
                    "id": f"{q.id}-s{n}",
                    "question": q.question,
                    "phrase": sentence.phrase,
                    # Même format que verify_answer : le juge et l'annotateur lisent le même texte.
                    "passages": "\n\n".join(f"[{p.titre}, p. {p.page}]\n{p.text}" for p in cited),
                    "origine": "systeme",
                }
            )
        print(f"{q.id} ({q.type}) : {len(answer.sentences)} phrase(s)", flush=True)

    OUT.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    print(f"{len(cases)} cas -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
