from django.contrib import admin
from .models import Propriedade, Talhao, Insumo, Atividade
admin.site.register(Propriedade)
admin.site.register(Talhao)
admin.site.register(Insumo)
admin.site.register(Atividade)
