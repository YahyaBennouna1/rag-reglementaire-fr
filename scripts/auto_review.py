"""Relecture AUTOMATIQUE des questions candidates par un LLM, avec la grille de la relecture humaine.

C'est une validation par IA, et elle est présentée comme telle. Pour savoir si on peut lui faire
confiance, on la CALIBRE sur les questions que l'humain a auditées (data/eval/audit.jsonl) :
accord et kappa de Cohen entre le LLM et l'humain.

    uv run python scripts/auto_review.py --calibrate   # seulement les questions auditées par l'humain
    uv run python scripts/auto_review.py --apply       # toutes, puis met à jour les statuts

Les décisions de l'humain restent prioritaires : une question auditée garde son verdict humain.
"""

import argparse
import json
from pathlib import Path

from pydantic import BaseModel

from ragfr.config import load_config
from ragfr.eval.agreement import cohen_kappa
from ragfr.eval.dataset import EvalQuestion, load_questions, save_questions
from ragfr.eval.review import source_context
from ragfr.llm import complete_json
from ragfr.pipeline import make_retriever

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "candidates.jsonl"
AUDIT_FILE = ROOT / "data" / "eval" / "audit.jsonl"
OUT = ROOT / "data" / "eval" / "auto_review.jsonl"
MODEL = "groq/openai/gpt-oss-120b"  # le juge du projet : une autre famille que le générateur (Gemini)


class Verdict(BaseModel):
    extrait_prouve: bool = True
    reponse_complete: bool = True
    question_claire: bool
    une_seule_reponse: bool = True
    hors_corpus: bool = True
    explication: str = ""

    @property
    def ok(self) -> bool:
        return (
            all([self.extrait_prouve, self.reponse_complete, self.question_claire, self.une_seule_reponse])
            and self.hors_corpus
        )


RULES = """Tu relis une question d'un jeu d'évaluation sur les guides de cybersécurité de l'ANSSI.
Tu ne juges PAS si la réponse est vraie dans l'absolu : tu juges si elle est FIDÈLE AU GUIDE fourni.
Sois exigeant : dans le doute, réponds false."""

PROMPT_ANSWERABLE = """{rules}

QUESTION : {question}
RÉPONSE DE RÉFÉRENCE : {reponse}
{sources}

Critères (true ou false) :
- "extrait_prouve" : en lisant l'extrait (ou sa ligne de tableau), arrive-t-on à la même réponse ?
- "reponse_complete" : la réponse contient-elle tout ce que le passage dit sur ce point ?
- "question_claire" : la question se comprend-elle SEULE, sans avoir le guide sous les yeux ?
  Réponds false si elle parle DU DOCUMENT au lieu du sujet : « selon le guide », « ce guide »,
  « ce tableau », « la section 3.4 », « la version 2.0 du guide », « qu'est-ce qui a été ajouté ».
  Un administrateur ne pose pas ce genre de question : il demande ce qu'il faut faire.
- "une_seule_reponse" : la question n'admet-elle qu'une bonne réponse
  (pas ambiguë, pas dépendante du contexte) ?
Réponds en JSON : {{"extrait_prouve": true, "reponse_complete": true, "question_claire": true,
"une_seule_reponse": true, "explication": "une phrase"}}"""

PROMPT_UNANSWERABLE = """{rules}

Cette question doit être SANS RÉPONSE dans les guides : c'est un test d'abstention.
QUESTION : {question}

Voici les passages des guides les plus proches de la question :
{passages}

Critères (true ou false) :
- "hors_corpus" : ces passages ne permettent-ils VRAIMENT PAS de répondre à la question ?
- "question_claire" : la question se comprend-elle seule, et reste-t-elle proche des thèmes des guides ?
Réponds en JSON : {{"hors_corpus": true, "question_claire": true, "explication": "une phrase"}}"""


