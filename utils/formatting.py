from __future__ import annotations

import re
import unicodedata


def normalize_text(value: object) -> str:
    """
    Normaliza texto para pesquisa.

    Remove:
    - acentos;
    - diferenças entre maiúsculas e minúsculas;
    - espaços repetidos;
    - parte da pontuação.
    """

    text = "" if value is None else str(value)

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = text.casefold()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def shorten_text(
    value: object,
    limit: int = 220,
) -> str:
    """Reduz textos extensos para exibição nos resultados."""

    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return f"{text[:limit].rstrip()}..."
