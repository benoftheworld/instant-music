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

    if len(lines) < 3:
        return None

    # Try several random lines to find one with a good blank-able word
    random.shuffle(lines)

    for line in lines[:15]:
        words = line.split()
        if len(words) < 4:
            continue

        # Find candidate words to blank out (interesting words)
        candidates = []
        for idx, word in enumerate(words):
            clean = re.sub(r'[^a-zA-ZÀ-ÿ]', '', word).lower()
            if len(clean) >= 3 and clean not in BORING_WORDS:
                candidates.append((idx, word))

        if not candidates:
            continue

        idx, original_word = random.choice(candidates)
        clean_word = re.sub(r'[^a-zA-ZÀ-ÿ\'-]', '', original_word)

        # Build the snippet with a blank
        display_words = words.copy()
        display_words[idx] = '_____'
        snippet = ' '.join(display_words)

        # Generate wrong options
        wrong_words: List[str] = []

        # Use words from the same lyrics
        all_lyric_words = re.findall(r'[a-zA-ZÀ-ÿ\'-]{3,}', lyrics)
        lyric_candidates = list({
            w for w in all_lyric_words
            if w.lower() != clean_word.lower()
            and w.lower() not in BORING_WORDS
            and len(w) >= 3
        })
        random.shuffle(lyric_candidates)
        wrong_words.extend(lyric_candidates[:6])

        # Add words from other tracks if available
        if all_tracks_words:
            extra = [
                w for w in all_tracks_words
                if w.lower() != clean_word.lower()
                and w.lower() not in BORING_WORDS
                and w not in wrong_words
            ]
            random.shuffle(extra)
            wrong_words.extend(extra[:4])

        # Deduplicate and pick 3
        seen = {clean_word.lower()}
        unique_wrong = []
        for w in wrong_words:
            low = w.lower()
            if low not in seen:
                seen.add(low)
                unique_wrong.append(w.capitalize() if clean_word[0].isupper() else w.lower())
            if len(unique_wrong) >= 3:
                break

        if len(unique_wrong) < 3:
            continue

        options = [clean_word] + unique_wrong[:3]
        random.shuffle(options)

        return snippet, clean_word, options

    return None
