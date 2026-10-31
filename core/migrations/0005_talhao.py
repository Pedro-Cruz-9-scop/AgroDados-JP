from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_delete_talhao'),
    ]

    operations = [
        migrations.CreateModel(
            name='Talhao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=80)),
                ('cultura', models.CharField(blank=True, max_length=80)),
                ('area_hectares', models.DecimalField(decimal_places=2, max_digits=12)),
                ('limites', models.JSONField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('propriedade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='talhoes', to='core.propriedade')),
            ],
            options={
                'verbose_name': 'talhão',
                'verbose_name_plural': 'talhões',
                'ordering': ['propriedade__nome', 'nome'],
            },
        ),
    ]
