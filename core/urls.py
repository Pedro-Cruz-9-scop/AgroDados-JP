from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('buscar/', views.buscar, name='buscar'),
    path('propriedades/', views.propriedades, name='propriedades'),
    path('talhoes/', views.talhoes, name='talhoes'),
    path('insumos/', views.insumos, name='insumos'),
    path('insumos/<int:insumo_id>/excluir/', views.excluir_insumo, name='excluir_insumo'),
    path(
        'propriedades/<int:propriedade_id>/excluir/',
        views.excluir_propriedade,
        name='excluir_propriedade',
    ),
    path('talhoes/<int:talhao_id>/excluir/', views.excluir_talhao, name='excluir_talhao'),
    path(
        'atividades/<int:atividade_id>/excluir/', views.excluir_atividade, name='excluir_atividade'
    ),
    path('atividades/', views.atividades, name='atividades'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('perfil/', views.perfil, name='perfil'),
    path('documentos/', views.documentos, name='documentos'),
    path(
        'documentos/<int:documento_id>/baixar/',
        views.download_documento,
        name='download_documento',
    ),
    path(
        'documentos/<int:documento_id>/excluir/',
        views.excluir_documento,
        name='excluir_documento',
    ),
    path('entrar/', views.login_view, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('sair/', views.logout_view, name='logout'),
]
