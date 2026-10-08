import pytest

from ragfr.eval.agreement import cohen_kappa


def test_kappa_calcule_a_la_main():
    # L'exemple de la leçon 15 : 38 oui/oui, 4 oui/non, 2 non/oui, 6 non/non -> kappa ≈ 0,59
    a = [True] * 38 + [True] * 4 + [False] * 2 + [False] * 6
    b = [True] * 38 + [False] * 4 + [True] * 2 + [False] * 6
    assert cohen_kappa(a, b) == pytest.approx(0.176 / 0.296, abs=1e-3)


def test_juge_qui_dit_toujours_oui():
    humain = [True] * 9 + [False]
    paresseux = [True] * 10
    # 90 % d'accord, mais le juge n'apporte aucune information : kappa = 0
    assert cohen_kappa(humain, paresseux) == pytest.approx(0.0)


def test_accord_parfait():
    assert cohen_kappa([True, False, True], [True, False, True]) == 1.0
