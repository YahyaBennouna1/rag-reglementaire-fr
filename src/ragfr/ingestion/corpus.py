import csv
from pathlib import Path

from ragfr.ingestion.models import CorpusEntry


def load_corpus(path: str | Path) -> list[CorpusEntry]:
    with open(path, encoding="utf-8", newline="") as f:
        return [CorpusEntry.model_validate(row) for row in csv.DictReader(f)]
