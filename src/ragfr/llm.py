"""Appels aux LLM : un seul point d'entrée pour tout le projet.

- LiteLLM : la même fonction pour Gemini, Groq, Mistral, Ollama… Le modèle se change dans le YAML.
- Cache disque : un prompt déjà envoyé n'est jamais repayé (clé = empreinte SHA-256 de la requête).
- Reprises avec attente exponentielle : les offres gratuites renvoient souvent 429 (trop de requêtes).
- Sortie JSON validée par Pydantic pour les tâches structurées (routeur, juge…).
"""

import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import litellm
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "cache" / "llm"

load_dotenv(ROOT / ".env")
litellm.suppress_debug_info = True

# Erreurs passagères : on réessaie. Les autres (clé invalide, modèle inconnu) remontent tout de suite.
RETRYABLE = (
    litellm.RateLimitError,
    litellm.Timeout,
    litellm.APIConnectionError,
    litellm.ServiceUnavailableError,
    litellm.InternalServerError,
)


def is_quota_exhausted(error: Exception) -> bool:
    """Vrai pour un quota qui ne se libère pas en quelques secondes : réessayer ne servirait à rien.

    - quota JOURNALIER épuisé (Groq : « tokens per day (TPD) ») ;
    - plus de CRÉDITS sur le compte (OpenAI : « insufficient_quota », « no credits remaining »).
    Une limite par MINUTE, elle, se libère vite : on réessaie.
    """
    message = str(error).lower()
    markers = ("per day", "(tpd)", "(rpd)", "insufficient_quota", "no credits", "exceeded your current quota")
    return any(marker in message for marker in markers)


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cached: bool


# Tokens consommés par modèle, réponses en cache comprises : on mesure le coût du système
# tel qu'il tournerait en production, pas seulement ce qu'on a payé pendant le développement.
usage: dict[str, dict[str, int]] = {}


def _track(result: LLMResponse) -> LLMResponse:
    counts = usage.setdefault(result.model, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
    counts["calls"] += 1
    counts["input_tokens"] += result.input_tokens
    counts["output_tokens"] += result.output_tokens
    return result


def reset_usage() -> None:
    usage.clear()


def estimated_cost_usd() -> tuple[float, list[str]]:
    """Coût au tarif public payant (prix connus de LiteLLM). Renvoie aussi les modèles sans prix connu."""
    total, unknown = 0.0, []
    for model, counts in usage.items():
        try:
            cost_in, cost_out = litellm.cost_per_token(
                model=model,
                prompt_tokens=counts["input_tokens"],
                completion_tokens=counts["output_tokens"],
            )
            total += cost_in + cost_out
        except Exception:  # modèle trop récent pour la table de prix de LiteLLM
            unknown.append(model)
    return total, unknown


def _cache_key(payload: dict) -> str:
    # sort_keys : le même contenu donne toujours la même chaîne, donc la même clé.
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _cache_path(key: str) -> Path:
    # Sous-dossier par préfixe : évite d'avoir des dizaines de milliers de fichiers dans un dossier.
    return CACHE_DIR / key[:2] / f"{key}.json"


def complete(
    messages: list[dict],
    model: str,
    temperature: float = 0.0,
    max_tokens: int | None = None,
    use_cache: bool = True,
    max_retries: int = 6,
) -> LLMResponse:
    """Envoie une conversation à un LLM et renvoie sa réponse (depuis le cache si possible)."""
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    path = _cache_path(_cache_key(payload))
    if use_cache and path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        return _track(
            LLMResponse(
                text=saved["text"],
                model=saved["model"],
                input_tokens=saved["input_tokens"],
                output_tokens=saved["output_tokens"],
                latency_s=0.0,
                cached=True,
            )
        )

    start = time.perf_counter()
    for attempt in range(max_retries + 1):
        try:
            response = litellm.completion(**payload, timeout=120)
            break
        except RETRYABLE as error:
            if attempt == max_retries or is_quota_exhausted(error):
                raise
            # Attente exponentielle avec gigue : 2 s, 4 s, 8 s… (+ hasard pour désynchroniser les clients)
            time.sleep(min(2 ** (attempt + 1), 60) + random.uniform(0, 1))

    result = LLMResponse(
        text=response.choices[0].message.content or "",
        model=model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        latency_s=time.perf_counter() - start,
        cached=False,
    )
    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        saved = {
            "text": result.text,
            "model": result.model,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        }
        path.write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
    return _track(result)


def _extract_json(text: str) -> str:
    """Retire les éventuelles balises ```json … ``` que certains modèles ajoutent."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def complete_json[T: BaseModel](messages: list[dict], model: str, schema: type[T], **kwargs) -> T:
    """Comme complete(), mais la réponse doit être un JSON conforme au schéma Pydantic.

    En cas de JSON invalide, on renvoie l'erreur au modèle une fois pour qu'il se corrige.
    """
    response = complete(messages, model, **kwargs)
    try:
        return schema.model_validate_json(_extract_json(response.text))
    except ValidationError as e:
        retry = messages + [
            {"role": "assistant", "content": response.text},
            {"role": "user", "content": f"JSON invalide : {e}. Renvoie uniquement un JSON valide."},
        ]
        return schema.model_validate_json(_extract_json(complete(retry, model, **kwargs).text))
