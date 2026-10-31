import mimetypes
import posixpath

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """Guarda os arquivos enviados no próprio banco de dados da aplicação.

    Serve para hospedagens sem disco persistente (ex.: Vercel): os arquivos
    ficam junto dos demais dados e são entregues pela rota ``/media/``.
    """

    def _model(self):
        from core.models import ArquivoArmazenado

        return ArquivoArmazenado

    def _open(self, name, mode='rb'):
        try:
            registro = self._model().objects.get(nome=name)
        except self._model().DoesNotExist as exc:
            raise FileNotFoundError(name) from exc
        return ContentFile(bytes(registro.conteudo), name=name)

    def _save(self, name, content):
        name = name.replace('\\', '/')
        content.seek(0)
        self._model().objects.update_or_create(
            nome=name,
            defaults={
                'conteudo': content.read(),
                'tipo_conteudo': mimetypes.guess_type(name)[0] or 'application/octet-stream',
            },
        )
        return name

    def exists(self, name):
        return self._model().objects.filter(nome=name).exists()

    def delete(self, name):
        self._model().objects.filter(nome=name).delete()

    def size(self, name):
        return len(self._open(name).read())

    def url(self, name):
        from django.conf import settings

        return posixpath.join(settings.MEDIA_URL, name)

    def get_available_name(self, name, max_length=None):
        return super().get_available_name(name.replace('\\', '/'), max_length)
