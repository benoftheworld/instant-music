"""
Lyrics service — fetches song lyrics from LRCLib and lyrics.ovh (free, no key).
Used by the 'paroles' game mode (fill-in-the-blank) and 'karaoke' mode (synced lyrics).
"""

import logging
import random
import re
import hashlib
from typing import Optional, Tuple, List, Dict

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Words that are too short or common to be interesting blanks
BORING_WORDS = {
    "i",
    "a",
    "the",
    "an",
    "is",
    "it",
    "in",
    "on",
    "to",
    "of",
    "and",
    "or",
    "at",
    "my",
    "me",
    "we",
    "he",
    "be",
    "do",
    "so",
    "no",
    "oh",
    "je",
    "tu",
    "il",
    "le",
    "la",
    "de",
    "et",
    "un",
    "ne",
    "se",
    "ce",
    "en",
    "du",
    "au",
    "on",
    "ma",
    "sa",
    "si",
    "ou",
    "ni",
    "que",
    "qui",
    "les",
    "des",
    "une",
    "pas",
    "son",
    "que",
    "par",
    "sur",
    "mais",
    "pour",
    "the",
    "and",
    "you",
    "for",
    "are",
    "but",
    "not",
    "all",
    "can",
    "had",
    "was",
    "has",
    "his",
    "her",
    "she",
    "out",
    "got",
    "like",
    "just",
    "yeah",
    "ooh",
    "hey",
    "mmm",
    "hmm",
    "ah",
    "uh",
}


# ─── LRC timestamp parser ───────────────────────────────────────────

_LRC_LINE_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]\s*(.*)")


def parse_lrc(lrc_text: str) -> List[Dict]:
    """Parse LRC-formatted synced lyrics into a list of timed lines.

    Each entry: {"time_ms": int, "text": str}
    Lines are sorted by time_ms ascending.
    Empty text lines are kept (they represent instrumental breaks).
    """
    lines: List[Dict] = []
    for raw_line in lrc_text.splitlines():
        m = _LRC_LINE_RE.match(raw_line.strip())
        if not m:
            continue
        minutes = int(m.group(1))
        seconds = int(m.group(2))
        centiseconds = m.group(3) or "0"
        # Normalise to milliseconds (handles .xx and .xxx)
        if len(centiseconds) == 2:
            ms = int(centiseconds) * 10
        else:
            ms = int(centiseconds)
        time_ms = minutes * 60_000 + seconds * 1000 + ms
        text = m.group(4).strip()
        lines.append({"time_ms": time_ms, "text": text})
    lines.sort(key=lambda x: x["time_ms"])
    return lines


# ─── Fetch helpers ───────────────────────────────────────────────────


