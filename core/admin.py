from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Atividade,
    DocumentoPropriedade,
    Insumo,
    PerfilUsuario,
    Propriedade,
    Talhao,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'foto')
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(Propriedade)
class PropriedadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'proprietario', 'municipio', 'area_hectares')
    list_filter = ('municipio',)
    search_fields = ('nome', 'municipio', 'proprietario__username', 'proprietario__email')


@admin.register(Talhao)
class TalhaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'propriedade', 'cultura', 'area_hectares')
    search_fields = ('nome', 'cultura', 'propriedade__nome', 'propriedade__proprietario__username')


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'proprietario', 'categoria', 'quantidade', 'unidade')
    list_filter = ('categoria',)
    search_fields = ('nome', 'proprietario__username', 'proprietario__email')


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('data', 'tipo', 'proprietario', 'propriedade', 'talhao', 'cultura')
    list_filter = ('tipo', 'data')
    search_fields = (
        'proprietario__username',
        'proprietario__email',
        'propriedade',
        'talhao',
        'cultura',
    )
    date_hierarchy = 'data'


@admin.register(DocumentoPropriedade)
class DocumentoPropriedadeAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'categoria',
        'propriedade',
        'proprietario',
        'enviado_em',
        'baixar_arquivo',
    )
    list_filter = ('categoria', 'enviado_em')
    search_fields = (
        'titulo',
        'numero',
        'propriedade__nome',
        'propriedade__proprietario__username',
        'propriedade__proprietario__email',
    )
    readonly_fields = ('enviado_em', 'baixar_arquivo')
    formfield_overrides = {
        models.FileField: {'widget': forms.FileInput},
    }

    @admin.display(description='Proprietário', ordering='propriedade__proprietario__username')
    def proprietario(self, obj):
        return obj.propriedade.proprietario

    @admin.display(description='Arquivo')
    def baixar_arquivo(self, obj):
        if not obj or not obj.arquivo:
            return 'Salve o documento para disponibilizar o download.'
        url = reverse('core:download_documento', args=(obj.pk,))
        return format_html('<a href="{}">Baixar arquivo</a>', url)
