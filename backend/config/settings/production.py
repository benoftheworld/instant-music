"""
Production settings for InstantMusic project.
"""

from .base import *

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
# HSTS : 1 an, cohérent avec nginx. Active le preload HSTS uniquement
# après avoir vérifié l'inscription sur hstspreload.org.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS settings
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
# CSRF trusted origins (must include scheme, e.g. https://example.com)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Logging : surcharge la config de base pour ajouter un handler fichier rotatif en prod
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.handlers.RotatingFileHandler",
    "filename": BASE_DIR / "logs" / "django.log",  # noqa: F405
    "maxBytes": 10 * 1024 * 1024,  # 10 MB
    "backupCount": 5,
    "formatter": "json",
    "level": "WARNING",
}
LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["django"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"].setdefault("apps", {}).update(  # noqa: F405
    {"handlers": ["console", "file"], "level": "INFO", "propagate": False}
)

# Handler Logstash (optionnel — activé si LOGSTASH_HOST est défini)
# En production avec le monitoring actif : LOGSTASH_HOST=logstash dans .env.prod
_logstash_host = env("LOGSTASH_HOST", default="")
if _logstash_host:
    LOGGING["handlers"]["logstash"] = {  # noqa: F405
        "class": "logstash.TCPLogstashHandler",
        "host": _logstash_host,
        "port": env.int("LOGSTASH_PORT", default=5000),
        "version": 1,
        "message_type": "django",
        "fqdn": False,
        "tags": ["django", "instantmusic"],
    }
    LOGGING["root"]["handlers"].append("logstash")  # noqa: F405
    LOGGING["loggers"]["django"]["handlers"].append("logstash")  # noqa: F405
    LOGGING["loggers"]["apps"]["handlers"].append("logstash")  # noqa: F405

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
