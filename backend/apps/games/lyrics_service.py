"""
Lyrics service — fetches song lyrics from LRCLib and lyrics.ovh (free, no key).
Used by the 'paroles' game mode (fill-in-the-blank) and 'karaoke' mode (synced lyrics).
"""

import logging
import random
import re
import hashlib
from typing import Optional, Tuple, List, Dict

import json
import socket
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlencode
from urllib.parse import quote as url_quote

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────

# (connect_timeout, read_timeout) — short connect so a down server fails fast
API_TIMEOUT: tuple = (3, 6)
CACHE_TTL_LYRICS: int = 3600  # 1 hour for successful lyrics
CACHE_TTL_NEGATIVE: int = 1800  # 30 min for "not found" lyrics
CACHE_TTL_SYNCED_NEG: int = 300  # 5 min for "not found" synced lyrics
CACHE_TTL_LRCLIB_ID: int = 3600  # 1 hour for lrclib-by-id results

# Circuit-breaker: if lrclib.net is unreachable, skip it for this window
_LRCLIB_DOWN_KEY: str = "lrclib_circuit_open"
_LRCLIB_DOWN_TTL: int = 90  # seconds before retrying after all failures


_OP_IGNORE_UNEXPECTED_EOF: int = getattr(ssl, "OP_IGNORE_UNEXPECTED_EOF", 0x80)
_LRCLIB_READ_TIMEOUT: int = (
    12  # lrclib.net can be slow; single call so 12s is acceptable
)


