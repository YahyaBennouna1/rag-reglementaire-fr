"""Génère des questions candidates pour le jeu d'évaluation -> data/eval/candidates.jsonl.

Le LLM propose, l'humain valide : chaque candidate est ensuite relue avec review_questions.py.
Filtres automatiques avant relecture :
- l'extrait cité doit exister mot pour mot dans le passage source (sinon le LLM l'a inventé) ;
- la question ne doit pas recopier l'extrait (elle avantagerait injustement BM25) ;
- pas de doublons.
"""

import argparse
import random
import re
from pathlib import Path

from pydantic import BaseModel

from ragfr.eval.dataset import EvalQuestion, Reference, save_questions
from ragfr.eval.retrieval_metrics import normalize
from ragfr.index import load_parsed_documents
from ragfr.ingestion.models import Element, ParsedDocument
from ragfr.llm import complete_json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "eval" / "candidates.jsonl"

# Une autre famille que le générateur des réponses (Gemini) : un modèle qui répondrait à ses propres
# questions serait avantagé. (gemini-3.5-flash, essayé d'abord, atteignait vite son quota gratuit : 429.)
MODEL = "groq/qwen/qwen3.8-27b"
SEED = 42
TARGETS = {"factuelle": 120, "tableau": 60, "multi_documents": 60, "vague": 30, "sans_reponse": 30}

STOPWORDS = set(
    "le la les un une des de du d l et ou à au aux en dans par pour sur avec sans ce cet cette ces "
    "qui que quoi dont où est sont être doit doivent il elle ils elles on se sa son ses leur leurs "
    "ne pas plus peut peuvent tout tous toute toutes afin ainsi comme si lors entre".split()
)


class Generated(BaseModel):
    possible: bool = True
    question: str = ""
    reponse: str = ""
    extrait: str = ""


class GeneratedMulti(BaseModel):
    possible: bool = True
    question: str = ""
    reponse: str = ""
    extrait_1: str = ""
    extrait_2: str = ""


class Rewritten(BaseModel):
    question: str


class Unanswerable(BaseModel):
    questions: list[str]


SYSTEM = (
    "Tu crées un jeu d'évaluation pour un assistant qui répond à des questions sur les guides de "
    "cybersécurité de l'ANSSI. Les questions doivent ressembler à celles d'un administrateur ou d'un "
    "responsable sécurité, en français naturel. Réponds uniquement en JSON."
)

PROMPT_SINGLE = """Passage extrait du guide « {titre} » (section : {section}) :
<passage>
{texte}
</passage>

Écris UNE question {consigne}
Règles :
- la réponse se trouve dans le passage, sans connaissance extérieure ;
- n'emploie pas les phrases du passage mot pour mot : reformule comme le ferait un utilisateur ;
- la question doit avoir du sens seule (pas de « dans ce passage », « selon ce texte ») ;
- "extrait" : la phrase ou ligne du passage qui justifie la réponse, COPIÉE À L'IDENTIQUE (30 mots maximum).
Si le passage ne permet pas une bonne question, mets "possible": false.
Format : {{"possible": true, "question": "...", "reponse": "...", "extrait": "..."}}"""

PROMPT_MULTI = """Deux passages de deux guides différents de l'ANSSI.
<passage_1 guide="{titre1}">
{texte1}
</passage_1>
<passage_2 guide="{titre2}">
{texte2}
</passage_2>

Si les deux passages traitent d'un sujet commun, écris UNE question dont la réponse complète demande
les DEUX passages (comparaison, ou combinaison de deux recommandations).
Mêmes règles : pas de copie mot pour mot, la question a du sens seule, et chaque extrait est copié
à l'identique de son passage (30 mots maximum).
Sinon, mets "possible": false.
Format : {{"possible": true, "question": "...", "reponse": "...", "extrait_1": "...", "extrait_2": "..."}}"""

PROMPT_VAGUE = """Réécris cette question comme la poserait quelqu'un de pressé ou peu technique :
plus courte, plus vague, avec d'autres mots (pas les termes techniques exacts), mais le même besoin.
Question : {question}
Format : {{"question": "..."}}"""

