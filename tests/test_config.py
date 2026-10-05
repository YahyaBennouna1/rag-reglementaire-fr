import pytest
from pydantic import ValidationError

from ragfr.config import Config, load_config


def test_baseline_se_charge():
    cfg = load_config("configs/baseline.yaml")
    assert cfg.name == "baseline"
    assert cfg.retrieval.mode == "dense"
    assert cfg.retrieval.reranker is False


def test_faute_de_frappe_refusee():
    with pytest.raises(ValidationError):
        Config.model_validate({"name": "x", "retrieval": {"rerankr": True}})