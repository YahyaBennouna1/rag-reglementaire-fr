"""Mesure le masquage des données personnelles : ce qui est trouvé, et ce qui est masqué à tort.

    uv run python scripts/eval_pii.py

- 20 questions avec des données personnelles (data/eval/pii.jsonl), dont on connaît les types :
  pour chaque type, quelle part est trouvée ?
- les 145 questions de développement, sans données personnelles : combien sont modifiées à tort ?
  Un terme technique pris pour un nom de personne serait masqué, et la recherche s'en trouverait abîmée.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ragfr.eval.dataset import load_questions
from ragfr.guardrails.pii import mask_pii

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    cases = [json.loads(line) for line in (ROOT / "data" / "eval" / "pii.jsonl").open(encoding="utf-8")]
    found_by_type = defaultdict(list)
    details = []
    for case in cases:
        masked, found = mask_pii(case["texte"])
        for kind in case["attendu"]:
            found_by_type[kind].append(kind in found)
        details.append({**case, "trouve": found, "masque": masked})
        if not case["attendu"] and found:
            print("   ^ masquée à tort (aucune donnée personnelle attendue)")
        print(f"{case['id']} attendu={case['attendu']} trouvé={found}\n   {masked}")

    dev = [q for q in load_questions(ROOT / "data" / "eval" / "questions.jsonl") if q.split == "dev"]
    wrongly_masked = []
    for q in dev:
        masked, found = mask_pii(q.question)
        if found:
            wrongly_masked.append({"id": q.id, "question": q.question, "masque": masked, "trouve": found})

    clean = [d for d in details if not d["attendu"]]  # questions sans donnée personnelle
    summary = {
        "trouves_par_type": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(found_by_type.items())},
        "trouves_total": f"{sum(map(sum, found_by_type.values()))}/{sum(map(len, found_by_type.values()))}",
        "questions_dev_modifiees": f"{len(wrongly_masked)}/{len(dev)}",
        "questions_sans_donnee_modifiees": f"{sum(bool(d['trouve']) for d in clean)}/{len(clean)}",
    }
    print(f"\n{summary}\nQuestions de développement modifiées :")
    for row in wrongly_masked:
        print(f"  {row['id']} {row['trouve']} : {row['masque'][:110]}")

    result = {"date": datetime.now().isoformat(timespec="seconds"), "resume": summary}
    result |= {"details": details, "questions_dev_modifiees": wrongly_masked}
    out = ROOT / "results" / f"{datetime.now():%Y-%m-%d_%H%M}_garde_fous_pii.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
