from django.contrib import admin
from .models import Talhao


admin.site.register(Talhao)
from .models import Propriedade, Insumo, Atividade
admin.site.register(Propriedade)
admin.site.register(Insumo)
admin.site.register(Atividade)
