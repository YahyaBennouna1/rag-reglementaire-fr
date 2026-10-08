"""Préparation du texte français pour BM25.

« Recommandations », « recommandée » et « RECOMMANDÉ » doivent devenir le même mot,
sinon BM25 les considère comme différents. Mais les codes (« R12 », « ANSSI-PA-022 »,
« 802.1X ») doivent rester intacts : ce sont eux que la recherche par sens rate.
"""

import re
import unicodedata

import snowballstemmer

# Un mot (accents compris), ou un code de lettres et chiffres reliés par - . _ (ex. anssi-pa-022, 802.1x)
TOKEN = re.compile(r"[a-zà-ÿ0-9]+(?:[-._][a-zà-ÿ0-9]+)*")

# Mots très fréquents qui n'aident pas à distinguer les passages.
STOPWORDS = set(
    """
    a afin ai aie aient ainsi alors au aucun aussi autre aux avec avoir c ca car ce ceci cela celle celles
    celui ces cet cette ceux chaque ci comme comment d dans de des deux doit doivent donc dont du elle elles
    en encore entre est et etaient etait etre eu fait faut il ils j je l la le les leur leurs lors lui m ma
    mais me meme mes moins mon n ne ni nos notre nous on ont ou par pas peu peut peuvent plus pour pourquoi
    qu quand que quel quelle quelles quels qui quoi s sa sans se selon ses si sinon soit son sont sous sur
    ta te tel telle tels tes toi ton tous tout toute toutes tres tu un une vers vos votre vous y
    """.split()
)

_stemmer = snowballstemmer.stemmer("french")


def strip_accents(text: str) -> str:
    """« sécurité » -> « securite » : NFD sépare la lettre et l'accent, puis on retire les accents."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def analyze(text: str) -> list[str]:
    """Texte -> liste de termes pour BM25 (minuscules, sans accents, sans mots vides, racinisés)."""
    terms = []
    for token in TOKEN.findall(text.lower()):
        if strip_accents(token) in STOPWORDS:
            continue
        if token.isalpha():
            # On racinise seulement les vrais mots ; les codes restent intacts.
            # Le raciniseur a besoin des accents : on les retire APRÈS (« recommandée » -> « recommand »).
            token = _stemmer.stemWord(token)
        terms.append(strip_accents(token))
    return terms
