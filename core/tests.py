import tempfile
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import (
    Atividade,
    DocumentoPropriedade,
    Insumo,
    PerfilUsuario,
    Propriedade,
    Talhao,
)


class ApplicationNavigationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='agro-teste',
            password='senha-de-teste-123',
        )
        self.client.force_login(self.user)
        self.property = Propriedade.objects.create(
            proprietario=self.user,
            nome='Fazenda Boa Vista',
            municipio='Jequié, BA',
            area_hectares=Decimal('12.50'),
            cultura_principal='Soja',
        )

    def test_application_pages_open_for_authenticated_user(self):
        paths = [
            reverse('core:dashboard'),
            reverse('core:propriedades'),
            reverse('core:talhoes'),
            reverse('core:insumos'),
            reverse('core:atividades'),
            reverse('core:relatorios'),
            reverse('core:perfil'),
            reverse('core:documentos'),
            reverse('core:buscar'),
        ]

        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_dashboard_links_to_every_application_module(self):
        response = self.client.get(reverse('core:dashboard'))

        for route_name in [
            'core:propriedades',
            'core:talhoes',
            'core:insumos',
            'core:atividades',
            'core:documentos',
            'core:relatorios',
            'core:perfil',
            'core:buscar',
        ]:
            with self.subTest(route=route_name):
                self.assertContains(response, reverse(route_name))

    def test_agricultural_photos_and_shared_visual_theme_are_loaded(self):
        dashboard = self.client.get(reverse('core:dashboard'))
        self.assertContains(dashboard, 'css/refresh.css')
        self.assertContains(dashboard, 'img/plantacao-campos.jpg')
        self.assertContains(dashboard, 'Johny Goerend')

        self.client.logout()
        login_page = self.client.get(reverse('core:login'))
        self.assertContains(login_page, 'css/refresh.css')
        self.assertContains(login_page, 'Referência: Agro 5.0')
        self.assertContains(login_page, 'https://networdagro.com.br/blog/agro-5-0/')

        signup_page = self.client.get(reverse('core:cadastro'))
        self.assertContains(signup_page, 'Criar conta')
        self.assertContains(signup_page, 'Referência: Agro 5.0')

    def test_map_uses_an_in_map_layer_control(self):
        response = self.client.get(reverse('core:talhoes'))

        self.assertContains(response, 'id="agro-map"')
        self.assertContains(response, 'aria-label="Mapa interativo para desenhar talhões"')
        self.assertNotContains(response, 'map-layer-toggle')

    def test_each_page_loads_its_styles_and_required_scripts(self):
        assets_by_route = {
            'core:dashboard': ('css/pages/dashboard.css', 'js/pages/dashboard.js'),
            'core:propriedades': ('css/pages/propriedades.css',),
            'core:talhoes': ('css/pages/talhoes.css', 'js/pages/talhoes.js'),
            'core:insumos': ('css/pages/insumos.css',),
            'core:atividades': ('css/pages/atividades.css',),
            'core:documentos': ('css/pages/documentos.css', 'js/pages/documentos.js'),
            'core:relatorios': ('css/pages/relatorios.css', 'js/pages/relatorios.js'),
            'core:perfil': ('css/pages/perfil.css', 'js/pages/perfil.js'),
        }
        for route_name, assets in assets_by_route.items():
            response = self.client.get(reverse(route_name))
            for asset in assets:
                with self.subTest(route=route_name, asset=asset):
                    self.assertContains(response, asset)

    def test_profile_update_changes_only_the_authenticated_user(self):
        response = self.client.post(
            reverse('core:perfil'),
            {'username': 'agro-atualizado', 'email': 'agro@example.com'},
        )

        self.assertRedirects(response, reverse('core:perfil'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'agro-atualizado')
        self.assertEqual(self.user.email, 'agro@example.com')

    def test_profile_rejects_an_existing_username(self):
        other_user = User.objects.create_user(
            username='nome-ja-usado',
            password='senha-de-teste-456',
        )

        response = self.client.post(
            reverse('core:perfil'),
            {'username': other_user.username, 'email': 'new@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'agro-teste')
        self.assertEqual(self.user.email, '')

    def test_profile_photo_upload_is_displayed_in_profile_and_account_avatars(self):
        image_buffer = BytesIO()
        Image.new('RGB', (32, 32), color='green').save(image_buffer, format='PNG')

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse('core:perfil'),
                    {
                        'acao': 'foto',
                        'foto': SimpleUploadedFile(
                            'foto-perfil.png',
                            image_buffer.getvalue(),
                            content_type='image/png',
                        ),
                    },
                )

                self.assertRedirects(response, reverse('core:perfil'))
                user_profile = PerfilUsuario.objects.get(usuario=self.user)
                self.assertTrue(user_profile.foto.name.startswith('fotos_perfil/'))
                self.assertTrue(user_profile.foto.storage.exists(user_profile.foto.name))

                profile_page = self.client.get(reverse('core:perfil'))
                self.assertContains(profile_page, user_profile.foto.url)
                self.assertContains(profile_page, 'Foto de perfil')
                self.assertContains(profile_page, 'Remover foto')

                dashboard_page = self.client.get(reverse('core:dashboard'))
                self.assertContains(dashboard_page, user_profile.foto.url)

    def test_profile_rejects_non_image_upload(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse('core:perfil'),
                    {
                        'acao': 'foto',
                        'foto': SimpleUploadedFile(
                            'foto.png',
                            b'not an image',
                            content_type='image/png',
                        ),
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'imagem')
        self.assertFalse(PerfilUsuario.objects.get(usuario=self.user).foto)

    def test_profile_photo_can_be_removed(self):
        image_buffer = BytesIO()
        Image.new('RGB', (32, 32), color='blue').save(image_buffer, format='PNG')

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                user_profile = PerfilUsuario.objects.create(usuario=self.user)
                user_profile.foto.save(
                    'foto-perfil.png',
                    SimpleUploadedFile(
                        'foto-perfil.png', image_buffer.getvalue(), content_type='image/png'
                    ),
                )
                photo_name = user_profile.foto.name

                response = self.client.post(
                    reverse('core:perfil'),
                    {
                        'acao': 'foto',
                        'remover_foto': '1',
                    },
                )

                self.assertRedirects(response, reverse('core:perfil'))
                user_profile.refresh_from_db()
                self.assertFalse(user_profile.foto)
                self.assertFalse(user_profile.foto.storage.exists(photo_name))

    def test_reports_show_real_data_tables_and_supported_report_types(self):
        response = self.client.get(reverse('core:relatorios'))

        self.assertContains(response, 'value="activities"')
        self.assertContains(response, 'value="inputs"')
        self.assertContains(response, 'value="properties"')
        self.assertContains(response, 'data-report-table="activities"')
        self.assertContains(response, 'data-report-table="inputs"')
        self.assertContains(response, 'data-report-table="properties"')
        self.assertContains(response, 'js/pages/relatorios.js')

    def test_inventory_and_activity_links_apply_account_scoped_filters(self):
        own_input = Insumo.objects.create(
            proprietario=self.user,
            nome='Adubo especial',
            categoria='Fertilizante',
            quantidade=50,
            unidade='kg',
        )
        Atividade.objects.create(
            proprietario=self.user,
            data=date(2026, 10, 1),
            propriedade=self.property.nome,
            talhao='Talhão Norte',
            cultura='Soja',
            tipo='Plantio',
            produto=own_input.nome,
            responsavel='Equipe de campo',
        )
        other_user = User.objects.create_user(
            username='inventario-de-outra-conta',
            password='senha-de-teste-789',
        )
        Insumo.objects.create(
            proprietario=other_user,
            nome='Adubo especial privado',
            categoria='Fertilizante',
            quantidade=1,
        )

        inventory_response = self.client.get(
            reverse('core:insumos'),
            {'q': 'Adubo especial'},
        )
        self.assertContains(inventory_response, 'Adubo especial')
        self.assertNotContains(inventory_response, 'Adubo especial privado')

        activity_response = self.client.get(
            reverse('core:atividades'),
            {'produto': own_input.nome, 'propriedade': self.property.nome},
        )
        self.assertEqual(len(activity_response.context['activities']), 1)
        self.assertContains(activity_response, 'Talhão Norte')

    def test_global_search_only_returns_the_current_users_records(self):
        Insumo.objects.create(
            proprietario=self.user,
            nome='Semente de soja',
            categoria='Semente',
            quantidade=10,
            unidade='kg',
        )
        Atividade.objects.create(
            proprietario=self.user,
            data=date(2026, 10, 1),
            propriedade=self.property.nome,
            talhao='Talhão Norte',
            cultura='Soja',
            tipo='Plantio',
            responsavel='Equipe de campo',
        )
        other_user = User.objects.create_user(
            username='outro-agricultor',
            password='senha-de-teste-456',
        )
        Propriedade.objects.create(
            proprietario=other_user,
            nome='Fazenda Boa Vista de Outro',
        )

        response = self.client.get(reverse('core:buscar'), {'q': 'Boa Vista'})

        self.assertContains(response, 'Fazenda Boa Vista')
        self.assertNotContains(response, 'Fazenda Boa Vista de Outro')

    def test_property_links_open_filtered_documents_and_activity_form(self):
        response = self.client.get(reverse('core:propriedades'))

        self.assertContains(
            response,
            f'{reverse("core:documentos")}?propriedade={self.property.pk}',
        )
        self.assertContains(
            response,
            f'{reverse("core:atividades")}?propriedade=Fazenda%20Boa%20Vista',
        )

        activity_response = self.client.get(
            reverse('core:atividades'),
            {'propriedade': self.property.nome},
        )
        self.assertContains(
            activity_response,
            f'value="{self.property.nome}"',
        )

    def test_document_page_filters_to_the_selected_property(self):
        other_property = Propriedade.objects.create(
            proprietario=self.user,
            nome='Fazenda Secundária',
        )
        first_document = DocumentoPropriedade.objects.create(
            propriedade=self.property,
            categoria='CAR',
            titulo='CAR Boa Vista',
            arquivo='documentos/car-boa-vista.pdf',
        )
        DocumentoPropriedade.objects.create(
            propriedade=other_property,
            categoria='CCIR',
            titulo='CCIR Secundária',
            arquivo='documentos/ccir-secundaria.pdf',
        )

        response = self.client.get(
            reverse('core:documentos'),
            {'propriedade': self.property.pk},
        )

        self.assertEqual(list(response.context['documents']), [first_document])
        self.assertEqual(response.context['selected_property'], self.property)

    def test_document_categories_have_distinct_identification_logos(self):
        categories = ['CAR', 'CCIR', 'ITR', 'Comodato', 'Escritura', 'Outro']
        for category in categories:
            DocumentoPropriedade.objects.create(
                propriedade=self.property,
                categoria=category,
                titulo=f'Documento {category}',
                arquivo=f'documentos/{category.lower()}.pdf',
            )

        response = self.client.get(reverse('core:documentos'))

        self.assertContains(response, 'data-document-category-select')
        self.assertContains(response, 'data-document-category-preview')
        self.assertContains(response, 'class="activity-list document-grid"')
        self.assertContains(response, 'class="activity-row document-card"')
        self.assertContains(response, 'class="document-actions"')
        self.assertContains(response, 'data-logo-zoom')
        self.assertContains(response, 'aria-haspopup="dialog"')
        self.assertContains(response, 'data-logo-lightbox')
        self.assertContains(response, 'data-logo-lightbox-image')
        self.assertContains(response, 'data-open-delete')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertContains(response, 'data-logo-src-car="/static/img/logo-car.png?v=2"')
        self.assertContains(response, 'alt="Logo do CAR"')
        self.assertContains(response, 'data-logo-src-ccir="/static/img/logo-ccir.png"')
        self.assertContains(response, 'alt="Logo do CCIR"')
        self.assertContains(response, 'data-logo-src-comodato="/static/img/logo-comodato.png"')
        self.assertContains(response, 'alt="Logo do Comodato"')
        self.assertContains(response, 'data-logo-src-escritura="/static/img/logo-escritura.png"')
        self.assertContains(response, 'alt="Logo da Escritura"')
        self.assertContains(response, 'data-logo-src-itr="/static/img/logo-itr.png"')
        self.assertContains(response, 'alt="Logo do ITR"')
        self.assertContains(response, 'data-logo-src-outro="/static/img/logo-outro.png"')
        self.assertContains(response, 'alt="Logo OUT"')
        for category in categories:
            with self.subTest(category=category):
                self.assertContains(response, f'data-document-category="{category}"')
        self.assertContains(response, 'document-type-logo--car')
        self.assertContains(response, 'document-type-logo--ccir')
        self.assertContains(response, 'document-type-logo--itr')
        self.assertContains(response, 'document-type-logo--comodato')
        self.assertContains(response, 'document-type-logo--escritura')
        self.assertContains(response, 'document-type-logo--outro')

    def test_document_download_requires_an_authenticated_owner(self):
        other_user = User.objects.create_user(
            username='dono-do-documento',
            password='senha-de-teste-789',
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                document = DocumentoPropriedade.objects.create(
                    propriedade=self.property,
                    categoria='CAR',
                    titulo='CAR Boa Vista',
                    arquivo=SimpleUploadedFile(
                        'car.pdf',
                        b'%PDF-1.4 test document',
                        content_type='application/pdf',
                    ),
                )
                url = reverse(
                    'core:download_documento',
                    kwargs={'documento_id': document.pk},
                )

                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 test document')
                self.assertIn('attachment;', response['Content-Disposition'])
                self.assertEqual(self.client.get(document.arquivo.url).status_code, 404)

                self.client.force_login(other_user)
                self.assertEqual(self.client.get(url).status_code, 404)

                self.client.logout()
                self.assertRedirects(
                    self.client.get(url),
                    f'{reverse("core:login")}?next={url}',
                )

                admin_user = User.objects.create_superuser(
                    username='administrador',
                    email='admin@example.com',
                    password='senha-de-administrador-123',
                )
                self.client.force_login(admin_user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 test document')

    def _create_input(self, user=None):
        return Insumo.objects.create(
            proprietario=user or self.user,
            nome='Adubo para excluir',
            categoria='Fertilizante',
            quantidade=10,
            unidade='kg',
        )

    def test_input_owner_can_delete_with_correct_password(self):
        item = self._create_input()
        response = self.client.post(
            reverse('core:excluir_insumo', args=[item.pk]),
            {'password': 'senha-de-teste-123'},
        )
        self.assertRedirects(response, reverse('core:insumos'))
        self.assertFalse(Insumo.objects.filter(pk=item.pk).exists())

    def test_input_is_kept_with_wrong_password_get_or_other_user(self):
        item = self._create_input()
        url = reverse('core:excluir_insumo', args=[item.pk])
        self.client.post(url, {'password': 'errada'})
        self.assertTrue(Insumo.objects.filter(pk=item.pk).exists())
        self.assertEqual(self.client.get(url).status_code, 405)

        other = User.objects.create_user(username='outro', password='outra-senha-123')
        self.client.force_login(other)
        response = self.client.post(url, {'password': 'outra-senha-123'})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Insumo.objects.filter(pk=item.pk).exists())

    def test_document_owner_can_delete_document_and_uploaded_file(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                document = DocumentoPropriedade.objects.create(
                    propriedade=self.property,
                    categoria='CAR',
                    titulo='CAR para excluir',
                    arquivo=SimpleUploadedFile(
                        'car-para-excluir.pdf',
                        b'%PDF-1.4 test document',
                        content_type='application/pdf',
                    ),
                )
                file_path = document.arquivo.path
                url = reverse(
                    'core:excluir_documento',
                    kwargs={'documento_id': document.pk},
                )

                response = self.client.post(
                    url,
                    {'password': 'senha-de-teste-123'},
                )

                self.assertRedirects(response, reverse('core:documentos'))
                self.assertFalse(DocumentoPropriedade.objects.filter(pk=document.pk).exists())
                self.assertFalse(Path(file_path).exists())

    def test_document_cannot_be_deleted_by_another_user_or_with_get(self):
        other_user = User.objects.create_user(
            username='nao-dono-do-documento',
            password='senha-de-teste-789',
        )
        document = DocumentoPropriedade.objects.create(
            propriedade=self.property,
            categoria='CAR',
            titulo='CAR protegido',
            arquivo='documentos/car-protegido.pdf',
        )
        url = reverse(
            'core:excluir_documento',
            kwargs={'documento_id': document.pk},
        )

        self.assertEqual(self.client.get(url).status_code, 405)

        wrong_password_response = self.client.post(
            url,
            {'password': 'senha-incorreta'},
        )
        self.assertRedirects(wrong_password_response, reverse('core:documentos'))
        self.assertTrue(DocumentoPropriedade.objects.filter(pk=document.pk).exists())
        self.assertTrue(
            any(
                'Senha incorreta' in str(message)
                for message in wrong_password_response.wsgi_request._messages
            )
        )

        self.client.force_login(other_user)
        self.assertEqual(
            self.client.post(url, {'password': 'senha-de-teste-123'}).status_code,
            404,
        )
        self.assertTrue(DocumentoPropriedade.objects.filter(pk=document.pk).exists())

        self.client.logout()
        self.assertRedirects(
            self.client.post(url, {'password': 'senha-de-teste-123'}),
            f'{reverse("core:login")}?next={url}',
        )

    def test_only_admins_can_see_all_records_in_the_admin_panel(self):
        other_user = User.objects.create_user(
            username='outra-conta',
            email='outra@example.com',
            password='senha-de-teste-789',
        )
        other_property = Propriedade.objects.create(
            proprietario=other_user,
            nome='Fazenda de outra conta',
        )
        Talhao.objects.create(
            propriedade=other_property,
            nome='Talhão de outra conta',
            area_hectares=Decimal('2.00'),
            limites=[[-13.85, -40.08], [-13.85, -40.07], [-13.86, -40.07]],
        )
        Insumo.objects.create(
            proprietario=other_user,
            nome='Insumo de outra conta',
            categoria='Fertilizante',
            quantidade=10,
        )
        Atividade.objects.create(
            proprietario=other_user,
            data=date(2026, 10, 1),
            propriedade=other_property.nome,
            talhao='Talhão de outra conta',
            cultura='Milho',
            tipo='Plantio',
            responsavel='Equipe externa',
        )
        DocumentoPropriedade.objects.create(
            propriedade=other_property,
            categoria='CAR',
            titulo='Documento de outra conta',
            arquivo='documentos/privado.pdf',
        )
        admin_path = reverse('admin:core_propriedade_changelist')

        response = self.client.get(admin_path)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response['Location'])

        admin_user = User.objects.create_superuser(
            username='administrador',
            email='admin@example.com',
            password='senha-de-administrador-123',
        )
        self.client.force_login(admin_user)

        admin_lists = (
            ('propriedade', 'Fazenda de outra conta'),
            ('talhao', 'Talhão de outra conta'),
            ('insumo', 'Insumo de outra conta'),
            ('atividade', 'Fazenda de outra conta'),
            ('documentopropriedade', 'Documento de outra conta'),
        )
        for model_name, record in admin_lists:
            with self.subTest(model=model_name):
                response = self.client.get(reverse(f'admin:core_{model_name}_changelist'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, record)

        response = self.client.get(reverse('admin:auth_user_changelist'))
        self.assertContains(response, other_user.email)

        response = self.client.get(admin_path)
        self.assertContains(response, self.property.nome)
        self.assertContains(response, other_property.nome)

        response = self.client.get(reverse('core:propriedades'))
        self.assertContains(response, self.property.nome)
        self.assertNotContains(response, other_property.nome)

    def test_map_saves_field_boundaries_and_calculates_area(self):
        response = self.client.post(
            reverse('core:talhoes'),
            {
                'action': 'save',
                'propriedade': self.property.pk,
                'nome': 'Talhão Norte',
                'cultura': 'Soja',
                'limites': ('[[-13.85,-40.08],[-13.85,-40.07],[-13.86,-40.07],[-13.86,-40.08]]'),
            },
        )

        self.assertRedirects(response, reverse('core:talhoes'))
        field = Talhao.objects.get(nome='Talhão Norte')
        self.assertEqual(field.propriedade, self.property)
        self.assertEqual(field.cultura, 'Soja')
        self.assertGreater(field.area_hectares, 0)
        self.assertEqual(len(field.limites), 4)

    def test_map_guides_user_to_create_a_property_when_none_exists(self):
        self.property.delete()

        response = self.client.get(reverse('core:talhoes'))

        self.assertContains(
            response,
            'Cadastre uma propriedade para habilitar o desenho e salvar talhões no mapa.',
        )
        self.assertContains(
            response,
            f'href="{reverse("core:propriedades")}"',
        )
        self.assertContains(response, 'id="startDrawing" disabled')

    def test_map_offers_world_view_and_place_search(self):
        response = self.client.get(reverse('core:talhoes'))

        self.assertContains(response, 'id="showWorld"')
        self.assertContains(response, 'id="placeSearchForm"')
        self.assertContains(response, 'placeholder="Ex.: Lisboa, Portugal"')
        self.assertContains(response, 'talhoes.js?v=4')

    def test_map_rejects_invalid_and_other_users_property_ids(self):
        other_user = User.objects.create_user(
            username='outro-proprietario',
            password='senha-de-teste-789',
        )
        other_property = Propriedade.objects.create(
            proprietario=other_user,
            nome='Propriedade privada',
        )
        response = self.client.post(
            reverse('core:talhoes'),
            {
                'action': 'save',
                'propriedade': other_property.pk,
                'nome': 'Talhão indevido',
                'limites': '[[0,0],[0,1],[1,1]]',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecione uma propriedade da sua conta.')
        self.assertFalse(Talhao.objects.exists())

        response = self.client.post(
            reverse('core:talhoes'),
            {
                'action': 'save',
                'propriedade': self.property.pk,
                'nome': 'Talhão inválido',
                'limites': '[[91,0],[0,1],[1,1]]',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'O limite do talhão contém coordenadas inválidas.')
        self.assertFalse(Talhao.objects.exists())

    def test_map_deletion_only_removes_fields_from_the_current_users_account(self):
        own_field = Talhao.objects.create(
            propriedade=self.property,
            nome='Talhão Norte',
            cultura='Soja',
            area_hectares=Decimal('12.34'),
            limites=[[-13.85, -40.08], [-13.85, -40.07], [-13.86, -40.07]],
        )
        other_user = User.objects.create_user(
            username='proprietario-de-outro-talhao',
            password='senha-de-teste-999',
        )
        other_property = Propriedade.objects.create(
            proprietario=other_user,
            nome='Fazenda de outra conta',
        )
        other_field = Talhao.objects.create(
            propriedade=other_property,
            nome='Talhão protegido',
            area_hectares=Decimal('1.00'),
            limites=[[-13.85, -40.08], [-13.85, -40.07], [-13.86, -40.07]],
        )

        response = self.client.post(
            reverse('core:excluir_talhao', args=[other_field.pk]),
            {'password': 'senha-de-teste-123'},
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Talhao.objects.filter(pk=own_field.pk).exists())
        self.assertTrue(Talhao.objects.filter(pk=other_field.pk).exists())

        own_url = reverse('core:excluir_talhao', args=[own_field.pk])
        self.client.post(own_url, {'password': 'errada'})
        self.assertTrue(Talhao.objects.filter(pk=own_field.pk).exists())
        self.client.post(own_url, {'password': 'senha-de-teste-123'})
        self.assertFalse(Talhao.objects.filter(pk=own_field.pk).exists())

    def test_property_and_activity_need_password_to_be_deleted(self):
        activity = Atividade.objects.create(
            proprietario=self.user,
            data=date(2026, 10, 1),
            propriedade=self.property.nome,
            talhao='T1',
            cultura='Soja',
            tipo='Plantio',
            responsavel='Ana',
        )
        cases = [
            (reverse('core:excluir_atividade', args=[activity.pk]), Atividade, activity.pk),
            (
                reverse('core:excluir_propriedade', args=[self.property.pk]),
                Propriedade,
                self.property.pk,
            ),
        ]
        for url, model, pk in cases:
            self.assertEqual(self.client.get(url).status_code, 405)
            self.client.post(url, {'password': 'errada'})
            self.assertTrue(model.objects.filter(pk=pk).exists())
            self.client.post(url, {'password': 'senha-de-teste-123'})
            self.assertFalse(model.objects.filter(pk=pk).exists())

    def test_logout_clears_session_and_allows_login_with_another_account(self):
        self.assertContains(
            self.client.get(reverse('core:dashboard')),
            'Sair da conta',
        )
        other_user = User.objects.create_user(
            username='segundo-acesso',
            password='outra-senha-segura-123',
        )

        logout_response = self.client.post(reverse('core:logout'))
        self.assertRedirects(logout_response, reverse('core:login'))
        self.assertRedirects(
            self.client.get(reverse('core:dashboard')),
            reverse('core:login'),
        )

        login_response = self.client.post(
            reverse('core:login'),
            {'username': other_user.username, 'password': 'outra-senha-segura-123'},
        )
        self.assertRedirects(login_response, reverse('core:dashboard'))
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            other_user.pk,
        )

    def test_login_screen_does_not_link_to_an_unavailable_demo_dashboard(self):
        self.client.logout()

        response = self.client.get(reverse('core:login'))

        self.assertContains(response, 'Ainda não tem acesso? Criar conta')
        self.assertNotContains(response, 'use o painel sem login')
