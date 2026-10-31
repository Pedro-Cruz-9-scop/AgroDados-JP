import os

from django.core.exceptions import ImproperlyConfigured
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrodados.settings')

from django.conf import settings

if settings.DEPLOYMENT_ERRORS:
    raise ImproperlyConfigured(' '.join(settings.DEPLOYMENT_ERRORS))

application = get_wsgi_application()

# Modo de teste no Vercel (ALLOW_EPHEMERAL_STORAGE=1 sem DATABASE_URL): o SQLite em /tmp
# começa vazio a cada instância, então as tabelas são criadas na inicialização.
if settings.DEPLOYED_ON_VERCEL and not settings.DATABASE_URL:
    from django.core.management import call_command

    call_command('migrate', interactive=False, verbosity=0)
