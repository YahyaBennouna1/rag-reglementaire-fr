"""Interface web pour les utilisateurs : poser une question, lire la réponse et ses sources.

    uv run streamlit run src/ragfr/ui/streamlit_app.py
    puis ouvrir http://localhost:8501

Elle appelle directement answer_question (le même code que l'API, le serveur MCP et l'évaluation).
Qdrant en mode local n'accepte qu'un programme à la fois : arrêter l'API ou une évaluation avant.
"""

import datetime
import os
import time

import streamlit as st

from ragfr.generation import Answer
from ragfr.models import Passage
from ragfr.pipeline import answer_question, production_config

# Démo publique : chaque question consomme le quota d'API du propriétaire. Limite par visiteur
# (par session du navigateur) ; 0 = pas de limite, le réglage par défaut en local.
MAX_QUESTIONS = int(os.environ.get("RAGFR_MAX_QUESTIONS", "0"))
# Recharger la page remet la limite par session à zéro : on ajoute une limite par jour, pour tous.
MAX_PER_DAY = int(os.environ.get("RAGFR_MAX_QUESTIONS_PER_DAY", "0"))


@st.cache_resource
def daily_counter() -> dict:
    """Un seul dictionnaire pour tout le programme (donc partagé par tous les visiteurs)."""
    return {"day": None, "count": 0}


def day_limit_reached() -> bool:
    counter = daily_counter()
    if counter["day"] != datetime.date.today():
        counter["day"], counter["count"] = datetime.date.today(), 0  # nouveau jour, compteur à zéro
    return MAX_PER_DAY > 0 and counter["count"] >= MAX_PER_DAY


EXAMPLES = [
    "Faut-il désactiver TLS 1.0 ?",
    "Combien de temps faut-il conserver les journaux d'événements ?",
    "Quelle longueur minimale recommander pour un mot de passe ?",
    "Comment sécuriser le démon Docker ?",
]


def show_answer(answer: Answer, duration: float) -> None:
    if answer.blocked:
        st.error(answer.text)  # refus des garde-fous : ni recherche ni sources à montrer
        return
    if answer.abstained:
        # L'abstention est un résultat normal : le système préfère ne rien dire plutôt qu'inventer.
        st.warning(answer.text)
    else:
        for sentence in answer.sentences:
            sources = ", ".join(sentence.sources)
            st.markdown(f"{sentence.phrase} **[{sources}]**" if sources else sentence.phrase)
    st.caption(f"Réponse en {duration:.1f} s")

    # Les passages cités par la réponse d'abord (ouverts), puis les autres passages consultés (repliés).
    cited = {label for sentence in answer.sentences for label in sentence.sources}
    labelled = [(f"P{i}", p) for i, p in enumerate(answer.passages, start=1)]
    cited_passages = [(label, p) for label, p in labelled if label in cited]
    other_passages = [(label, p) for label, p in labelled if label not in cited]

    if cited_passages:
        st.subheader("Sources citées")
        for label, p in cited_passages:
            show_passage(label, p, expanded=True)
    if other_passages:
        # En cas d'abstention, aucun passage n'est cité : on montre ce qui s'en approchait le plus.
        if answer.abstained:
            st.subheader("Passages les plus proches (aucun ne répond)")
        else:
            st.subheader("Autres passages consultés")
        for label, p in other_passages:
            show_passage(label, p, expanded=False)


def show_passage(label: str, p: Passage, expanded: bool) -> None:
    pages = f"p. {p.page}" if p.page == p.page_end else f"p. {p.page}-{p.page_end}"
    with st.expander(f"{label} — {p.titre}, {pages}", expanded=expanded):
        if p.section:
            st.caption(p.section)
        st.write(p.text)


st.set_page_config(page_title="RAG ANSSI", page_icon="🛡️")
st.title("🛡️ Questions sur les guides de l'ANSSI")
st.write(
    "Posez une question sur les 45 guides de cybersécurité de l'ANSSI. Chaque phrase de la réponse "
    "renvoie à ses sources ; si les guides ne contiennent pas la réponse, l'assistant le dit."
)

example = st.selectbox("Exemples", EXAMPLES, index=None, placeholder="Choisir un exemple…")
question = st.text_input("Votre question", value=example or "", max_chars=1000)

asked = st.session_state.get("asked", 0)
limit_reached = (MAX_QUESTIONS > 0 and asked >= MAX_QUESTIONS) or day_limit_reached()
if limit_reached:
    st.info("Limite de la démo atteinte pour le moment. Le code complet est sur GitHub.")

if st.button("Demander", type="primary", disabled=len(question.strip()) < 3 or limit_reached):
    st.session_state["asked"] = asked + 1
    daily_counter()["count"] += 1
    with st.spinner("Recherche dans les guides et rédaction de la réponse…"):
        start = time.perf_counter()
        answer = answer_question(production_config(), question.strip())
        duration = time.perf_counter() - start
    show_answer(answer, duration)

st.divider()
st.caption(
    "Sources : guides publiés par l'ANSSI, réutilisés sous Licence Ouverte 2.0. "
    "Ce projet n'est ni affilié à l'ANSSI ni approuvé par elle. Vérifiez toujours dans le guide cité."
)
