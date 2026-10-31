from django.conf import settings
from django.db import models


class Propriedade(models.Model):
    proprietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='propriedades')
    nome = models.CharField(max_length=120)
    municipio = models.CharField(max_length=120, blank=True)
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    responsavel = models.CharField(max_length=120, blank=True)
    cultura_principal = models.CharField(max_length=80, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'propriedade'
        verbose_name_plural = 'propriedades'

    def __str__(self):
        return self.nome


class Talhao(models.Model):
    propriedade = models.ForeignKey(Propriedade, on_delete=models.CASCADE, related_name='talhoes')
    nome = models.CharField(max_length=80)
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cultura = models.CharField(max_length=80, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['propriedade__nome', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['propriedade', 'nome'], name='unique_talhao_per_propriedade'),
        ]
        verbose_name = 'talhão'
        verbose_name_plural = 'talhões'

    def __str__(self):
        return f'{self.nome} — {self.propriedade.nome}'


class Insumo(models.Model):
    proprietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insumos')
    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=80)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidade = models.CharField(max_length=20, default='kg')
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Atividade(models.Model):
    TIPO = [
        ('Plantio', 'Plantio'), ('Adubação', 'Adubação'),
        ('Defensivo', 'Aplicação de defensivo'), ('Irrigação', 'Irrigação'),
        ('Colheita', 'Colheita'), ('Análise', 'Análise de solo'),
    ]
    proprietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='atividades')
    data = models.DateField()
    propriedade = models.CharField(max_length=120)
    talhao = models.CharField(max_length=80)
    cultura = models.CharField(max_length=80)
    tipo = models.CharField(max_length=30, choices=TIPO)
    produto = models.CharField(max_length=120, blank=True)
    quantidade = models.CharField(max_length=80, blank=True)
    responsavel = models.CharField(max_length=120)
    observacoes = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-id']
        verbose_name_plural = 'atividades'

    def __str__(self):
        return f'{self.tipo} — {self.talhao}'
