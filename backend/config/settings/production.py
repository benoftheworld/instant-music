"""Production settings for InstantMusic project.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403

DEBUG = False

# ── Sécurité : vérification des clés au démarrage ────────────────────
_INSECURE_DEFAULTS = {
    "SECRET_KEY": "django-insecure-change-this-in-production",
    "EMAIL_ENCRYPTION_KEY": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "EMAIL_HASH_KEY": "change-this-hash-key-in-production",
}
for _var_name, _insecure_value in _INSECURE_DEFAULTS.items():
    if globals().get(_var_name) == _insecure_value:
        raise ImproperlyConfigured(
            f"{_var_name} utilise encore sa valeur par défaut non sécurisée. "
            f"Définissez {_var_name} dans votre fichier .env.prod."
        )

# Security settings
# SECURE_SSL_REDIRECT doit rester False si Nginx gère déjà la redirection HTTP→HTTPS.
# Mettre True UNIQUEMENT si Django est exposé directement sans reverse proxy.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
# Indique à Django que les requêtes sont HTTPS via le header X-Forwarded-Proto de Nginx.
# Requis pour que SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE et HSTS fonctionnent correctement.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
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

# ── CDN / S3 storage (optionnel) ────────────────────────────────────
# Activé si AWS_STORAGE_BUCKET_NAME est défini.
# Sans cette variable, Django sert les fichiers statiques/media via Nginx.
_s3_bucket = env("AWS_STORAGE_BUCKET_NAME", default="")
if _s3_bucket:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "storages.backends.s3boto3.S3StaticStorage"},
    }
    AWS_STORAGE_BUCKET_NAME = _s3_bucket
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="eu-west-3")
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

# ── Read replica PostgreSQL (optionnel) ──────────────────────────────
# Activé si DB_REPLICA_HOST est défini.
_replica_host = env("DB_REPLICA_HOST", default="")
if _replica_host:
    DATABASES["replica"] = {  # noqa: F405
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="instantmusic"),
        "USER": env("POSTGRES_USER", default="postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="postgres"),
        "HOST": _replica_host,
        "PORT": env("DB_REPLICA_PORT", default="5432"),
        "OPTIONS": {"options": "-c default_transaction_read_only=on"},
    }
    DATABASE_ROUTERS = ["config.db_router.ReadReplicaRouter"]