PROMPT_UNANSWERABLE = """Les guides de l'ANSSI couvrent : administration sécurisée, Active Directory, Linux,
Windows, authentification et mots de passe, TLS, IPsec, PKI, cloud, conteneurs, virtualisation,
journalisation, supervision, réponse à incident, sauvegarde, rançongiciels.
Écris {n} questions en français, proches de ces thèmes (pour être difficiles), mais auxquelles des guides
techniques de l'ANSSI ne répondent PAS : prix ou comparatif de produits commerciaux, détails juridiques
précis (montants d'amendes), statistiques chiffrées d'actualité, procédures internes d'un éditeur, etc.
Format : {{"questions": ["...", "..."]}}"""


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) > 2 and w not in STOPWORDS}


def section_blocks(doc: ParsedDocument, min_words: int = 60, max_words: int = 450) -> list[list[Element]]:
    """Regroupe les éléments de texte consécutifs d'une même section en blocs de taille raisonnable."""
    blocks, current = [], []
    for el in doc.elements:
        if el.kind in ("table", "footnote"):
            continue
        new_section = current and el.section_path != current[-1].section_path
        too_long = current and sum(len(e.text.split()) for e in current) + len(el.text.split()) > max_words
        if new_section or too_long:
            blocks.append(current)
            current = []
        current.append(el)
    if current:
        blocks.append(current)
    return [b for b in blocks if sum(len(e.text.split()) for e in b) >= min_words]


def block_text(block: list[Element]) -> str:
    return "\n".join(e.text for e in block)


def excerpt_page(block: list[Element], extrait: str) -> int | None:
    """Page de l'élément qui contient l'extrait ; None si l'extrait n'existe pas (inventé par le LLM)."""
    target = normalize(extrait)
    if not target:
        return None
    for el in block:
        if target in normalize(el.text):
            return el.page
    return None


def copies_excerpt(question: str, extrait: str) -> bool:
    q = content_words(question)
    return bool(q) and len(q & content_words(extrait)) / len(q) > 0.7


def ask_single(doc: ParsedDocument, block: list[Element], consigne: str) -> tuple[Generated, int] | None:
    prompt = PROMPT_SINGLE.format(
        titre=doc.titre,
        section=" > ".join(block[0].section_path) or "(début du guide)",
        texte=block_text(block),
        consigne=consigne,
    )
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    try:
        out = complete_json(messages, model=MODEL, schema=Generated)
    except Exception as e:  # une réponse inexploitable ne doit pas arrêter la génération
        print(f"  [rejet] réponse LLM inexploitable : {type(e).__name__}")
        return None
    if not out.possible:
        return None
    page = excerpt_page(block, out.extrait)
    if page is None:
        print(f"  [rejet] extrait introuvable dans le passage : {out.extrait[:60]!r}")
        return None
    if copies_excerpt(out.question, out.extrait):
        print(f"  [rejet] question trop proche de l'extrait : {out.question[:60]!r}")
        return None
    return out, page


