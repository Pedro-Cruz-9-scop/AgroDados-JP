import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='Propriedade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('municipio', models.CharField(blank=True, max_length=120)),
                ('area_hectares', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('responsavel', models.CharField(blank=True, max_length=120)),
                ('cultura_principal', models.CharField(blank=True, max_length=80)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('proprietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='propriedades', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['nome'], 'verbose_name': 'propriedade', 'verbose_name_plural': 'propriedades'},
        ),
        migrations.CreateModel(
            name='Insumo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('categoria', models.CharField(max_length=80)),
                ('quantidade', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('unidade', models.CharField(default='kg', max_length=20)),
                ('observacoes', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('proprietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='insumos', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['nome']},
        ),
        migrations.CreateModel(
            name='Atividade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField()),
                ('propriedade', models.CharField(max_length=120)),
                ('talhao', models.CharField(max_length=80)),
                ('cultura', models.CharField(max_length=80)),
                ('tipo', models.CharField(choices=[('Plantio', 'Plantio'), ('Adubação', 'Adubação'), ('Defensivo', 'Aplicação de defensivo'), ('Irrigação', 'Irrigação'), ('Colheita', 'Colheita'), ('Análise', 'Análise de solo')], max_length=30)),
                ('produto', models.CharField(blank=True, max_length=120)),
                ('quantidade', models.CharField(blank=True, max_length=80)),
                ('responsavel', models.CharField(max_length=120)),
                ('observacoes', models.TextField(blank=True)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('proprietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='atividades', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-data', '-id'], 'verbose_name_plural': 'atividades'},
        ),
    ]
