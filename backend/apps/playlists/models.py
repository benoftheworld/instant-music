"""
Playlists app models removed.

`Playlist` and `Track` models have been deleted — the app now provides
YouTube/Deezer helper endpoints only (cached DB models removed).

Keeping this file present (empty) so Django app import does not fail.
"""

from django.db import models  # keep import available for potential future models