def main() -> None:
    global MODEL
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=MODEL, help="modèle LiteLLM utilisé pour générer les questions")
    MODEL = parser.parse_args().model

    rng = random.Random(SEED)
    docs = load_parsed_documents()
    blocks = [(doc, b) for doc in docs for b in section_blocks(doc)]
    tables = [
        (doc, el) for doc in docs for el in doc.elements if el.kind == "table" and el.text.count("\n|") >= 4
    ]
    rng.shuffle(blocks)
    rng.shuffle(tables)
    block_words = [content_words(block_text(b)) for _, b in blocks]  # calculé une fois
    print(f"{len(docs)} guides, {len(blocks)} blocs de texte, {len(tables)} tableaux exploitables")

    questions: list[EvalQuestion] = []
    seen: set[str] = set()

    def keep(q: EvalQuestion) -> None:
        key = normalize(q.question)
        if key not in seen:
            seen.add(key)
            q.id = f"q{len(questions) + 1:04d}"
            questions.append(q)

    def count(kind: str) -> int:
        return sum(q.type == kind for q in questions)

    # 1. Questions factuelles, une par bloc de texte.
    for doc, block in blocks:
        if count("factuelle") >= TARGETS["factuelle"]:
            break
        if result := ask_single(doc, block, "factuelle et précise sur ce passage."):
            out, page = result
            keep(
                EvalQuestion(
                    id="",
                    type="factuelle",
                    question=out.question,
                    reponse_reference=out.reponse,
                    references=[Reference(doc_ref=doc.doc_ref, page=page, extrait=out.extrait)],
                )
            )
    print(f"factuelle : {count('factuelle')}")

    # 2. Questions dont la réponse est dans un tableau.
    for doc, table in tables:
        if count("tableau") >= TARGETS["tableau"]:
            break
        consigne = "dont la réponse demande de lire ce tableau (croiser une ligne et une colonne)."
        if result := ask_single(doc, [table], consigne):
            out, page = result
            keep(
                EvalQuestion(
                    id="",
                    type="tableau",
                    question=out.question,
                    reponse_reference=out.reponse,
                    references=[Reference(doc_ref=doc.doc_ref, page=page, extrait=out.extrait)],
                )
            )
    print(f"tableau : {count('tableau')}")

    # 3. Questions multi-documents : deux blocs de guides différents du même thème, au vocabulaire proche.
    for i, (doc1, block1) in enumerate(blocks):
        if count("multi_documents") >= TARGETS["multi_documents"]:
            break
        candidates = [
            j for j, (d, _) in enumerate(blocks) if d.theme == doc1.theme and d.doc_ref != doc1.doc_ref
        ]
        if not block_words[i] or not candidates:
            continue
        best = max(candidates, key=lambda j: len(block_words[i] & block_words[j]))
        doc2, block2 = blocks[best]
        prompt = PROMPT_MULTI.format(
            titre1=doc1.titre, texte1=block_text(block1), titre2=doc2.titre, texte2=block_text(block2)
        )
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
        try:
            out = complete_json(messages, model=MODEL, schema=GeneratedMulti)
        except Exception as e:
            print(f"  [rejet] réponse LLM inexploitable : {type(e).__name__}")
            continue
        if not out.possible:
            continue
        page1, page2 = excerpt_page(block1, out.extrait_1), excerpt_page(block2, out.extrait_2)
        if page1 is None or page2 is None:
            print("  [rejet] extrait multi-documents introuvable")
            continue
        keep(
            EvalQuestion(
                id="",
                type="multi_documents",
                question=out.question,
                reponse_reference=out.reponse,
                references=[
                    Reference(doc_ref=doc1.doc_ref, page=page1, extrait=out.extrait_1),
                    Reference(doc_ref=doc2.doc_ref, page=page2, extrait=out.extrait_2),
                ],
            )
        )
    print(f"multi_documents : {count('multi_documents')}")

    # 4. Questions vagues : réécriture de questions factuelles, mêmes références.
    factual = [q for q in questions if q.type == "factuelle"]
    for source in rng.sample(factual, min(TARGETS["vague"], len(factual))):
        messages = [{"role": "user", "content": PROMPT_VAGUE.format(question=source.question)}]
        try:
            out = complete_json(messages, model=MODEL, schema=Rewritten)
        except Exception:
            continue
        keep(
            EvalQuestion(
                id="",
                type="vague",
                question=out.question,
                reponse_reference=source.reponse_reference,
                references=source.references,
            )
        )
    print(f"vague : {count('vague')}")

    # 5. Questions sans réponse dans le corpus (à vérifier avec soin à la relecture).
    messages = [{"role": "user", "content": PROMPT_UNANSWERABLE.format(n=TARGETS["sans_reponse"])}]
    for text in complete_json(messages, model=MODEL, schema=Unanswerable).questions:
        keep(
            EvalQuestion(
                id="",
                type="sans_reponse",
                question=text,
                reponse_reference="Le corpus ne contient pas cette information.",
            )
        )
    print(f"sans_reponse : {count('sans_reponse')}")

    save_questions(questions, OUT)
    print(f"\n{len(questions)} candidates écrites dans {OUT}")


if __name__ == "__main__":
    main()
