"""The Design Mechanism's house terms, applied to text that comes from the data.

The chapters are written in house style by hand and are linted for it
(tests/test_guide.py). Text pulled from the campaign files -- a sheet's
description, a map note -- was written for the engine and says GM, PC and NPC,
so it is normalised on the way into the guide rather than rewritten at source.
"""
import re

_RULES = [
    (r"\bGMs\b", "Games Masters"),
    (r"\bGM\b", "Games Master"),
    (r"\bGame Master\b", "Games Master"),
    (r"\bNPCs\b", "Non-Player Characters"),
    (r"\bNPC\b", "Non-Player Character"),
    (r"\bPCs\b", "characters"),
    (r"\bPC\b", "character"),
    (r"\betc\.(?=\s|$)", "and so on."),
    (r"\betc\b\.?", "and so on"),
    (r"(\d)D(\d)", r"\1d\2"),
    (r" -- ", " — "),
    (r"(?<![-|])--(?![-|])", "—"),
]


def house(text):
    for pat, rep in _RULES:
        text = re.sub(pat, rep, text)
    return text


BANNED = [r"\bGMs?\b", r"\bNPCs?\b", r"\bPCs?\b", r"\betc\b", r"\bGame Master\b", r"\d+D\d+"]


def violations(text):
    """House-style breaches in hand-written prose. Ignores code and directives."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "", text)
    out = []
    for pat in BANNED:
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            out.append((line, m.group(0)))
    return out
