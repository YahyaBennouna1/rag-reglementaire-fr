"""Compter et découper en tokens avec le tokenizer du modèle d'embedding (bge-m3).

On compte avec le tokenizer du modèle qui lira les chunks : « 512 tokens » n'a de sens
que pour un tokenizer donné.
"""

from functools import lru_cache

from transformers import AutoTokenizer, PreTrainedTokenizerFast

TOKENIZER_NAME = "BAAI/bge-m3"


@lru_cache(maxsize=1)
def get_tokenizer() -> PreTrainedTokenizerFast:
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    # On tokenise des documents entiers pour les découper : pas d'avertissement de longueur.
    tokenizer.model_max_length = 10_000_000
    return tokenizer


def count_tokens(text: str) -> int:
    return len(get_tokenizer().encode(text, add_special_tokens=False))