def review_one(q: EvalQuestion, retriever, model: str = MODEL) -> Verdict:
    if q.type == "sans_reponse":
        passages = retriever.search(q.question, 5)
        text = "\n\n".join(f"[{p.titre}, p. {p.page}]\n{p.text[:800]}" for p in passages)
        prompt = PROMPT_UNANSWERABLE.format(rules=RULES, question=q.question, passages=text)
    else:
        sources = "\n".join(
            f"EXTRAIT ({r.doc_ref}, p. {r.page}) : « {r.extrait} »\nPASSAGE SOURCE :\n"
            f"{source_context(r.doc_ref, r.extrait)}\n"
            for r in q.references
        )
        prompt = PROMPT_ANSWERABLE.format(
            rules=RULES, question=q.question, reponse=q.reponse_reference, sources=sources
        )
    return complete_json([{"role": "user", "content": prompt}], model=model, schema=Verdict)


def load_audit() -> dict[str, dict]:
    if not AUDIT_FILE.exists():
        return {}
    rows = [json.loads(line) for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines() if line]
    return {r["id"]: r for r in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--calibrate", action="store_true", help="seulement les questions auditées")
    parser.add_argument(
        "--apply", action="store_true", help="toutes les questions, puis mise à jour des statuts"
    )
    parser.add_argument("--model", default=MODEL, help="juge LiteLLM (par défaut : le juge du projet)")
    args = parser.parse_args()

    questions = load_questions(CANDIDATES)
    audit = load_audit()
    retriever = make_retriever(load_config(ROOT / "configs" / "ablation" / "recherche_1_bm25.yaml"))
    targets = [q for q in questions if q.id in audit] if args.calibrate else questions

    # Reprise : les verdicts déjà obtenus sont gardés, on ne relit que le reste (idempotence).
    verdicts: dict[str, Verdict] = {}
    if OUT.exists() and not args.calibrate:
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line:
                row = json.loads(line)
                verdicts[row["id"]] = Verdict.model_validate(row)
    todo = [q for q in targets if q.id not in verdicts]
    print(f"{len(verdicts)} verdicts déjà obtenus, {len(todo)} questions à relire avec {args.model}.")

    mode = "w" if args.calibrate else "a"
    with open(OUT, mode, encoding="utf-8", newline="\n") as f:
        for i, q in enumerate(todo, start=1):
            try:
                verdicts[q.id] = review_one(q, retriever, args.model)
            except Exception as e:  # un appel raté ne doit pas arrêter la relecture
                print(f"  [erreur] {q.id} : {type(e).__name__}")
                continue
            f.write(
                json.dumps(
                    {
                        "id": q.id,
                        "type": q.type,
                        "ok": verdicts[q.id].ok,
                        "juge": args.model,
                        **verdicts[q.id].model_dump(),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            if i % 25 == 0:
                print(f"  {i}/{len(todo)}", flush=True)

    # Calibration : accord avec l'humain sur les questions auditées
    common = [qid for qid in audit if qid in verdicts]
    if common:
        human = [audit[qid]["ok"] for qid in common]
        llm = [verdicts[qid].ok for qid in common]
        agree = sum(h == m for h, m in zip(human, llm, strict=True)) / len(common)
        print(f"\nCalibration sur {len(common)} questions auditées par l'humain :")
        print(f"  accord {agree:.0%} ; kappa de Cohen {cohen_kappa(human, llm):.2f}")
        print(f"  l'humain rejette {human.count(False)}, le LLM rejette {llm.count(False)}")

    rejected = sum(not v.ok for v in verdicts.values())
    share = rejected / max(1, len(verdicts))
    print(f"\n{len(verdicts)} questions relues par le LLM, {rejected} rejetées ({share:.0%}).")

    if args.apply:
        for q in questions:
            if q.id in audit:
                continue  # le verdict humain reste prioritaire
            if q.id in verdicts:
                q.statut = "valide" if verdicts[q.id].ok else "rejete"
            elif q.statut == "valide":
                q.statut = "genere"  # jamais relue par le juge : on ne la garde pas sans vérification
        save_questions(questions, CANDIDATES)
        kept = {
            t: sum(q.type == t and q.statut in ("valide", "corrige") for q in questions)
            for t in sorted({q.type for q in questions})
        }
        print(f"Statuts mis à jour. Questions acceptées par type : {kept}")


if __name__ == "__main__":
    main()
