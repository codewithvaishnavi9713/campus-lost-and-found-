"""Individual, explainable scoring rules for item matching."""

import re
from datetime import date, datetime
from difflib import SequenceMatcher

from app.ai.text_similarity import calculate_text_similarity


COLOR_GROUPS = {
    "black": {"black", "dark", "charcoal"},
    "white": {"white", "cream", "ivory"},
    "blue": {"blue", "navy", "cyan", "teal"},
    "red": {"red", "maroon", "burgundy", "pink"},
    "green": {"green", "olive", "lime"},
    "yellow": {"yellow", "gold", "golden"},
    "brown": {"brown", "tan", "beige", "khaki"},
    "purple": {"purple", "violet", "lavender"},
    "gray": {"gray", "grey", "silver"},
    "orange": {"orange"},
}


def _normalise(value):
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").lower()))


def category_score(category_a, category_b):
    return 20 if _normalise(category_a) and _normalise(category_a) == _normalise(category_b) else 0


def color_score(color_a, color_b):
    first, second = _normalise(color_a), _normalise(color_b)
    if not first or not second:
        return 0
    if first == second:
        return 10
    for group in COLOR_GROUPS.values():
        if any(word in group for word in first.split()) and any(word in group for word in second.split()):
            return 8
    return 0


def location_score(location_a, location_b):
    first, second = _normalise(location_a), _normalise(location_b)
    if not first or not second:
        return 0
    if first == second:
        return 15
    first_words, second_words = set(first.split()), set(second.split())
    overlap = len(first_words & second_words) / len(first_words | second_words)
    similarity = SequenceMatcher(None, first, second).ratio()
    if overlap >= 0.5 or similarity >= 0.8:
        return 10
    if overlap > 0 or similarity >= 0.55:
        return 5
    return 0


def date_score(date_a, date_b):
    if not isinstance(date_a, (date, datetime)) or not isinstance(date_b, (date, datetime)):
        return 0
    days_apart = abs((date_a.date() if isinstance(date_a, datetime) else date_a) -
                     (date_b.date() if isinstance(date_b, datetime) else date_b)).days
    if days_apart == 0:
        return 10
    if days_apart == 1:
        return 8
    if days_apart == 2:
        return 6
    if days_apart == 3:
        return 4
    if days_apart <= 7:
        return 2
    return 0


def text_score(title_a, description_a, title_b, description_b):
    first = f"{title_a or ''} {description_a or ''}".strip()
    second = f"{title_b or ''} {description_b or ''}".strip()
    return round(calculate_text_similarity(first, second) * 45, 2)
