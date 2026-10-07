from pathlib import Path

import pytest
from pydantic import ValidationError

from ragfr.config import Config, load_config

CONFIGS = Path(__file__).parent.parent / "configs"


def test_baseline_se_charge():
    cfg = load_config(CONFIGS / "baseline.yaml")
    assert cfg.name == "baseline"
    assert cfg.retrieval.mode == "dense"
    assert cfg.retrieval.reranker is False


def test_faute_de_frappe_refusee():
    with pytest.raises(ValidationError):
        Config.model_validate({"name": "x", "retrieval": {"rerankr": True}})


def test_rerank_candidates_trop_petit_refuse():
    with pytest.raises(ValidationError):
        Config.model_validate(
            {"name": "x", "retrieval": {"top_k": 10, "rerank_candidates": 5}}
        )

