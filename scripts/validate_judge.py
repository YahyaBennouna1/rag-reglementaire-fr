"""Peut-on faire confiance au juge des citations ? On compare ses verdicts aux annotations.

    uv run python scripts/validate_judge.py --model groq/qwen/qwen3.8-27b

Deux mesures :
- l'accord avec les annotations, au-delà du hasard : kappa de Cohen sur la décision qui compte,
  « retirer la phrase (non_soutenu) ou la garder » ;
- les erreurs piégées (phrases faussées exprès, donc « non_soutenu » à coup sûr) : quelle part le
  juge attrape-t-il ?
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from ragfr.citations.verify import judge_sentence
from ragfr.eval.agreement import cohen_kappa
from ragfr.generation import Sentence

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "eval" / "judge_cases.jsonl"
LABELS = ROOT / "data" / "eval" / "judge_labels.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def share(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="groq/qwen/qwen3.8-27b")
    args = parser.parse_args()

    labels = {row["id"]: row for row in read_jsonl(LABELS)}
    cases = [c for c in read_jsonl(CASES) if c["id"] in labels]
    rows = []
    for case in cases:
        verdict = judge_sentence(Sentence(phrase=case["phrase"]), case["passages"], args.model)
        label = labels[case["id"]]
        rows.append(
            {
                "id": case["id"],
                "origine": case["origine"],
                "etiquette": label["etiquette"],
                "verdict_juge": verdict,
                "relu": label.get("relu", False),
            }
        )
        print(f"{case['id']:<16} étiquette={label['etiquette']:<12} juge={verdict}", flush=True)

    # La décision qui compte en production : la phrase est-elle retirée (non_soutenu) ?
    removed_label = [r["etiquette"] == "non_soutenu" for r in rows]
    removed_judge = [r["verdict_juge"] == "non_soutenu" for r in rows]
    # Les pièges « non_soutenu » seulement : les pièges « partiel » n'ont pas à être retirés.
    traps = [r for r in rows if r["origine"] == "piege" and r["etiquette"] == "non_soutenu"]
    system_ok = [r for r in rows if r["origine"] == "systeme" and r["etiquette"] != "non_soutenu"]
    summary = {
        "n_cas": len(rows),
        "n_pieges": len(traps),
        "n_relus": sum(r["relu"] for r in rows),
        "kappa_retrait": round(cohen_kappa(removed_label, removed_judge), 3),
        "accord_3_classes": share([r["etiquette"] == r["verdict_juge"] for r in rows]),
        # Part des phrases faussées que le juge retire (on veut près de 1).
        "pieges_detectes": share([r["verdict_juge"] == "non_soutenu" for r in traps]),
        # Part des bonnes phrases que le juge retire à tort (on veut près de 0).
        "fausses_alertes": share([r["verdict_juge"] == "non_soutenu" for r in system_ok]),
    }
    print(summary)
    result = {"date": datetime.now().isoformat(timespec="seconds"), "modele": args.model}
    result |= {"resume": summary, "details": rows}
    out = ROOT / "results" / f"{datetime.now():%Y-%m-%d_%H%M}_validation_juge.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
