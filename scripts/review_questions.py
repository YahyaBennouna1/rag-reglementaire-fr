"""Relecture humaine des questions candidates, dans le terminal.

Deux modes :
- relecture : chaque question encore au statut « genere » ; [v] valider, [c] corriger, [r] rejeter,
  [s] passer, [q] quitter. La progression est enregistrée après chaque décision.
- audit (--audit N) : N questions déjà validées, tirées au hasard, relues critère par critère.
  Le taux d'erreur mesuré dit si la relecture rapide est fiable (data/eval/audit.jsonl).

On ne juge pas si la réponse est vraie dans l'absolu (il faudrait être expert) :
on juge si elle est FIDÈLE AU GUIDE, qui est affiché à l'écran.
"""

import argparse
import json
import random
import re
import textwrap
from pathlib import Path

from ragfr.eval.dataset import QUOTAS, EvalQuestion, load_questions, save_questions
from ragfr.eval.retrieval_metrics import normalize
from ragfr.ingestion.models import ParsedDocument

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "candidates.jsonl"
AUDIT_FILE = ROOT / "data" / "eval" / "audit.jsonl"
PARSED_DIR = ROOT / "data" / "parsed"

CRITERIA = [
    ("extrait_prouve", "1. L'extrait (ou sa ligne de tableau) PROUVE-t-il la réponse ?"),
    ("reponse_complete", "2. La réponse est-elle COMPLÈTE (le passage ne dit pas plus) ?"),
    ("question_claire", "3. La question se comprend-elle SEULE, sans le guide sous les yeux ?"),
    ("une_seule_reponse", "4. N'y a-t-il qu'UNE bonne réponse (pas d'autre passage contradictoire) ?"),
]
UNANSWERABLE_CRITERIA = [
    ("hors_corpus", "1. Les guides ne répondent-ils VRAIMENT pas (cherche dans data/parsed/*.md) ?"),
    ("question_claire", "2. La question se comprend-elle seule et reste-t-elle proche des thèmes ?"),
]

_docs: dict[str, ParsedDocument] = {}


def source_context(doc_ref: str, extrait: str, width: int = 1500) -> str:
    """Le texte du guide autour de l'extrait : c'est la référence pour juger."""
    if doc_ref not in _docs:
        _docs[doc_ref] = ParsedDocument.model_validate_json(
            (PARSED_DIR / f"{doc_ref}.json").read_text(encoding="utf-8")
        )
    elements = _docs[doc_ref].elements
    target = normalize(extrait)
    for i, el in enumerate(elements):
        if target and target in normalize(el.text):
            around = elements[max(0, i - 2) : i + 3]
            # Les tableaux Markdown ont de très longues lignes de tirets et d'espaces : on les raccourcit.
            text = "\n".join(e.text for e in around)
            text = re.sub(r"-{4,}", "---", text)
            text = re.sub(r" {2,}", " ", text)
            section = " > ".join(el.section_path)
            return f"[{section}]\n{text[:width]}{'…' if len(text) > width else ''}"
    return "(passage source introuvable)"


def show(q: EvalQuestion, index: int, total: int) -> None:
    print("\n" + "=" * 90)
    print(f"[{index}/{total}]  {q.id}  type={q.type}")
    print(textwrap.fill(f"QUESTION : {q.question}", 90))
    print(textwrap.fill(f"RÉPONSE  : {q.reponse_reference}", 90))
    for ref in q.references:
        print(textwrap.fill(f"EXTRAIT  ({ref.doc_ref}, p. {ref.page}) : « {ref.extrait} »", 90))
        print("-" * 90 + "\nPASSAGE SOURCE (la référence pour juger) :")
        print(source_context(ref.doc_ref, ref.extrait))
    print("-" * 90)
    for _, label in UNANSWERABLE_CRITERIA if q.type == "sans_reponse" else CRITERIA:
        print("   " + label)


def accepted_count(questions: list[EvalQuestion], kind: str) -> int:
    return sum(q.type == kind and q.statut in ("valide", "corrige") for q in questions)


