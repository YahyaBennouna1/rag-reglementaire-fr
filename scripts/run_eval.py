"""Évalue une configuration sur le jeu de questions et écrit le résultat dans results/.

    uv run python scripts/run_eval.py --config configs/baseline.yaml --split dev

Chaque fichier de résultat contient la date, la config complète et le commit Git :
on sait toujours quel code et quels réglages ont produit quel chiffre.
"""

import argparse
import json
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path

from ragfr.config import load_config
from ragfr.eval.dataset import load_questions
from ragfr.eval.retrieval_metrics import covered_refs_by_rank, ndcg_at_k, recall_at_k, reciprocal_rank
from ragfr.pipeline import make_retriever

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
K = 10


def git_commit() -> str:
    out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT)
    return out.stdout.strip() or "inconnu"


def percentile(values: list[float], p: float) -> float:
    return statistics.quantiles(values, n=100)[int(p) - 1] if len(values) > 1 else values[0]


def average(rows: list[dict], key: str) -> float:
    return round(sum(r[key] for r in rows) / len(rows), 4) if rows else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--questions", default=str(ROOT / "data" / "eval" / "questions.jsonl"))
    args = parser.parse_args()

    cfg = load_config(args.config)
    questions = load_questions(args.questions)
    if args.split != "all":
        questions = [q for q in questions if q.split == args.split]
    # Les questions sans réponse n'ont pas de passage à retrouver : elles servent à l'abstention (Partie 5).
    with_refs = [q for q in questions if q.references]
    retriever = make_retriever(cfg)

    rows, latencies = [], []
    for q in with_refs:
        start = time.perf_counter()
        passages = retriever.search(q.question, K)
        latencies.append((time.perf_counter() - start) * 1000)
        found = covered_refs_by_rank(passages, q.references)
        n = len(q.references)
        rows.append(
            {
                "id": q.id,
                "type": q.type,
                "recall@5": recall_at_k(found, n, 5),
                "recall@10": recall_at_k(found, n, 10),
                "mrr": reciprocal_rank(found),
                "ndcg@10": ndcg_at_k(found, n, 10),
            }
        )

    metrics = ["recall@5", "recall@10", "mrr", "ndcg@10"]
    summary = {m: average(rows, m) for m in metrics}
    summary["latence_p50_ms"] = round(percentile(latencies, 50), 1)
    summary["latence_p95_ms"] = round(percentile(latencies, 95), 1)
    by_type = {
        kind: {m: average([r for r in rows if r["type"] == kind], m) for m in metrics}
        | {"n": sum(r["type"] == kind for r in rows)}
        for kind in sorted({r["type"] for r in rows})
    }

    result = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "config": cfg.model_dump(),
        "commit": git_commit(),
        "questions": Path(args.questions).name,
        "split": args.split,
        "n_questions": len(rows),
        "recherche": summary,
        "par_type": by_type,
        "details": rows,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{cfg.name}_{args.split}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{cfg.name} ({args.split}, {len(rows)} questions) : {summary}")
    for kind, values in by_type.items():
        print(f"  {kind:16s} {values}")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
