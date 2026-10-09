"""Masquer les données personnelles d'une question avant de l'envoyer au LLM (RGPD).

Presidio (Microsoft) trouve les données personnelles : des expressions régulières pour les formats
connus (e-mail, téléphone, IBAN, carte bancaire, adresse IP) et le modèle français de spaCy pour
les noms de personnes. Chaque donnée trouvée est remplacée par son type : « [PERSONNE] », « [EMAIL] »
(entre crochets et pas entre chevrons : un marqueur ne doit pas ressembler à une balise du prompt).

On ne masque PAS les organisations ni les lieux : « ANSSI », « Microsoft », « Active Directory »
sont justement ce qu'on cherche dans les guides.
"""

from functools import cache

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer,
    EmailRecognizer,
    IbanRecognizer,
    IpRecognizer,
    PhoneRecognizer,
    SpacyRecognizer,
)
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

LANGUAGE = "fr"
# Type Presidio -> marqueur écrit à la place de la donnée.
LABELS = {
    "PERSON": "[PERSONNE]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "PHONE_NUMBER": "[TELEPHONE]",
    "IBAN_CODE": "[IBAN]",
    "CREDIT_CARD": "[CARTE_BANCAIRE]",
    "IP_ADDRESS": "[ADRESSE_IP]",
}

# Mots jamais masqués : le modèle français prend « Réponds », en tête de phrase avec une majuscule,
# pour un prénom (mesuré, leçon 23). Presidio appelle ça une « allow list ».
ALLOW_LIST = ["Réponds", "Répondez", "Réponse"]


@cache
def get_analyzer() -> AnalyzerEngine:
    """L'analyseur Presidio en français, créé une seule fois (le modèle spaCy met 2 s à charger)."""
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": LANGUAGE, "model_name": "fr_core_news_md"}],
            # Le modèle français étiquette les personnes « PER » ; Presidio attend « PERSON ».
            "ner_model_configuration": {"model_to_presidio_entity_mapping": {"PER": "PERSON"}},
        }
    ).create_engine()
    registry = RecognizerRegistry(supported_languages=[LANGUAGE])
    for recognizer in [
        SpacyRecognizer(supported_language=LANGUAGE, supported_entities=["PERSON"]),
        EmailRecognizer(supported_language=LANGUAGE),
        PhoneRecognizer(supported_language=LANGUAGE, supported_regions=("FR",)),
        IbanRecognizer(supported_language=LANGUAGE),
        CreditCardRecognizer(supported_language=LANGUAGE),
        IpRecognizer(supported_language=LANGUAGE),
    ]:
        registry.add_recognizer(recognizer)
    return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=[LANGUAGE])


def mask_pii(text: str) -> tuple[str, list[str]]:
    """Renvoie (texte masqué, types trouvés), par exemple ("Je suis [PERSONNE]…", ["PERSON"])."""
    analyzer = get_analyzer()
    findings = analyzer.analyze(text=text, language=LANGUAGE, entities=list(LABELS), allow_list=ALLOW_LIST)
    if not findings:
        return text, []
    operators = {kind: OperatorConfig("replace", {"new_value": label}) for kind, label in LABELS.items()}
    masked = AnonymizerEngine().anonymize(text=text, analyzer_results=findings, operators=operators)
    return masked.text, sorted({f.entity_type for f in findings})
