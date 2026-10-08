"""Évalue une configuration sur le jeu de questions et écrit le résultat dans results/.

    uv run python scripts/run_eval.py --config configs/baseline.yaml --split dev
    uv run python scripts/run_eval.py --config configs/baseline.yaml --split dev --answers

Sans --answers : métriques de recherche seulement (aucun appel de LLM sauf routeur/HyDE, rapide).
Avec --answers : on génère aussi les réponses et un juge les note (appels de LLM, plus lent).
Chaque fichier de résultat contient la date, la config complète et le commit Git.
"""

import argparse
import json
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path

from ragfr import llm
from ragfr.config import Config, load_config
from ragfr.eval.answer_metrics import judge_answer
from ragfr.eval.dataset import EvalQuestion, load_questions
from ragfr.eval.retrieval_metrics import covered_refs_by_rank, ndcg_at_k, recall_at_k, reciprocal_rank
from ragfr.pipeline import answer_question, make_search
from ragfr.query.transforms import TransformingRetriever

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
K = 10
# Route attendue pour chaque type de question : sert à mesurer l'exactitude du routeur.
EXPECTED_ROUTE = {
    "factuelle": "simple",
    "tableau": "simple",
    "vague": "vague",
    "multi_documents": "multi_documents",
}


def git_commit() -> str:
    out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT)
    return out.stdout.strip() or "inconnu"


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    return statistics.quantiles(values, n=100)[int(p) - 1] if len(values) > 1 else values[0]


def average(rows: list[dict], key: str) -> float:
    values = [r[key] for r in rows if r.get(key) is not None]
    return round(sum(values) / len(values), 4) if values else 0.0


def by_type(rows: list[dict], metrics: list[str]) -> dict:
    return {
        kind: {m: average([r for r in rows if r["type"] == kind], m) for m in metrics}
        | {"n": sum(r["type"] == kind for r in rows)}
        for kind in sorted({r["type"] for r in rows})
    }


def evaluate_retrieval(cfg: Config, questions: list[EvalQuestion]) -> dict:
    search = make_search(cfg)
    rows, latencies = [], []
    # Les questions sans réponse n'ont pas de passage à retrouver : elles servent à l'abstention.
    for q in [q for q in questions if q.references]:
        start = time.perf_counter()
        passages = search.search(q.question, K)
        latencies.append((time.perf_counter() - start) * 1000)
        found = covered_refs_by_rank(passages, q.references)
        n = len(q.references)
        row = {
            "id": q.id,
            "type": q.type,
            "recall@5": recall_at_k(found, n, 5),
            "recall@10": recall_at_k(found, n, 10),
            "mrr": reciprocal_rank(found),
            "ndcg@10": ndcg_at_k(found, n, 10),
        }
        if isinstance(search, TransformingRetriever) and search.router:
            row["route_ok"] = float(search.last_route == EXPECTED_ROUTE[q.type])
        rows.append(row)

    metrics = ["recall@5", "recall@10", "mrr", "ndcg@10"]
    summary = {m: average(rows, m) for m in metrics}
    if any("route_ok" in r for r in rows):
        summary["exactitude_routeur"] = average(rows, "route_ok")
    summary["latence_p50_ms"] = round(percentile(latencies, 50), 1)
    summary["latence_p95_ms"] = round(percentile(latencies, 95), 1)
    return {"resume": summary, "par_type": by_type(rows, metrics), "details": rows}


def evaluate_answers(cfg: Config, questions: list[EvalQuestion]) -> dict:
    rows, latencies = [], []
    system_usage: dict[str, dict[str, int]] = {}
    for q in questions:
        llm.reset_usage()
        start = time.perf_counter()
        answer = answer_question(cfg, q.question)
        latencies.append(time.perf_counter() - start)
        # On garde les tokens consommés par le système (pas ceux du juge, qui ne tourne pas en production).
        for model, counts in llm.usage.items():
            total = system_usage.setdefault(model, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
            for key, value in counts.items():
                total[key] += value

        row = {"id": q.id, "type": q.type, "abstention": answer.abstained, "reponse": answer.text}
        if q.type == "sans_reponse":
            row["abstention_correcte"] = float(answer.abstained)
        else:
            row["fausse_abstention"] = float(answer.abstained)
            if not answer.abstained:
                verdict = judge_answer(q, answer, cfg.llm.judge_model)
                row |= {
                    "fidelite": float(verdict.fidele),
                    "exactitude": float(verdict.exacte),
                    "pertinence": float(verdict.pertinente),
                }
                if cfg.citations.verify and answer.citations:
                    supported = [c.verdict == "soutenu" for c in answer.citations]
                    row["precision_citations"] = sum(supported) / len(supported)
                if answer.sentences:
                    row["couverture_citations"] = sum(bool(s.sources) for s in answer.sentences) / len(
                        answer.sentences
                    )
        rows.append(row)

    llm.usage.clear()
    llm.usage.update(system_usage)
    cost, unknown = llm.estimated_cost_usd()
    metrics = ["fidelite", "exactitude", "pertinence", "precision_citations", "couverture_citations"]
    summary = {m: average(rows, m) for m in metrics}
    summary["abstention_correcte"] = average(rows, "abstention_correcte")
    summary["fausses_abstentions"] = average(rows, "fausse_abstention")
    summary["latence_p50_s"] = round(percentile(latencies, 50), 2)
    summary["latence_p95_s"] = round(percentile(latencies, 95), 2)
    summary["cout_1000_requetes_usd"] = round(cost / max(len(questions), 1) * 1000, 3)
    summary["modeles_sans_prix_connu"] = unknown
    summary["tokens_par_modele"] = system_usage
    return {"resume": summary, "par_type": by_type(rows, metrics[:3]), "details": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--questions", default=str(ROOT / "data" / "eval" / "questions.jsonl"))
    parser.add_argument("--answers", action="store_true", help="évaluer aussi les réponses (appels de LLM)")
    parser.add_argument("--limit", type=int, help="seulement les N premières questions (essais rapides)")
    parser.add_argument("--per-type", type=int, help="N questions de chaque type (échantillon équilibré)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    questions = load_questions(args.questions)
    if args.split != "all":
        questions = [q for q in questions if q.split == args.split]
    if args.limit:
        questions = questions[: args.limit]
    if args.per_type:
        # Les questions sont rangées par type : --limit ne prendrait que des factuelles.
        counts: dict[str, int] = {}
        sample = []
        for q in questions:
            counts[q.type] = counts.get(q.type, 0) + 1
            if counts[q.type] <= args.per_type:
                sample.append(q)
        questions = sample

    result = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "config": cfg.model_dump(),
        "commit": git_commit(),
        "questions": Path(args.questions).name,
        "split": args.split,
        "n_questions": len(questions),
        "recherche": evaluate_retrieval(cfg, questions),
    }
    print(f"{cfg.name} ({args.split}, {len(questions)} questions)")
    print(f"  recherche : {result['recherche']['resume']}")
    if args.answers:
        result["reponses"] = evaluate_answers(cfg, questions)
        print(f"  réponses  : {result['reponses']['resume']}")

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{cfg.name}_{args.split}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
