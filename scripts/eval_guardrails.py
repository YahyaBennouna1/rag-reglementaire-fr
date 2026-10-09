"""Mesure le détecteur d'injection : attaques détectées, et fausses alertes sur de vraies questions.

    uv run python scripts/eval_guardrails.py

Trois groupes de textes :
- 40 attaques (data/eval/injections.jsonl, « attaque » = true), par famille ;
- 15 questions normales qui PARLENT d'attaques (pièges bénins) : elles ne doivent pas être bloquées ;
- les 145 questions de développement du jeu d'évaluation : des questions d'utilisateurs ordinaires.
On note chaque texte une fois avec les deux couches, puis on compare les combinaisons.
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ragfr.eval.dataset import load_questions
from ragfr.guardrails.injection import classify_injection, injection_score

ROOT = Path(__file__).resolve().parent.parent
THRESHOLDS = [0.3, 0.5, 0.7, 0.9]


def share(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def measure(rows: list[dict], blocked) -> dict:
    """Taux de détection (par famille) et de fausses alertes, pour une règle de blocage donnée."""
    attacks = [r for r in rows if r["attaque"]]
    by_family = defaultdict(list)
    for r in attacks:
        by_family[r["famille"]].append(blocked(r))
    return {
        "attaques_detectees": share([blocked(r) for r in attacks]),
        "par_famille": {f: share(v) for f, v in sorted(by_family.items())},
        "fausses_alertes_pieges": share([blocked(r) for r in rows if r["famille"] == "piege_benin"]),
        "fausses_alertes_questions_dev": share([blocked(r) for r in rows if r["famille"] == "question_dev"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="groq/meta-llama/llama-prompt-guard-2-86m")
    parser.add_argument("--classifier", default="groq/openai/gpt-oss-20b", help="couche 2 (LLM)")
    args = parser.parse_args()

    rows = [json.loads(line) for line in (ROOT / "data" / "eval" / "injections.jsonl").open(encoding="utf-8")]
    dev = [q for q in load_questions(ROOT / "data" / "eval" / "questions.jsonl") if q.split == "dev"]
    rows += [{"id": q.id, "attaque": False, "famille": "question_dev", "texte": q.question} for q in dev]

    for row in rows:
        row["score"] = round(injection_score(row["texte"], args.model), 4)
        verdict = classify_injection(row["texte"], args.classifier)
        row["llm_attaque"], row["llm_raison"] = verdict.attaque, verdict.raison
    print(f"{len(rows)} textes notés")

    results = {f"couche 1, seuil {t}": measure(rows, lambda r, t=t: r["score"] >= t) for t in THRESHOLDS}
    results["couche 2 (LLM) seule"] = measure(rows, lambda r: r["llm_attaque"])
    results["couches 1 + 2"] = measure(rows, lambda r: r["score"] >= 0.5 or r["llm_attaque"])
    for name, values in results.items():
        print(f"{name} : {values}")

    print("\nAttaques non détectées par les deux couches :")
    for r in rows:
        if r["attaque"] and r["score"] < 0.5 and not r["llm_attaque"]:
            print(f"  {r['id']} ({r['famille']}, score {r['score']}) : {r['texte'][:80]}")
    print("\nFausses alertes des deux couches :")
    for r in rows:
        if not r["attaque"] and (r["score"] >= 0.5 or r["llm_attaque"]):
            print(f"  {r['id']} ({r['famille']}) : {r['texte'][:80]} -> {r['llm_raison'][:100]}")

    result = {"date": datetime.now().isoformat(timespec="seconds"), "modele": args.model}
    result |= {"classifieur": args.classifier, "resultats": results, "details": rows}
    out = ROOT / "results" / f"{datetime.now():%Y-%m-%d_%H%M}_garde_fous_injection.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
