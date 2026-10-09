"""Intervalles de confiance (bootstrap) pour les mesures de recherche, et comparaison de deux configurations.

    uv run python scripts/intervalles.py results/A.json results/B.json --metric mrr

Avec 49 questions, un écart de 0,03 entre deux méthodes peut venir du hasard du tirage des questions.
Le bootstrap répond à : « si on avait tiré d'autres questions du même genre, de combien le score
aurait-il varié ? ». On retire les questions au hasard, avec remise, 10 000 fois.

Pour comparer A et B, on travaille sur la DIFFÉRENCE question par question (mesures appariées) :
c'est plus précis que de comparer deux intervalles, car les deux méthodes voient les mêmes questions.
"""

import argparse
import json
import random
from pathlib import Path

ROUNDS = 10_000


def per_question(path: Path, metric: str) -> dict[str, float]:
    details = json.loads(path.read_text(encoding="utf-8"))["recherche"]["details"]
    return {d["id"]: d[metric] for d in details if d.get(metric) is not None}


def bootstrap(values: list[float], seed: int = 0) -> tuple[float, float, float]:
    """(moyenne, borne basse à 2,5 %, borne haute à 97,5 %)."""
    rng = random.Random(seed)  # graine fixe : le même calcul donne le même résultat
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(ROUNDS))
    return sum(values) / len(values), means[int(0.025 * ROUNDS)], means[int(0.975 * ROUNDS)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--metric", default="recall@10")
    args = parser.parse_args()

    scores = {f: per_question(f, args.metric) for f in args.files}
    for f, s in scores.items():
        mean, low, high = bootstrap(list(s.values()))
        print(f"{f.stem:<50} {args.metric} = {mean:.3f}  [IC 95 % : {low:.3f} – {high:.3f}]  (n = {len(s)})")

    if len(args.files) == 2:
        a, b = (scores[f] for f in args.files)
        common = sorted(set(a) & set(b))
        diffs = [b[q] - a[q] for q in common]
        mean, low, high = bootstrap(diffs)
        significant = low > 0 or high < 0  # l'intervalle ne contient pas 0
        verdict = "écart significatif" if significant else "écart NON significatif (l'intervalle contient 0)"
        print(f"\nDifférence (2e - 1er) : {mean:+.3f}  [IC 95 % : {low:+.3f} – {high:+.3f}]  -> {verdict}")


if __name__ == "__main__":
    main()
