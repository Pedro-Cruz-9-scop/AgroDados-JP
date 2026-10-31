from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from . import views
from .models import ArquivoArmazenado, DocumentoPropriedade, PerfilUsuario, Propriedade
from .storage import DatabaseStorage


class DatabaseStorageTests(TestCase):
    def setUp(self):
        self.storage = DatabaseStorage()

    def test_save_open_exists_size_and_delete(self):
        name = self.storage.save('documentos_propriedades/2026/01/car.pdf', ContentFile(b'%PDF-teste'))

        self.assertEqual(name, 'documentos_propriedades/2026/01/car.pdf')
        self.assertTrue(self.storage.exists(name))
        self.assertEqual(self.storage.open(name).read(), b'%PDF-teste')
        self.assertEqual(self.storage.size(name), 10)
        self.assertEqual(self.storage.url(name), '/media/documentos_propriedades/2026/01/car.pdf')

        self.storage.delete(name)
        self.assertFalse(self.storage.exists(name))

    def test_duplicate_names_do_not_overwrite(self):
        first = self.storage.save('fotos_perfil/a.png', ContentFile(b'1'))
        second = self.storage.save('fotos_perfil/a.png', ContentFile(b'2'))

        self.assertNotEqual(first, second)
        self.assertEqual(self.storage.open(first).read(), b'1')
        self.assertEqual(self.storage.open(second).read(), b'2')


class MediaViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = User.objects.create_user('dono', password='x')
        self.other = User.objects.create_user('outro', password='x')
        propriedade = Propriedade.objects.create(proprietario=self.owner, nome='Fazenda')
        ArquivoArmazenado.objects.create(
            nome='documentos_propriedades/2026/01/car.pdf',
            conteudo=b'%PDF-teste',
            tipo_conteudo='application/pdf',
        )
        ArquivoArmazenado.objects.create(
            nome='fotos_perfil/2026/01/foto.png', conteudo=b'png', tipo_conteudo='image/png'
        )
        DocumentoPropriedade.objects.create(
            propriedade=propriedade,
            categoria='CAR',
            titulo='CAR',
            arquivo='documentos_propriedades/2026/01/car.pdf',
        )
        PerfilUsuario.objects.create(usuario=self.owner, foto='fotos_perfil/2026/01/foto.png')

    def get(self, user, path):
        request = self.factory.get('/media/' + path)
        request.user = user
        return views.media_arquivo(request, path)

    def test_owner_receives_document_and_photo(self):
        document = self.get(self.owner, 'documentos_propriedades/2026/01/car.pdf')
        photo = self.get(self.owner, 'fotos_perfil/2026/01/foto.png')

        self.assertEqual(document.content, b'%PDF-teste')
        self.assertEqual(document['Content-Type'], 'application/pdf')
        self.assertEqual(photo.content, b'png')

    def test_other_users_cannot_read_files(self):
        for path in ('documentos_propriedades/2026/01/car.pdf', 'fotos_perfil/2026/01/foto.png'):
            with self.assertRaises(Http404):
                self.get(self.other, path)

    def test_unknown_and_traversal_paths_are_not_found(self):
        for path in ('outro/arquivo.txt', 'documentos_propriedades/../x'):
            with self.assertRaises(Http404):
                self.get(self.owner, path)

@override_settings(
    STORAGES={
        'default': {'BACKEND': 'core.storage.DatabaseStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
)
class DatabaseUploadFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('produtor', password='senha-forte-123')
        self.propriedade = Propriedade.objects.create(proprietario=self.user, nome='Sítio')
        self.client.force_login(self.user)

    def test_document_upload_is_stored_in_database_and_downloadable(self):
        response = self.client.post(
            reverse('core:documentos'),
            {
                'propriedade': self.propriedade.pk,
                'categoria': 'CAR',
                'titulo': 'CAR 2026',
                'arquivo': SimpleUploadedFile('car.pdf', b'%PDF-1.4 teste', content_type='application/pdf'),
            },
        )

        self.assertEqual(response.status_code, 302)
        documento = DocumentoPropriedade.objects.get()
        self.assertTrue(ArquivoArmazenado.objects.filter(nome=documento.arquivo.name).exists())

        download = self.client.get(reverse('core:download_documento', args=[documento.pk]))
        self.assertEqual(b''.join(download.streaming_content), b'%PDF-1.4 teste')

    def test_oversized_document_is_rejected(self):
        with override_settings(MAX_UPLOAD_BYTES=10):
            self.client.post(
                reverse('core:documentos'),
                {
                    'propriedade': self.propriedade.pk,
                    'categoria': 'CAR',
                    'arquivo': SimpleUploadedFile('car.pdf', b'x' * 11, content_type='application/pdf'),
                },
            )

        self.assertFalse(DocumentoPropriedade.objects.exists())
        self.assertFalse(ArquivoArmazenado.objects.exists())

    def test_deleting_document_removes_stored_file(self):
        self.client.post(
            reverse('core:documentos'),
            {
                'propriedade': self.propriedade.pk,
                'categoria': 'CAR',
                'arquivo': SimpleUploadedFile('car.pdf', b'%PDF-1.4', content_type='application/pdf'),
            },
        )
        documento = DocumentoPropriedade.objects.get()

        documento.arquivo.delete(save=False)

        self.assertFalse(ArquivoArmazenado.objects.exists())
