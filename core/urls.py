from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("buscar/", views.buscar, name="buscar"),
    path("propriedades/", views.propriedades, name="propriedades"),
    path("talhoes/", views.talhoes, name="talhoes"),
    path("insumos/", views.insumos, name="insumos"),
    path("atividades/", views.atividades, name="atividades"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("perfil/", views.perfil, name="perfil"),
    path("documentos/", views.documentos, name="documentos"),
    path(
        "documentos/<int:documento_id>/baixar/",
        views.download_documento,
        name="download_documento",
    ),
    path("entrar/", views.login_view, name="login"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("sair/", views.logout_view, name="logout"),
]
