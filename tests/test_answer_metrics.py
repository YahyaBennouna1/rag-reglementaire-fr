"""Le juge des réponses ne reçoit que les passages cités, avec leurs numéros d'origine."""

from ragfr.eval import answer_metrics
from ragfr.eval.answer_metrics import AnswerJudgement, judge_answer
from ragfr.eval.dataset import EvalQuestion
from ragfr.generation import Answer, Citation
from ragfr.models import Passage


def passage(n: int) -> Passage:
    return Passage(
        id=f"doc:{n}", doc_ref="doc", titre="Guide", page=n, page_end=n, section="", text=f"texte {n}"
    )


def test_le_juge_ne_voit_que_les_passages_cites(monkeypatch):
    prompts = []

    def fake_complete_json(messages, model, schema, **kwargs):
        prompts.append(messages[0]["content"])
        return AnswerJudgement(fidele=True, exacte=True, pertinente=True)

    monkeypatch.setattr(answer_metrics, "complete_json", fake_complete_json)
    passages = [passage(n) for n in range(1, 6)]
    citation = Citation(phrase="Une phrase.", passage_id="doc:3", doc_ref="doc", page=3)
    answer = Answer(
        text="Une phrase. [P3]", sentences=[], citations=[citation], abstained=False, passages=passages
    )
    question = EvalQuestion(id="q1", type="factuelle", question="Question ?", reponse_reference="Réponse.")

    judge_answer(question, answer, "faux-juge")

    assert 'id="P3"' in prompts[0]  # le numéro d'origine, celui que cite la réponse
    assert "texte 3" in prompts[0]
    assert "texte 1" not in prompts[0] and 'id="P1"' not in prompts[0]  # les passages non cités sont absents
