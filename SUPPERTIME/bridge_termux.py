"""
Termux bridge - only guess_participants function (no Telegram)
"""
import re

NAME_MARKERS = {
    "Judas": re.compile(r"\bJudas\b|\bI,\s*Judas\b", re.I),
    "Yeshua": re.compile(r"\bYeshua\b|\bYeshu\b|\bTeacher\b", re.I),
    "Peter": re.compile(r"\bPeter\b|\bwig\b|\bdress\b", re.I),
    "Mary": re.compile(r"\bMary\b", re.I),
    "Yakov": re.compile(r"\bYakov\b|\bJacob\b", re.I),
    "Jan": re.compile(r"\bJan\b", re.I),
    "Thomas": re.compile(r"\bThomas\b", re.I),
    "Andrew": re.compile(r"\bAndrew\b", re.I),
    "Leo": re.compile(r"\bLeo\b|\bMadonna\b|\bsketch\b", re.I),
    "Theodore": re.compile(r"\bTheodore\b|\bAllow me-s\b", re.I),
    "Dubrovsky": re.compile(r"\bDubrovsky\b|\bAlexey\b", re.I),
}
ALL_CHAR_NAMES = list(NAME_MARKERS.keys())


def detect_names(text: str) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for name, rx in NAME_MARKERS.items():
        if rx.search(text) and name not in found:
            found.append(name)
    return found


def guess_participants(chapter_text: str):
    header_match = re.match(r"\s*Participants:\s*(.*)", chapter_text or "", re.IGNORECASE)
    names: list[str] = []
    if header_match:
        for part in header_match.group(1).split(","):
            part = part.strip()
            if part and part in ALL_CHAR_NAMES:
                names.append(part)
    if not names:
        names = detect_names(chapter_text)
    return names if names else ALL_CHAR_NAMES[:3]

