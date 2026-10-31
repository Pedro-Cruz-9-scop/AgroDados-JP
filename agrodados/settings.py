from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG", "0").lower() in {"1", "true", "yes"}
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "local-development-key-do-not-use-in-production" if DEBUG else ""
)
if not SECRET_KEY:
    raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY antes de iniciar em produção.")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "agrodados.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "agrodados.wsgi.application"
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    if not DEBUG and os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        raise ImproperlyConfigured(
            "Configure DATABASE_URL com um PostgreSQL persistente antes de iniciar no Render."
        )
    DATABASE_PATH = Path(os.environ.get("DJANGO_DATABASE_PATH", BASE_DIR / "db.sqlite3"))
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DATABASE_PATH}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Bahia"
USE_I18N = True
USE_TZ = True
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
R2_STORAGE_SETTINGS = {
    "access_key": os.environ.get("R2_ACCESS_KEY_ID"),
    "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY"),
    "bucket_name": os.environ.get("R2_BUCKET_NAME"),
    "endpoint_url": os.environ.get("R2_ENDPOINT_URL"),
}
R2_STORAGE_CONFIGURED = all(R2_STORAGE_SETTINGS.values())
if any(R2_STORAGE_SETTINGS.values()) and not R2_STORAGE_CONFIGURED:
    raise ImproperlyConfigured(
        "Configure todas as variáveis R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, "
        "R2_BUCKET_NAME e R2_ENDPOINT_URL."
    )
if not DEBUG and os.environ.get("RENDER_EXTERNAL_HOSTNAME") and not R2_STORAGE_CONFIGURED:
    raise ImproperlyConfigured(
        "Configure o armazenamento persistente R2 antes de iniciar no Render."
    )
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": (
            "storages.backends.s3.S3Storage"
            if R2_STORAGE_CONFIGURED
            else "django.core.files.storage.FileSystemStorage"
        ),
        **(
            {
                "OPTIONS": {
                    **R2_STORAGE_SETTINGS,
                    "region_name": "auto",
                    "default_acl": None,
                    "querystring_auth": True,
                    "file_overwrite": False,
                }
            }
            if R2_STORAGE_CONFIGURED
            else {}
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/entrar/"
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31_536_000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = (
    [f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}"]
    if os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    else []
)
