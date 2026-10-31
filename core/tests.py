from datetime import date
from decimal import Decimal
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Atividade, DocumentoPropriedade, Insumo, Propriedade, Talhao


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
            f"{reverse('core:documentos')}?propriedade={self.property.pk}",
        )
        self.assertContains(
            response,
            f"{reverse('core:atividades')}?propriedade=Fazenda%20Boa%20Vista",
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

                self.client.force_login(other_user)
                self.assertEqual(self.client.get(url).status_code, 404)

                self.client.logout()
                self.assertRedirects(
                    self.client.get(url),
                    f'{reverse("core:login")}?next={url}',
                )

    def test_map_saves_field_boundaries_and_calculates_area(self):
        response = self.client.post(
            reverse('core:talhoes'),
            {
                'action': 'save',
                'propriedade': self.property.pk,
                'nome': 'Talhão Norte',
                'cultura': 'Soja',
                'limites': (
                    '[[-13.85,-40.08],[-13.85,-40.07],'
                    '[-13.86,-40.07],[-13.86,-40.08]]'
                ),
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
            reverse('core:talhoes'),
            {'action': 'delete', 'talhao': other_field.pk},
        )

        self.assertRedirects(response, reverse('core:talhoes'))
        self.assertTrue(Talhao.objects.filter(pk=own_field.pk).exists())
        self.assertTrue(Talhao.objects.filter(pk=other_field.pk).exists())

        self.client.post(
            reverse('core:talhoes'),
            {'action': 'delete', 'talhao': own_field.pk},
        )
        self.assertFalse(Talhao.objects.filter(pk=own_field.pk).exists())

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
