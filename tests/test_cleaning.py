from ragfr.ingestion.cleaning import clean_text, fix_hyphenation, is_noise


def test_cesure_recollee():
    assert fix_hyphenation("des applica- tions") == "des applications"
    assert fix_hyphenation("des applica-\ntions") == "des applications"


def test_mots_composes_et_listes_conserves():
    assert fix_hyphenation("un porte-monnaie") == "un porte-monnaie"
    assert fix_hyphenation("privilèges - création") == "privilèges - création"


def test_ligatures_remplacees():
    assert clean_text("diﬀuser la ﬁgure") == "diffuser la figure"


def test_glyphes_de_figure():
    assert clean_text("F 1.1 - Architecture Docker", "caption") == ("Figure 1.1 - Architecture Docker")


def test_puce_wingdings_retiree_des_listes():
    assert clean_text("n un fichier /etc/hosts", "list_item") == "un fichier /etc/hosts"
    # Hors liste, un « n » en tête est un vrai mot : on n'y touche pas.
    assert clean_text("n est un entier", "paragraph") == "n est un entier"


def test_points_decoratifs_retires():
    assert clean_text(". . . Chaque conteneur doit") == "Chaque conteneur doit"


def test_bruit_detecte():
    assert is_noise(".")
    assert is_noise(" . . ")
    assert is_noise("R2")
    assert is_noise("R12 - -")
    assert is_noise("R5 +")
    assert not is_noise("R2 impose un bastion")
    assert not is_noise("2.1")
