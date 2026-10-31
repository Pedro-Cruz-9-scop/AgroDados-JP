import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get('DJANGO_DEBUG', '0').lower() in {'1', 'true', 'yes'}
# Apenas para testes: permite rodar no Render com SQLite e arquivos temporários (dados somem ao reiniciar).
ALLOW_EPHEMERAL_STORAGE = os.environ.get('ALLOW_EPHEMERAL_STORAGE', '0').lower() in {
    '1',
    'true',
    'yes',
}
DEPLOYED_ON_RENDER = bool(os.environ.get('RENDER_EXTERNAL_HOSTNAME'))
DEPLOYED_ON_VERCEL = os.environ.get('VERCEL') == '1'
# Defina DJANGO_HOST_PLATFORM=ethiodeploy no painel do EthioDeploy.
DEPLOYED_ON_ETHIODEPLOY = os.environ.get('DJANGO_HOST_PLATFORM', '').lower() == 'ethiodeploy'
DEPLOYED_ON_SERVERLESS_HOST = DEPLOYED_ON_RENDER or DEPLOYED_ON_VERCEL or DEPLOYED_ON_ETHIODEPLOY
# O Vercel importa estas configurações durante o build, antes de o app iniciar.
# Lá os erros são acumulados e só barram o início real do app (veja wsgi.py).
DEPLOYMENT_ERRORS = []


# O build da hospedagem pode rodar collectstatic sem as variáveis de ambiente.
COLLECTSTATIC_RUN = 'collectstatic' in sys.argv


def config_error(message):
    if COLLECTSTATIC_RUN:
        return
    if DEPLOYED_ON_VERCEL:
        DEPLOYMENT_ERRORS.append(message)
    else:
        raise ImproperlyConfigured(message)


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or (
    'local-development-key-do-not-use-in-production' if DEBUG else ''
)
if not SECRET_KEY:
    config_error('Defina DJANGO_SECRET_KEY antes de iniciar em produção.')
    SECRET_KEY = 'build-only-placeholder-key-not-for-runtime'
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]
VERCEL_HOSTS = [
    os.environ[name].strip()
    for name in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL')
    if os.environ.get(name, '').strip()
]
PLATFORM_HOSTS = [*VERCEL_HOSTS]
if DEPLOYED_ON_VERCEL:
    PLATFORM_HOSTS.append('.vercel.app')
if DEPLOYED_ON_ETHIODEPLOY:
    PLATFORM_HOSTS.append('.ethiodeploy.app')
for host in PLATFORM_HOSTS:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'agrodados.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]
WSGI_APPLICATION = 'agrodados.wsgi.application'
# collectstatic não acessa o banco; ignorar a URL evita exigir o driver no build.
DATABASE_URL = None if COLLECTSTATIC_RUN else os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    if not DEBUG and DEPLOYED_ON_SERVERLESS_HOST and not ALLOW_EPHEMERAL_STORAGE:
        config_error(
            'Configure DATABASE_URL com um PostgreSQL persistente antes de iniciar no Render, Vercel ou EthioDeploy.'
        )
    # No Vercel só /tmp é gravável; no modo de teste o SQLite fica lá.
    DATABASE_PATH = Path(
        os.environ.get(
            'DJANGO_DATABASE_PATH',
            '/tmp/db.sqlite3' if DEPLOYED_ON_VERCEL else BASE_DIR / 'db.sqlite3',
        )
    )
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DATABASE_PATH}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Bahia'
USE_I18N = True
USE_TZ = True
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(
    os.environ.get('DJANGO_MEDIA_ROOT', '/tmp/media' if DEPLOYED_ON_VERCEL else BASE_DIR / 'media')
)
R2_STORAGE_SETTINGS = {
    'access_key': os.environ.get('R2_ACCESS_KEY_ID'),
    'secret_key': os.environ.get('R2_SECRET_ACCESS_KEY'),
    'bucket_name': os.environ.get('R2_BUCKET_NAME'),
    'endpoint_url': os.environ.get('R2_ENDPOINT_URL'),
}
R2_STORAGE_CONFIGURED = all(R2_STORAGE_SETTINGS.values())
if any(R2_STORAGE_SETTINGS.values()) and not R2_STORAGE_CONFIGURED:
    raise ImproperlyConfigured(
        'Configure todas as variáveis R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, '
        'R2_BUCKET_NAME e R2_ENDPOINT_URL.'
    )
# Onde guardar fotos e documentos: R2 (se configurado), o banco de dados em
# hospedagens sem disco persistente (Vercel/Render/EthioDeploy) ou o disco local.
if R2_STORAGE_CONFIGURED:
    FILE_STORAGE = 'r2'
elif DEPLOYED_ON_SERVERLESS_HOST and not DEBUG and not ALLOW_EPHEMERAL_STORAGE:
    FILE_STORAGE = 'database'
else:
    FILE_STORAGE = 'filesystem'
FILES_SERVED_BY_APP = FILE_STORAGE == 'database'
# O Vercel recusa requisições acima de ~4,5 MB; deixa margem para o formulário.
MAX_UPLOAD_BYTES = (4 if DEPLOYED_ON_VERCEL else 15) * 1024 * 1024
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_FILE_STORAGE_OPTIONS = {
    'r2': {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            **R2_STORAGE_SETTINGS,
            'region_name': 'auto',
            'default_acl': None,
            'querystring_auth': True,
            'file_overwrite': False,
        },
    },
    'database': {'BACKEND': 'core.storage.DatabaseStorage'},
    'filesystem': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}
STORAGES = {
    'default': DEFAULT_FILE_STORAGE_OPTIONS[FILE_STORAGE],
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/entrar/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/entrar/'
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31_536_000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_TRUSTED_ORIGINS = []
for origin in (
    os.environ.get('RENDER_EXTERNAL_HOSTNAME'),
    *VERCEL_HOSTS,
    'https://*.ethiodeploy.app' if DEPLOYED_ON_ETHIODEPLOY else None,
    *os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(','),
):
    if origin and origin.strip():
        origin = origin.strip()
        CSRF_TRUSTED_ORIGINS.append(
            origin if '://' in origin else f'https://{origin}'
        )
