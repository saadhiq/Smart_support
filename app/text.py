"""Text normalisation shared by training and prediction."""

import re

PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}")
DIGITS_RE = re.compile(r"\d+")
APOSTROPHE_RE = re.compile(r"['’]")
NON_WORD_RE = re.compile(r"[^a-z0-9_ ]+")
ENT = "ENT"


def normalise(text: str) -> str:
    """Lowercase, map {{...}} placeholders and digit runs to ENT, drop punctuation."""
    text = text.lower()
    text = PLACEHOLDER_RE.sub(" _ent_ ", text)
    text = DIGITS_RE.sub(" _ent_ ", text)
    text = APOSTROPHE_RE.sub("", text)
    text = NON_WORD_RE.sub(" ", text)
    return " ".join(text.split()).replace("_ent_", ENT)
