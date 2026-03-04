"""
Utilitaires de comparaison de texte pour le mode réponse libre.

Fonctions utilisées par GameService.check_answer() et les tests.
"""

import re
import unicodedata
from typing import Tuple


def normalize_text(text: str) -> str:
    """Normalize text for fuzzy comparison in text answer mode."""
    text = text.lower().strip()
    # Remove accents
    text = "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    # Remove common prefixes/articles
    for prefix in ("the ", "le ", "la ", "les ", "l'", "un ", "une ", "des "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    # Remove punctuation
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _levenshtein_similarity(g: str, c: str) -> float:
    """Compute Levenshtein-based similarity between two normalized strings."""
    if not g or not c:
        return 0.0
    max_len = max(len(g), len(c))
    if max_len > 50:
        # For very long strings, fall back to character-based only
        common = sum(1 for a, b in zip(g, c) if a == b)
        return common / max_len
    dp = list(range(len(c) + 1))
    for i in range(1, len(g) + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, len(c) + 1):
            temp = dp[j]
            if g[i - 1] == c[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    edit_dist = dp[len(c)]
    return 1.0 - (edit_dist / max_len)


def fuzzy_match(
    given: str, correct: str, threshold: float = 0.65
) -> Tuple[bool, float]:
    """Compare two strings with fuzzy matching for text answer mode.

    Returns (is_match, similarity_factor) where similarity_factor is 0.0-1.0.
    Uses multiple strategies: exact match, containment, word-set overlap,
    and Levenshtein edit-distance.  Threshold default is intentionally
    tolerant (0.65) so that minor typos are accepted.
    """
    g = normalize_text(given)
    c = normalize_text(correct)

    if not g or not c:
        return False, 0.0

    # 1. Exact match after normalisation
    if g == c:
        return True, 1.0

    # 2. Containment check (one is a substring of the other)
    if g in c or c in g:
        ratio = min(len(g), len(c)) / max(len(g), len(c))
        if ratio >= 0.4:  # accept partial matches (e.g. just the artist name)
            return True, max(ratio, 0.75)

    # 3. Word-set overlap (order-independent)
    g_words = set(g.split())
    c_words = set(c.split())
    if g_words and c_words:
        common_words = g_words & c_words
        union_words = g_words | c_words
        word_sim = len(common_words) / len(union_words)  # Jaccard
        if word_sim >= threshold:
            return True, word_sim

    # 4. Levenshtein edit-distance similarity
    edit_sim = _levenshtein_similarity(g, c)

    # 5. Character-based positional similarity
    max_len = max(len(g), len(c))
    common = sum(1 for a, b in zip(g, c) if a == b)
    char_sim = common / max_len

    similarity = max(edit_sim, char_sim)

    if similarity >= threshold:
        return True, similarity

    return False, similarity