def _lrclib_request(artist_clean: str, title_clean: str) -> Optional[dict]:
    """Call LRCLib API and return the JSON response dict or None."""
    try:
        resp = requests.get(
            "https://lrclib.net/api/get",
            params={
                "artist_name": artist_clean,
                "track_name": title_clean,
            },
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(
            "LRCLib request failed for %s - %s: %s",
            artist_clean,
            title_clean,
            e,
        )
    return None


def get_synced_lyrics_by_lrclib_id(lrclib_id: int) -> Optional[List[Dict]]:
    """
    Fetch synced lyrics directly from lrclib.net using a known numeric ID.

    This is faster and more reliable than a name-based search because it
    bypasses disambiguation and always resolves the exact entry chosen by
    an admin. Used by karaoke mode when KaraokeSong.lrclib_id is set.

    Returns:
        List of {"time_ms": int, "text": str} or None if unavailable.
    """
    cache_key = f"lrclib_id_{lrclib_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != "__NONE__" else None

    try:
        resp = requests.get(
            f"https://lrclib.net/api/get/{lrclib_id}",
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None
                cache.set(cache_key, lines if lines else "__NONE__", 3600)
                return lines
        # Cache negative result to avoid hammering the API
        cache.set(cache_key, "__NONE__", 3600)
    except Exception as exc:
        logger.warning("LRCLib by-id request failed for id=%s: %s", lrclib_id, exc)
    return None


def _clean_artist_title(artist: str, title: str) -> Tuple[str, str]:
    """Strip parenthesised suffixes for cleaner API queries."""
    artist_clean = re.sub(r"\s*\(.*?\)\s*", "", artist).strip()
    title_clean = re.sub(r"\s*\(.*?\)\s*", "", title).strip()
    return artist_clean, title_clean


def get_lyrics(artist: str, title: str) -> Optional[str]:
    """
    Fetch plain lyrics (Redis cache → LRCLib → lyrics.ovh fallback).

    Returns:
        Lyrics text or None
    """
    cache_key = f"lyrics_{hashlib.md5(f'{artist}|{title}'.lower().encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != "__NONE__" else None

    artist_clean, title_clean = _clean_artist_title(artist, title)

    # ── 1. LRCLib ────────────────────────────────────────────────────
    data = _lrclib_request(artist_clean, title_clean)
    if data:
        lyrics = data.get("plainLyrics", "")
        if lyrics and len(lyrics) >= 50:
            cache.set(cache_key, lyrics, 3600)
            return lyrics

    # ── 2. lyrics.ovh fallback ────────────────────────────────────────
    url = (
        f"https://api.lyrics.ovh/v1/"
        f"{requests.utils.quote(artist_clean)}/{requests.utils.quote(title_clean)}"
    )
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            lyrics = resp.json().get("lyrics", "")
            if lyrics and len(lyrics) >= 50:
                cache.set(cache_key, lyrics, 3600)
                return lyrics
    except Exception as e:
        logger.warning("lyrics.ovh failed for %s - %s: %s", artist, title, e)

    cache.set(cache_key, "__NONE__", 1800)
    return None


def _lrclib_search(query: str) -> Optional[dict]:
    """Call LRCLib /api/search and return the best matching result or None."""
    try:
        resp = requests.get(
            "https://lrclib.net/api/search",
            params={"q": query},
            timeout=8,
        )
        if resp.status_code == 200:
            results = resp.json()
            if isinstance(results, list) and results:
                # Prefer results that have synced lyrics
                for item in results:
                    if item.get("syncedLyrics"):
                        return item
                return results[0]
    except Exception as e:
        logger.warning("LRCLib search failed for %s: %s", query, e)
    return None


# Placeholder artists injected when YouTube title parsing cannot detect the artist.
_UNKNOWN_ARTIST_MARKERS = {"artiste inconnu", "unknown artist", "unknown", ""}


def get_synced_lyrics(artist: str, title: str) -> Optional[List[Dict]]:
    """
    Fetch synced (timestamped) lyrics.

    Resolution order:
      0. Redis cache (fastest)
      1. LRCLib /api/get  (exact artist + title)
      2. LRCLib /api/search ("artist title")
      3. LRCLib /api/search (title only — handles inverted YouTube title order)

    On a successful fetch from LRCLib the result is written to Redis cache.

    Returns:
        List of {"time_ms": int, "text": str} sorted by time, or None.
    """
    key = f"synced_{hashlib.md5(f'{artist}|{title}'.lower().encode()).hexdigest()}"
    cached = cache.get(key)
    if cached is not None:
        return cached if cached != "__NONE__" else None

    artist_clean, title_clean = _clean_artist_title(artist, title)
    artist_is_unknown = artist_clean.lower() in _UNKNOWN_ARTIST_MARKERS
    query = (
        title_clean if artist_is_unknown else f"{artist_clean} {title_clean}"
    )
    lines: Optional[List[Dict]] = None

    # ── 1. Exact query (skip if artist is a known placeholder) ────────
    if not artist_is_unknown:
        data = _lrclib_request(artist_clean, title_clean)
        if data:
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None

    # ── 2. Full-text search: "artist title" (or title-only) ───────────
    if lines is None:
        data = _lrclib_search(query)
        if data:
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None

    # ── 3. Last-resort: title-only (inverted YouTube order) ───────────
    if lines is None and not artist_is_unknown and query != title_clean:
        data = _lrclib_search(title_clean)
        if data:
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None

    if lines:
        cache.set(key, lines, 3600)
        return lines

    # Cache negative result for only 5 min so retries can succeed sooner
    cache.set(key, "__NONE__", 300)
    return None


def create_lyrics_question(
    lyrics: str,
    all_tracks_words: List[str] | None = None,
    words_to_blank: int = 1,
) -> Optional[Tuple[str, str, List[str]]]:
    """
    Create a fill-in-the-blank lyrics question.

    Args:
        lyrics: Full lyrics text
        all_tracks_words: Extra words from other tracks to use as wrong options

    Returns:
        (lyrics_snippet, correct_word, options) or None
    """
    # Split into lines, filter out empty / very short lines
    lines = [
        line.strip()
        for line in lyrics.split("\n")
        if line.strip() and len(line.strip()) > 15
    ]

    # We'll try to blank a contiguous sequence of words of length `words_to_blank`.
    for line in lines[:15]:
        words = line.split()
        if len(words) < (2 + words_to_blank):
            continue

        # Build candidate sequences of length words_to_blank where words are interesting
        sequences = []
        for start in range(0, len(words) - words_to_blank + 1):
            seq = words[start : start + words_to_blank]
            clean_seq = [re.sub(r"[^a-zA-ZÀ-ÿ']", "", w).lower() for w in seq]
            if any(len(w) < 1 for w in clean_seq):
                continue
            if any(w in BORING_WORDS for w in clean_seq):
                continue
            sequences.append((start, seq))

        if not sequences:
            continue

        start, original_seq = random.choice(sequences)
        # Build correct phrase
        clean_words = [re.sub(r"[^a-zA-ZÀ-ÿ' -]", "", w) for w in original_seq]
        correct_phrase = " ".join(clean_words)

        # Build snippet with a single placeholder for the whole sequence
        display_words = words.copy()
        display_words[start : start + words_to_blank] = ["_____"]
        snippet = " ".join(display_words)

        # Generate wrong options (phrases of same length)
        wrong_phrases: List[str] = []

        # Extract candidate n-word phrases from lyrics
        all_lyric_words = re.findall(r"[a-zA-ZÀ-ÿ' -]{1,}", lyrics)
        lyric_phrases = []
        for i in range(0, len(all_lyric_words) - words_to_blank + 1):
            seq = all_lyric_words[i : i + words_to_blank]
            cleaned = [re.sub(r"[^a-zA-ZÀ-ÿ']", "", w).lower() for w in seq]
            if any(w in BORING_WORDS or len(w) < 1 for w in cleaned):
                continue
            phrase = " ".join(
                [
                    w if idx == 0 and w[0].isupper() else w.lower()
                    for idx, w in enumerate(seq)
                ]
            )
            lyric_phrases.append(phrase)

        random.shuffle(lyric_phrases)
        for p in lyric_phrases:
            if p.lower() != correct_phrase.lower():
                wrong_phrases.append(p)
            if len(wrong_phrases) >= 6:
                break

        # Add phrases built from other tracks' words if available
        if all_tracks_words:
            other_candidates = []
            # build simple phrases by sampling consecutive words from extra list
            for i in range(0, len(all_tracks_words) - words_to_blank + 1):
                seq = all_tracks_words[i : i + words_to_blank]
                cleaned = [
                    re.sub(r"[^a-zA-ZÀ-ÿ']", "", w).lower() for w in seq
                ]
                if any(w in BORING_WORDS or len(w) < 1 for w in cleaned):
                    continue
                other_candidates.append(" ".join(seq))
            random.shuffle(other_candidates)
            for p in other_candidates:
                if (
                    p.lower() != correct_phrase.lower()
                    and p not in wrong_phrases
                ):
                    wrong_phrases.append(p)
                if len(wrong_phrases) >= 10:
                    break

        # Deduplicate and pick 3 wrong options
        seen = {correct_phrase.lower()}
        unique_wrong = []
        for w in wrong_phrases:
            low = w.lower()
            if low not in seen:
                seen.add(low)
                unique_wrong.append(w)
            if len(unique_wrong) >= 3:
                break

        if len(unique_wrong) < 3:
            continue

        options = [correct_phrase] + unique_wrong[:3]
        random.shuffle(options)

        return snippet, correct_phrase, options

    return None
