"""Découpe d'un tableau trop long par groupes de lignes, en répétant l'en-tête.

Règle du guide : un tableau n'est jamais coupé au milieu d'une ligne, et chaque morceau
garde la légende et l'en-tête, sinon ses colonnes n'ont plus de sens.
"""

from collections.abc import Callable


def split_table(text: str, max_tokens: int, count: Callable[[str], int]) -> list[str]:
    """`text` = légende éventuelle + tableau Markdown. Renvoie un ou plusieurs morceaux."""
    if count(text) <= max_tokens:
        return [text]

    lines = text.split("\n")
    first_row = next((i for i, line in enumerate(lines) if line.startswith("|")), None)
    if first_row is None or first_row + 2 > len(lines):
        return [text]  # pas un tableau Markdown reconnaissable : on ne le casse pas

    # préambule (légende) + ligne d'en-tête + ligne de séparation |---|---|
    head = "\n".join(lines[: first_row + 2])
    rows = lines[first_row + 2 :]

    pieces, current = [], []
    for row in rows:
        candidate = "\n".join([head, *current, row])
        if current and count(candidate) > max_tokens:
            pieces.append("\n".join([head, *current]))
            current = []
        current.append(row)
    if current:
        pieces.append("\n".join([head, *current]))
    return pieces
