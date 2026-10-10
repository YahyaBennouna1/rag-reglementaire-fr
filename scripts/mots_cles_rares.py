"""Les questions générées avantagent-elles BM25 ? Recall@10 avec ou sans mot rare de la source.

uv run python scripts/mots_cles_rares.py

Un vrai utilisateur ne connaît pas toujours le vocabulaire exact des guides (« Sysmon », « GPP »).
Si nos questions reprennent ces mots rares, BM25 est avantagé. On compare donc les questions de
développement avec et sans mot rare partagé avec leur extrait source.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from ragfr.config import ChunkingConfig
from ragfr.eval.dataset import load_questions
from ragfr.index import chunk_corpus
from ragfr.retrieval.french_analyzer import analyze

ROOT = Path(__file__).resolve().parents[1]
RARE = 20  # un terme présent dans au plus 20 passages (sur environ 2 100) est « rare »
RUNS = {"BM25": "recherche_1_bm25", "dense": "recherche_2_dense", "hybride": "recherche_3_hybride"}


def recall_by_question(run: str) -> dict[str, float]:
    path = sorted((ROOT / "results").glob(f"*_{run}_dev.json"))[-1]  # le résultat le plus récent
    details = json.loads(path.read_text(encoding="utf-8"))["recherche"]["details"]
    return {d["id"]: d["recall@10"] for d in details if d.get("recall@10") is not None}


def main() -> None:
    passages = chunk_corpus(ChunkingConfig(method="fixed", size=512, overlap=64))
    doc_freq = Counter(term for p in passages for term in set(analyze(p.index_text)))
    recalls = {name: recall_by_question(run) for name, run in RUNS.items()}

    groups = defaultdict(list)  # (type, mot rare partagé ?) -> identifiants des questions
    overlap = defaultdict(list)  # type -> part des mots de la question présents dans l'extrait
    for q in load_questions(ROOT / "data" / "eval" / "questions.jsonl"):
        if q.split != "dev" or q.id not in recalls["BM25"]:
            continue
        terms = set(analyze(q.question))
        shared = terms & {t for ref in q.references for t in analyze(ref.extrait)}
        overlap[q.type].append(len(shared) / max(len(terms), 1))
        has_rare = any(doc_freq[t] <= RARE for t in shared)
        groups[(q.type, has_rare)].append(q.id)
        groups[("tous", has_rare)].append(q.id)

    print("Part des mots de la question présents dans l'extrait source :")
    for qtype, values in overlap.items():
        print(f"  {qtype:16s} {sum(values) / len(values):.0%}  (n = {len(values)})")
    print(f"\n{'type':16s} {'mot rare':9s} {'n':>3s}  " + "  ".join(f"{name:>7s}" for name in RUNS))
    for (qtype, has_rare), ids in sorted(groups.items()):
        means = "  ".join(f"{sum(recalls[name][i] for i in ids) / len(ids):7.3f}" for name in RUNS)
        print(f"{qtype:16s} {'oui' if has_rare else 'non':9s} {len(ids):3d}  {means}")


if __name__ == "__main__":
    main()