def review(questions: list[EvalQuestion]) -> None:
    """Relecture ciblée : ordre aléatoire, et on passe les types qui ont déjà atteint leur quota."""
    todo = [q for q in questions if q.statut == "genere"]
    random.Random(11).shuffle(todo)  # au hasard : chaque type avance en même temps
    print(f"{len(todo)} questions à relire. Objectif : {QUOTAS}")
    print("Règle : on juge la FIDÉLITÉ AU GUIDE, pas la vérité absolue. Dans le doute, on rejette.")
    for i, q in enumerate(todo, start=1):
        if accepted_count(questions, q.type) >= QUOTAS[q.type]:
            continue  # quota atteint pour ce type : inutile de relire plus
        progress = {k: f"{accepted_count(questions, k)}/{v}" for k, v in QUOTAS.items()}
        print(f"\nAvancement : {progress}")
        show(q, i, len(todo))
        choice = input("[v]alider [c]orriger [r]ejeter [s]auter [q]uitter > ").strip().lower()
        if choice == "q":
            break
        if choice == "v":
            q.statut = "valide"
        elif choice == "r":
            q.statut = "rejete"
        elif choice == "c":
            q.question = input("Nouvelle question (Entrée = garder) : ").strip() or q.question
            q.reponse_reference = (
                input("Nouvelle réponse (Entrée = garder) : ").strip() or q.reponse_reference
            )
            q.statut = "corrige"
        save_questions(questions, CANDIDATES)  # sauvegarde après chaque décision

    counts = {s: sum(q.statut == s for q in questions) for s in ("valide", "corrige", "rejete", "genere")}
    print(f"\nBilan : {counts}")


def reset(questions: list[EvalQuestion]) -> None:
    """Remet à relire les questions validées trop vite. Celles qui ont réussi l'audit restent validées."""
    audited_ok = set()
    if AUDIT_FILE.exists():
        rows = [json.loads(line) for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines() if line]
        audited_ok = {r["id"] for r in rows if r["ok"]}
    n = 0
    for q in questions:
        if q.statut == "valide" and q.id not in audited_ok:
            q.statut = "genere"
            n += 1
    save_questions(questions, CANDIDATES)
    print(f"{n} questions remises à relire ; {len(audited_ok)} gardées (réussies à l'audit).")


def audit(questions: list[EvalQuestion], n: int, seed: int = 7) -> None:
    done = set()
    if AUDIT_FILE.exists():
        done = {
            json.loads(line)["id"] for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines() if line
        }
    # Les questions déjà auditées restent dans le tirage même si l'audit les a rejetées :
    # sinon l'échantillon changerait à chaque reprise.
    pool = [q for q in questions if q.statut in ("valide", "corrige") or q.id in done]
    sample = random.Random(seed).sample(pool, min(n, len(pool)))
    todo = [q for q in sample if q.id not in done]
    print(f"Audit : {len(sample)} questions tirées au hasard, {len(todo)} restantes.")
    print("Réponds o (oui) ou n (non) à chaque critère, en t'appuyant sur le PASSAGE SOURCE.")

    for i, q in enumerate(todo, start=1):
        show(q, i, len(todo))
        answers = {}
        for key, label in UNANSWERABLE_CRITERIA if q.type == "sans_reponse" else CRITERIA:
            reply = ""
            while reply not in ("o", "n", "q"):
                reply = input(f"{label} [o/n, q=quitter] > ").strip().lower()
            if reply == "q":
                return report_audit()
            answers[key] = reply == "o"
        ok = all(answers.values())
        if not ok:  # l'audit corrige aussi le jeu : une question qui échoue à un critère est rejetée
            q.statut = "rejete"
            save_questions(questions, CANDIDATES)
        with open(AUDIT_FILE, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"id": q.id, "type": q.type, "ok": ok, **answers}, ensure_ascii=False) + "\n")
    report_audit()


def report_audit() -> None:
    if not AUDIT_FILE.exists():
        return
    rows = [json.loads(line) for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines() if line]
    errors = sum(not r["ok"] for r in rows)
    print(f"\nAudit : {len(rows)} questions relues en détail, {errors} en erreur ({errors / len(rows):.0%}).")
    for key, label in CRITERIA + UNANSWERABLE_CRITERIA:
        failed = sum(r.get(key) is False for r in rows)
        if failed:
            print(f"  {failed} échec(s) au critère : {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audit", type=int, metavar="N", help="auditer N questions déjà validées")
    parser.add_argument("--reset", action="store_true", help="remettre à relire les validées trop vite")
    args = parser.parse_args()
    questions = load_questions(CANDIDATES)
    if args.reset:
        reset(questions)
    elif args.audit:
        audit(questions, args.audit)
    else:
        review(questions)


if __name__ == "__main__":
    main()
