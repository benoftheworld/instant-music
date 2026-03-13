"""Development settings for InstantMusic project.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# Rate limiting : seuils élevés pour ne pas bloquer le développement
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    k: "1000/min"
    for k in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]  # noqa: F405
}

# Development email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
