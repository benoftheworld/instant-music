"""
Lyrics service — fetches song lyrics from lyrics.ovh (free, no key).
Used by the 'lyrics' game mode to create fill-in-the-blank questions.
"""
import logging
import random
import re
import hashlib
from typing import Optional, Tuple, List

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Words that are too short or common to be interesting blanks
BORING_WORDS = {
    'i', 'a', 'the', 'an', 'is', 'it', 'in', 'on', 'to', 'of', 'and',
    'or', 'at', 'my', 'me', 'we', 'he', 'be', 'do', 'so', 'no', 'oh',
    'je', 'tu', 'il', 'le', 'la', 'de', 'et', 'un', 'ne', 'se', 'ce',
    'en', 'du', 'au', 'on', 'ma', 'sa', 'si', 'ou', 'ni', 'que', 'qui',
    'les', 'des', 'une', 'pas', 'son', 'que', 'par', 'sur', 'mais', 'pour',
    'the', 'and', 'you', 'for', 'are', 'but', 'not', 'all', 'can', 'had',
    'was', 'has', 'his', 'her', 'she', 'out', 'got', 'like', 'just',
    'yeah', 'ooh', 'hey', 'mmm', 'hmm', 'ah', 'uh',
}


def get_lyrics(artist: str, title: str) -> Optional[str]:
    """
    Fetch lyrics from lyrics.ovh API.

    Args:
        artist: Artist name
        title:  Song title

    Returns:
        Lyrics text or None
    """
    cache_key = f"lyrics_{hashlib.md5(f'{artist}|{title}'.lower().encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != '__NONE__' else None

    # Clean up artist/title for API call
    artist_clean = re.sub(r'\s*\(.*?\)\s*', '', artist).strip()
    title_clean = re.sub(r'\s*\(.*?\)\s*', '', title).strip()

    # Try LRCLib first (reliable, free, no key required)
    try:
        resp = requests.get(
            'https://lrclib.net/api/get',
            params={'artist_name': artist_clean, 'track_name': title_clean},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            lyrics = data.get('plainLyrics', '')
            if lyrics and len(lyrics) >= 50:
                cache.set(cache_key, lyrics, 3600)
                return lyrics
    except Exception as e:
        logger.warning("LRCLib failed for %s - %s: %s", artist, title, e)

    # Fallback: lyrics.ovh
    url = f"https://api.lyrics.ovh/v1/{requests.utils.quote(artist_clean)}/{requests.utils.quote(title_clean)}"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            lyrics = data.get('lyrics', '')
            if lyrics and len(lyrics) >= 50:
                cache.set(cache_key, lyrics, 3600)
                return lyrics
    except Exception as e:
        logger.warning("lyrics.ovh failed for %s - %s: %s", artist, title, e)

    cache.set(cache_key, '__NONE__', 1800)
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
        line.strip() for line in lyrics.split('\n')
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
            seq = words[start:start + words_to_blank]
            clean_seq = [re.sub(r"[^a-zA-ZÀ-ÿ']", '', w).lower() for w in seq]
            if any(len(w) < 1 for w in clean_seq):
                continue
            if any(w in BORING_WORDS for w in clean_seq):
                continue
            sequences.append((start, seq))

        if not sequences:
            continue

        start, original_seq = random.choice(sequences)
        # Build correct phrase
        clean_words = [re.sub(r"[^a-zA-ZÀ-ÿ' -]", '', w) for w in original_seq]
        correct_phrase = ' '.join(clean_words)

        # Build snippet with a single placeholder for the whole sequence
        display_words = words.copy()
        display_words[start:start + words_to_blank] = ['_____']
        snippet = ' '.join(display_words)

        # Generate wrong options (phrases of same length)
        wrong_phrases: List[str] = []

        # Extract candidate n-word phrases from lyrics
        all_lyric_words = re.findall(r"[a-zA-ZÀ-ÿ' -]{1,}", lyrics)
        lyric_phrases = []
        for i in range(0, len(all_lyric_words) - words_to_blank + 1):
            seq = all_lyric_words[i:i + words_to_blank]
            cleaned = [re.sub(r"[^a-zA-ZÀ-ÿ']", '', w).lower() for w in seq]
            if any(w in BORING_WORDS or len(w) < 1 for w in cleaned):
                continue
            phrase = ' '.join([w if idx == 0 and w[0].isupper() else w.lower() for idx, w in enumerate(seq)])
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
                seq = all_tracks_words[i:i + words_to_blank]
                cleaned = [re.sub(r"[^a-zA-ZÀ-ÿ']", '', w).lower() for w in seq]
                if any(w in BORING_WORDS or len(w) < 1 for w in cleaned):
                    continue
                other_candidates.append(' '.join(seq))
            random.shuffle(other_candidates)
            for p in other_candidates:
                if p.lower() != correct_phrase.lower() and p not in wrong_phrases:
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
