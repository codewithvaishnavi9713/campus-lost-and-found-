"""TF-IDF based text similarity helpers."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_text_similarity(text_a, text_b):
    """Return a cosine similarity in the inclusive range 0..1.

    Empty strings and text containing only stop words have no useful signal, so
    they intentionally produce zero instead of raising a vectorizer error.
    """
    text_a = (text_a or "").strip()
    text_b = (text_b or "").strip()
    if not text_a or not text_b:
        return 0.0

    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([text_a, text_b])
    except ValueError:
        return 0.0
    return max(0.0, min(1.0, float(cosine_similarity(matrix[0], matrix[1])[0][0])))
