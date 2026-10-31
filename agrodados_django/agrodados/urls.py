from django.contrib import admin
from django.urls import path
from core import views
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("propriedades/", views.propriedades, name="propriedades"),
    path("talhoes/", views.talhoes, name="talhoes"),
    path("insumos/", views.insumos, name="insumos"),
    path("atividades/", views.atividades, name="atividades"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("perfil/", views.perfil, name="perfil"),
    path("entrar/", views.login_view, name="login"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("sair/", views.logout_view, name="logout"),
]
