from ragfr.citations import verify as verify_module
from ragfr.citations.verify import Judgement, verify_answer
from ragfr.generation import Answer, Sentence
from ragfr.models import Passage


def passage(pid: str, text: str) -> Passage:
    return Passage(id=pid, doc_ref="tls", titre="TLS", page=3, page_end=3, section="", text=text)


PASSAGES = [passage("tls:1", "TLS 1.0 doit être désactivé."), passage("tls:2", "TLS 1.3 est recommandé.")]


def answer_with(sentences: list[Sentence]) -> Answer:
    return Answer(text="", sentences=sentences, citations=[], abstained=False, passages=PASSAGES)


def fake_judge(verdicts: dict[str, str]):
    """Faux juge : le verdict dépend de la phrase vérifiée."""

    def complete_json(messages, model, schema, **kwargs):
        prompt = messages[0]["content"]
        for phrase, verdict in verdicts.items():
            if phrase in prompt:
                return Judgement(verdict=verdict)
        raise AssertionError("phrase inconnue")

    return complete_json


def test_phrase_non_soutenue_retiree(monkeypatch):
    sentences = [
        Sentence(phrase="Il faut désactiver TLS 1.0.", sources=["P1"]),
        Sentence(phrase="TLS 1.3 est recommandé.", sources=["P2"]),
        Sentence(phrase="SSL 3.0 reste acceptable.", sources=["P1"]),
    ]
    verdicts = {s.phrase: v for s, v in zip(sentences, ["soutenu", "soutenu", "non_soutenu"], strict=True)}
    monkeypatch.setattr(verify_module, "complete_json", fake_judge(verdicts))

    cleaned, reliable = verify_answer(answer_with(sentences), model="juge")

    assert [s.phrase for s in cleaned.sentences] == ["Il faut désactiver TLS 1.0.", "TLS 1.3 est recommandé."]
    assert reliable  # 1 phrase retirée sur 3 : pas plus d'un tiers
    assert [c.verdict for c in cleaned.citations] == ["soutenu", "soutenu", "non_soutenu"]


def test_trop_de_phrases_retirees_reponse_non_fiable(monkeypatch):
    sentences = [
        Sentence(phrase="Phrase A.", sources=["P1"]),
        Sentence(phrase="Phrase B.", sources=["P2"]),
    ]
    monkeypatch.setattr(
        verify_module, "complete_json", fake_judge({"Phrase A.": "soutenu", "Phrase B.": "non_soutenu"})
    )
    _, reliable = verify_answer(answer_with(sentences), model="juge")
    assert not reliable  # 1 sur 2 = la moitié, plus d'un tiers


def test_source_inventee_non_soutenue(monkeypatch):
    monkeypatch.setattr(verify_module, "complete_json", fake_judge({}))  # le juge ne doit pas être appelé
    cleaned, reliable = verify_answer(answer_with([Sentence(phrase="X.", sources=["P9"])]), model="juge")
    assert cleaned.sentences == [] and not reliable
