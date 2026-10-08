"""Le jeu de questions d'évaluation (data/eval/questions.jsonl).

Les passages de référence sont stockés comme (doc_ref, page, extrait exact) et non comme des
identifiants de chunks : sinon le jeu dépendrait d'une méthode de chunking.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

QuestionType = Literal["factuelle", "tableau", "multi_documents", "vague", "sans_reponse"]
Status = Literal["genere", "valide", "corrige", "rejete"]
Split = Literal["dev", "test"]

# Nombre de questions du jeu final, par type (guide du projet).
QUOTAS = {"factuelle": 80, "tableau": 40, "multi_documents": 40, "vague": 20, "sans_reponse": 20}


class Reference(BaseModel):
    doc_ref: str
    page: int
    extrait: str  # copié mot pour mot du guide


class EvalQuestion(BaseModel):
    id: str
    type: QuestionType
    question: str
    reponse_reference: str
    references: list[Reference] = Field(default_factory=list)  # vide pour "sans_reponse"
    statut: Status = "genere"
    split: Split | None = None


def load_questions(path: str | Path) -> list[EvalQuestion]:
    with open(path, encoding="utf-8") as f:
        return [EvalQuestion.model_validate_json(line) for line in f if line.strip()]


def save_questions(questions: list[EvalQuestion], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for q in questions:
            f.write(json.dumps(q.model_dump(), ensure_ascii=False) + "\n")
