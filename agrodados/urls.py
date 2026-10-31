from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # Nomes sem namespace, usados por templates e redirecionamentos.
    path('', views.dashboard, name='dashboard'),
    path('propriedades/', views.propriedades, name='propriedades'),
    path('talhoes/', views.talhoes, name='talhoes'),
    path('insumos/', views.insumos, name='insumos'),
    path('atividades/', views.atividades, name='atividades'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('perfil/', views.perfil, name='perfil'),
    path('documentos/', views.documentos, name='documentos'),
    path('entrar/', views.login_view, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('sair/', views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.FILES_SERVED_BY_APP:
    urlpatterns += [
        re_path(r'^media/(?P<caminho>.+)$', views.media_arquivo, name='media_arquivo'),
    ]
