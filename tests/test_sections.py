from ragfr.ingestion.models import Element
from ragfr.ingestion.sections import assign_sections, heading_depth


def h(text: str) -> Element:
    return Element(kind="heading", text=text, page=1, page_end=1)


def p(text: str) -> Element:
    return Element(kind="paragraph", text=text, page=1, page_end=1)


def test_profondeur_des_titres():
    assert heading_depth("2 Recommandations") == 1
    assert heading_depth("2.1 Cloisonnement") == 2
    assert heading_depth("4.2.3 Un poste") == 3
    assert heading_depth("A Correspondance avec le CIS") == 1
    assert heading_depth("Isoler les systèmes de fichiers") is None


def test_chemin_de_section():
    out = assign_sections(
        [
            h("2 Recommandations"),
            h("2.1 Cloisonnement"),
            h("Isoler les systèmes de fichiers"),
            p("texte A"),
            h("2.2 Ressources"),
            p("texte B"),
            h("3 Annexe"),
            p("texte C"),
        ]
    )
    paths = {e.text: e.section_path for e in out if e.kind == "paragraph"}
    assert paths["texte A"] == ["2 Recommandations", "2.1 Cloisonnement", "Isoler les systèmes de fichiers"]
    assert paths["texte B"] == ["2 Recommandations", "2.2 Ressources"]
    assert paths["texte C"] == ["3 Annexe"]


def test_numero_isole_fusionne_avec_le_titre_suivant():
    out = assign_sections([h("2"), h("Recommandations"), p("texte")])
    assert [e.text for e in out] == ["2 Recommandations", "texte"]
    assert out[1].section_path == ["2 Recommandations"]
