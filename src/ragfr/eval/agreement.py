"""Accord entre deux juges (un humain et un LLM, par exemple), au-delà du hasard."""


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    """Kappa de Cohen pour deux listes de verdicts oui/non, dans le même ordre.

    kappa = (accord observé - accord dû au hasard) / (1 - accord dû au hasard)
    1 = accord parfait ; 0 = pas mieux que le hasard ; < 0 = pire que le hasard.
    """
    if len(a) != len(b) or not a:
        raise ValueError("il faut deux listes non vides de même longueur")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    yes_a, yes_b = sum(a) / n, sum(b) / n
    chance = yes_a * yes_b + (1 - yes_a) * (1 - yes_b)
    if chance == 1:  # les deux juges disent toujours la même chose : accord parfait mais non informatif
        return 1.0
    return (observed - chance) / (1 - chance)
