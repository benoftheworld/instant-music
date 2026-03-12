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

if not env("JWT_SIGNING_KEY", default=None):
    raise ImproperlyConfigured(
        "JWT_SIGNING_KEY doit être défini en production. "
        "Ajoutez JWT_SIGNING_KEY dans votre fichier .env.prod."
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

# Logging : surcharge la config de base pour ajouter des handlers fichier rotatifs en prod
# Fichier principal : tous les logs WARNING+ avec rotation par taille (10 MB × 10 = max 100 MB)
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.handlers.RotatingFileHandler",
    "filename": BASE_DIR / "logs" / "django.log",  # noqa: F405
    "maxBytes": 10 * 1024 * 1024,  # 10 MB par fichier
    "backupCount": 10,              # 10 fichiers = 100 MB max
    "formatter": "json",
    "filters": ["redact_sensitive_params"],
    "level": "WARNING",
    "encoding": "utf-8",
    "delay": True,                  # Ne crée le fichier qu'au premier log
}
# Fichier erreurs : ERROR+ uniquement avec rotation temporelle (1 fichier/jour × 30 jours)
LOGGING["handlers"]["file_errors"] = {  # noqa: F405
    "class": "logging.handlers.TimedRotatingFileHandler",
    "filename": BASE_DIR / "logs" / "errors.log",  # noqa: F405
    "when": "midnight",
    "interval": 1,
    "backupCount": 30,              # 30 jours d'historique des erreurs
    "formatter": "json",
    "filters": ["redact_sensitive_params"],
    "level": "ERROR",
    "encoding": "utf-8",
    "delay": True,
    "utc": True,
}
LOGGING["root"]["handlers"] = ["console", "file", "file_errors"]  # noqa: F405
LOGGING["loggers"]["django"]["handlers"] = ["console", "file", "file_errors"]  # noqa: F405
LOGGING["loggers"].setdefault("apps", {}).update(  # noqa: F405
    {"handlers": ["console", "file", "file_errors"], "level": "INFO", "propagate": False}
)
# Exceptions DRF : toujours loggées dans les deux fichiers
LOGGING["loggers"]["apps.core.exceptions"]["handlers"] = ["console", "file", "file_errors"]  # noqa: F405
# HTTP structuré : warning+ dans le fichier, errors dans file_errors
LOGGING["loggers"]["apps.core.http"]["handlers"] = ["console", "file", "file_errors"]  # noqa: F405
# Celery en prod
LOGGING["loggers"]["celery"]["handlers"] = ["console", "file", "file_errors"]  # noqa: F405

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
    LOGGING["loggers"]["apps.core.exceptions"]["handlers"].append("logstash")  # noqa: F405
    LOGGING["loggers"]["apps.core.http"]["handlers"].append("logstash")  # noqa: F405
    LOGGING["loggers"]["celery"]["handlers"].append("logstash")  # noqa: F405
    # file_errors n'est pas ajouté à logstash (déjà envoyé via les autres loggers)

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

# ── Connection pool (psycopg3) ───────────────────────────────────────
# CONN_MAX_AGE must be 0 when using psycopg3 built-in pool.
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
DATABASES["default"]["OPTIONS"] = {  # noqa: F405
    "pool": {
        "min_size": env.int("DB_POOL_MIN_SIZE", default=2),
        "max_size": env.int("DB_POOL_MAX_SIZE", default=4),
        "timeout": 10,
    },
}

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