def _lrclib_ssl_context() -> ssl.SSLContext:
    """Return an SSL context that works with lrclib.net on OpenSSL 3.5+.

    OpenSSL 3.5 raised the default SECLEVEL to 2, which rejects ciphers/
    certificates used by lrclib.net during the TLS handshake.  Lowering to
    SECLEVEL=1 and using PROTOCOL_TLS_CLIENT (not create_default_context)
    matches curl's effective behaviour on the same host.

    urllib.request is used (not requests/urllib3) because urllib3 wraps SSL
    sockets via MemoryBIO in a way that consistently triggers
    SSLZeroReturnError for this host even with the same SSL options.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_default_certs()
    ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.options |= _OP_IGNORE_UNEXPECTED_EOF
    return ctx


def _lrclib_fetch(url: str, params: Optional[dict] = None):
    """GET a lrclib.net endpoint via urllib.request; return parsed JSON or None.

    Uses urllib.request directly to bypass urllib3's MemoryBIO SSL layer,
    which is incompatible with lrclib.net's TLS stack on OpenSSL 3.5.
    Marks the circuit breaker only on genuine connection failures (DNS,
    refused), not on SSL or timeout errors.
    """
    if _lrclib_is_down():
        return None
    if params:
        url = f"{url}?{urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "InstantMusic/1.0 (lyrics fetcher)"},
    )
    try:
        with urllib.request.urlopen(
            req, context=_lrclib_ssl_context(), timeout=_LRCLIB_READ_TIMEOUT
        ) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except ssl.SSLError as exc:
        # Transient TLS issue — do NOT open circuit breaker
        logger.warning("LRCLib SSL error for %s: %s", url, exc)
    except (socket.timeout, TimeoutError) as exc:
        logger.warning("LRCLib timeout for %s: %s", url, exc)
    except urllib.error.HTTPError as exc:
        logger.warning(
            "LRCLib HTTP error for %s: %s %s", url, exc.code, exc.reason
        )
    except urllib.error.URLError as exc:
        # Connection refused, DNS failure — server genuinely unreachable
        logger.warning("LRCLib connection error for %s: %s", url, exc)
        _lrclib_mark_down()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LRCLib unexpected error for %s: %s", url, exc)
    return None


def _lrclib_is_down() -> bool:
    """True when the circuit breaker flag is set (lrclib recently failed)."""
    return bool(cache.get(_LRCLIB_DOWN_KEY))


def _lrclib_mark_down() -> None:
    """Open the circuit breaker for _LRCLIB_DOWN_TTL seconds."""
    # Only set if not already set (preserve the original expiry)
    cache.add(_LRCLIB_DOWN_KEY, True, _LRCLIB_DOWN_TTL)


# ─── Common words excluded from fill-in-the-blank ───────────────────

BORING_WORDS = {
    # English
    "a",
    "ah",
    "all",
    "an",
    "and",
    "are",
    "at",
    "be",
    "but",
    "can",
    "do",
    "for",
    "got",
    "had",
    "has",
    "he",
    "her",
    "hey",
    "his",
    "hmm",
    "i",
    "in",
    "is",
    "it",
    "just",
    "like",
    "me",
    "mmm",
    "my",
    "no",
    "not",
    "of",
    "oh",
    "on",
    "ooh",
    "or",
    "out",
    "she",
    "so",
    "the",
    "to",
    "uh",
    "was",
    "we",
    "yeah",
    "you",
    # French
    "au",
    "ce",
    "de",
    "des",
    "du",
    "en",
    "et",
    "il",
    "je",
    "la",
    "le",
    "les",
    "ma",
    "mais",
    "ne",
    "ni",
    "ou",
    "par",
    "pas",
    "pour",
    "que",
    "qui",
    "sa",
    "se",
    "si",
    "son",
    "sur",
    "tu",
    "un",
    "une",
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
    """Call LRCLib /api/get and return the JSON response dict or None."""
    return _lrclib_fetch(
        "https://lrclib.net/api/get",
        params={"artist_name": artist_clean, "track_name": title_clean},
    )


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

    data = _lrclib_fetch(f"https://lrclib.net/api/get/{lrclib_id}")
    if data is not None:
        raw = data.get("syncedLyrics", "")
        if raw:
            lines = parse_lrc(raw) or None
            cache.set(
                cache_key,
                lines if lines else "__NONE__",
                CACHE_TTL_LRCLIB_ID,
            )
            return lines
    # Cache negative result to avoid hammering the API
    cache.set(cache_key, "__NONE__", CACHE_TTL_LRCLIB_ID)
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
            cache.set(cache_key, lyrics, CACHE_TTL_LYRICS)
            return lyrics

    # ── 2. lyrics.ovh fallback ────────────────────────────────────────
    url = (
        f"https://api.lyrics.ovh/v1/"
        f"{url_quote(artist_clean)}/{url_quote(title_clean)}"
    )
    try:
        resp = requests.get(url, timeout=API_TIMEOUT)
        if resp.status_code == 200:
            lyrics = resp.json().get("lyrics", "")
            if lyrics and len(lyrics) >= 50:
                cache.set(cache_key, lyrics, CACHE_TTL_LYRICS)
                return lyrics
    except Exception as e:
        logger.warning("lyrics.ovh failed for %s - %s: %s", artist, title, e)

    cache.set(cache_key, "__NONE__", CACHE_TTL_NEGATIVE)
    return None


def _lrclib_search(query: str) -> Optional[dict]:
    """Call LRCLib /api/search and return the best matching result or None."""
    results = _lrclib_fetch(
        "https://lrclib.net/api/search", params={"q": query}
    )
    if isinstance(results, list) and results:
        # Prefer results that have synced lyrics
        for item in results:
            if item.get("syncedLyrics"):
                return item
        return results[0]
    return None


# Placeholder artists injected when YouTube title parsing cannot detect the artist.
_UNKNOWN_ARTIST_MARKERS = {"artiste inconnu", "unknown artist", "unknown", ""}


def get_synced_lyrics(
    artist: str, title: str
) -> Tuple[Optional[List[Dict]], Optional[int]]:
    """
    Fetch synced (timestamped) lyrics.

    Resolution order:
      0. Redis cache (fastest)
      1. LRCLib /api/get  (exact artist + title)
      2. LRCLib /api/search ("artist title")
      3. LRCLib /api/search (title only — handles inverted YouTube title order)

    On a successful fetch from LRCLib the result is written to Redis cache.

    Returns:
        Tuple of (List of {"time_ms": int, "text": str}, found_lrclib_id) or (None, None).
        ``found_lrclib_id`` is the numeric ID on lrclib.net for the matched entry;
        callers can persist it to avoid future search-based lookups.
    """
    key = f"synced_{hashlib.md5(f'{artist}|{title}'.lower().encode()).hexdigest()}"
    cached = cache.get(key)
    if cached is not None:
        if cached == "__NONE__":
            return None, None
        # Handle both new dict format and legacy list format
        if isinstance(cached, list):
            return cached, None
        return cached.get("lines"), cached.get("lrclib_id")

    artist_clean, title_clean = _clean_artist_title(artist, title)
    artist_is_unknown = artist_clean.lower() in _UNKNOWN_ARTIST_MARKERS
    query = (
        title_clean if artist_is_unknown else f"{artist_clean} {title_clean}"
    )
    lines: Optional[List[Dict]] = None
    found_lrclib_id: Optional[int] = None

    # ── 1. Exact query (skip if artist is a known placeholder) ────────
    if not artist_is_unknown:
        data = _lrclib_request(artist_clean, title_clean)
        if data:
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None
                if lines:
                    found_lrclib_id = data.get("id")

    # ── 2. Full-text search: "artist title" (or title-only) ───────────
    if lines is None:
        data = _lrclib_search(query)
        if data:
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None
                if lines:
                    found_lrclib_id = data.get("id")

    # ── 3. Last-resort: title-only (inverted YouTube order) ───────────
    if lines is None and not artist_is_unknown and query != title_clean:
        data = _lrclib_search(title_clean)
        if data:
            raw = data.get("syncedLyrics", "")
            if raw:
                lines = parse_lrc(raw) or None
                if lines:
                    found_lrclib_id = data.get("id")

    if lines:
        cache.set(
            key,
            {"lines": lines, "lrclib_id": found_lrclib_id},
            CACHE_TTL_LYRICS,
        )
        return lines, found_lrclib_id

    # Cache negative result for only 5 min so retries can succeed sooner
    cache.set(key, "__NONE__", CACHE_TTL_SYNCED_NEG)
    return None, None


def _extract_line_sequences(
    line: str, n: int
) -> List[Tuple[int, List[str]]]:
    """Extract all valid n-word sequences from a lyrics line.

    Returns list of (start_index, word_sequence) tuples where every word
    in the sequence is "interesting" (not in BORING_WORDS and long enough).
    """
    words = line.split()
    sequences: List[Tuple[int, List[str]]] = []
    for start in range(0, len(words) - n + 1):
        seq = words[start : start + n]
        clean_seq = [re.sub(r"[^a-zA-ZÀ-ÿ']", "", w).lower() for w in seq]
        if any(len(w) < 2 for w in clean_seq):
            continue
        if any(w in BORING_WORDS for w in clean_seq):
            continue
        sequences.append((start, seq))
    return sequences


def create_lyrics_question(
    lyrics: str,
    all_tracks_words: List[str] | None = None,
    words_to_blank: int = 1,
) -> Optional[Tuple[str, str, List[str]]]:
    """
    Create a fill-in-the-blank lyrics question.

    Wrong options are sourced **from other lines of the same lyrics** first,
    guaranteeing language consistency and coherent phrasing.  Track-title
    words are only used as a last resort.

    Args:
        lyrics: Full lyrics text
        all_tracks_words: Extra words from other tracks (last-resort distractors)
        words_to_blank: Number of consecutive words to blank out

    Returns:
        (lyrics_snippet, correct_phrase, options) or None
    """
    # Split into lines, filter out empty / very short lines
    lines = [
        line.strip()
        for line in lyrics.split("\n")
        if line.strip() and len(line.strip()) > 15
    ]

    if not lines:
        return None

    # Shuffle candidate lines so we don't always pick the first one
    candidate_indices = list(range(len(lines)))
    random.shuffle(candidate_indices)

    for chosen_idx in candidate_indices[:20]:
        line = lines[chosen_idx]
        words = line.split()
        if len(words) < (2 + words_to_blank):
            continue

        sequences = _extract_line_sequences(line, words_to_blank)
        if not sequences:
            continue

        start, original_seq = random.choice(sequences)
        # Build correct phrase (strip trailing punctuation, keep internal)
        clean_words = [re.sub(r"[^a-zA-ZÀ-ÿ' -]", "", w) for w in original_seq]
        correct_phrase = " ".join(clean_words)
        if not correct_phrase.strip():
            continue

        # Build snippet with a single placeholder for the blanked sequence
        display_words = words.copy()
        display_words[start : start + words_to_blank] = ["_____"]
        snippet = " ".join(display_words)

        # ── Generate wrong options from OTHER lines of the same lyrics ─
        # This guarantees the same language and coherent phrases.
        wrong_phrases: List[str] = []
        seen_lower = {correct_phrase.lower()}

        other_lines = [l for i, l in enumerate(lines) if i != chosen_idx]
        random.shuffle(other_lines)
        for other_line in other_lines:
            for _, seq in _extract_line_sequences(other_line, words_to_blank):
                phrase = " ".join(
                    re.sub(r"[^a-zA-ZÀ-ÿ' -]", "", w) for w in seq
                )
                low = phrase.lower()
                if low not in seen_lower and phrase.strip():
                    seen_lower.add(low)
                    wrong_phrases.append(phrase)
            if len(wrong_phrases) >= 8:
                break

        # ── Last-resort fallback: individual track title words ─────────
        # Only used when the lyrics lack enough distinct phrases.
        # We never combine words from different titles to avoid gibberish.
        if len(wrong_phrases) < 3 and all_tracks_words and words_to_blank == 1:
            random.shuffle(all_tracks_words)
            for w in all_tracks_words:
                cleaned = re.sub(r"[^a-zA-ZÀ-ÿ']", "", w).lower()
                if (
                    len(cleaned) >= 3
                    and cleaned not in BORING_WORDS
                    and cleaned not in seen_lower
                ):
                    seen_lower.add(cleaned)
                    wrong_phrases.append(w)
                if len(wrong_phrases) >= 6:
                    break

        # Deduplicate and pick 3 wrong options
        unique_wrong: List[str] = []
        final_seen = {correct_phrase.lower()}
        for w in wrong_phrases:
            low = w.lower()
            if low not in final_seen:
                final_seen.add(low)
                unique_wrong.append(w)
            if len(unique_wrong) >= 3:
                break

        if len(unique_wrong) < 3:
            continue

        options = [correct_phrase] + unique_wrong[:3]
        random.shuffle(options)

        return snippet, correct_phrase, options

    return None
