from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Atividade, Insumo, Propriedade, Talhao


class AgroDadosFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='produtor', password='senha-forte-123')
        self.other_user = User.objects.create_user(username='outra-conta', password='senha-forte-456')
        self.property = Propriedade.objects.create(
            proprietario=self.user,
            nome='Fazenda Verde',
            municipio='Goiânia, GO',
            area_hectares=Decimal('100.00'),
            cultura_principal='Soja',
        )
        self.client.force_login(self.user)

    def test_plot_registration_is_limited_to_owned_property_area(self):
        response = self.client.post(reverse('talhoes'), {
            'propriedade': self.property.pk,
            'nome': 'Talhão 01',
            'area': '60.50',
            'cultura': 'Soja',
        })
        self.assertRedirects(response, reverse('talhoes'))
        self.assertTrue(Talhao.objects.filter(propriedade=self.property, nome='Talhão 01').exists())

        self.client.post(reverse('talhoes'), {
            'propriedade': self.property.pk,
            'nome': 'Talhão 02',
            'area': '40',
            'cultura': 'Milho',
        })
        self.assertEqual(Talhao.objects.filter(propriedade=self.property).count(), 1)

    def test_plot_registration_rejects_another_users_property(self):
        other_property = Propriedade.objects.create(
            proprietario=self.other_user,
            nome='Propriedade privada',
            area_hectares=Decimal('20.00'),
        )
        self.client.post(reverse('talhoes'), {
            'propriedade': other_property.pk,
            'nome': 'Talhão indevido',
            'area': '5',
            'cultura': 'Soja',
        })
        self.assertFalse(Talhao.objects.filter(propriedade=other_property).exists())

    def test_dashboard_uses_registered_plot_count(self):
        Talhao.objects.create(propriedade=self.property, nome='Talhão 01', area_hectares=Decimal('10.00'))
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['plot_count'], 1)

    def test_report_chart_uses_real_activity_counts(self):
        Atividade.objects.create(
            proprietario=self.user,
            data=date.today(),
            propriedade=self.property.nome,
            talhao='Talhão 01',
            cultura='Soja',
            tipo='Plantio',
            responsavel='Produtor',
        )
        response = self.client.get(reverse('relatorios'))
        chart_items = {item['value']: item for item in response.context['activity_types']}
        self.assertEqual(chart_items['Plantio']['count'], 1)
        self.assertEqual(chart_items['Plantio']['width'], 100)

    def test_registration_and_login_pages_render(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.assertEqual(self.client.get(reverse('cadastro')).status_code, 200)

    def test_create_property_input_and_activity(self):
        response = self.client.post(reverse('propriedades'), {
            'nome': 'Fazenda Nova',
            'municipio': 'Anápolis, GO',
            'area': '25.50',
            'responsavel': 'Produtor',
            'cultura': 'Milho',
        })
        self.assertRedirects(response, reverse('propriedades'))

        response = self.client.post(reverse('insumos'), {
            'nome': 'Semente certificada',
            'categoria': 'Semente',
            'quantidade': '10',
            'unidade': 'kg',
            'observacoes': '',
        })
        self.assertRedirects(response, reverse('insumos'))
        self.assertTrue(Insumo.objects.filter(proprietario=self.user, nome='Semente certificada').exists())

        response = self.client.post(reverse('atividades'), {
            'data': date.today().isoformat(),
            'tipo': 'Plantio',
            'propriedade': self.property.nome,
            'talhao': 'Talhão 01',
            'cultura': 'Soja',
            'produto': 'Semente certificada',
            'quantidade': '10 kg',
            'responsavel': 'Produtor',
            'observacoes': '',
        })
        self.assertRedirects(response, reverse('atividades'))
        self.assertTrue(Atividade.objects.filter(proprietario=self.user, propriedade=self.property.nome).exists())

    def test_all_authenticated_pages_render(self):
        for name in ('dashboard', 'propriedades', 'talhoes', 'insumos', 'atividades', 'relatorios', 'perfil'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_registration_creates_account_and_logs_in(self):
        self.client.logout()
        response = self.client.post(reverse('cadastro'), {
            'username': 'nova-conta',
            'email': 'nova@example.com',
            'password': 'senha-com-oito',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='nova-conta').exists())
        self.assertTrue('_auth_user_id' in self.client.session)
