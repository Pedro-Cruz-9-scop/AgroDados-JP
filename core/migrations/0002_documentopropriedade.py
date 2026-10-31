from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]
    operations = [migrations.CreateModel(name='DocumentoPropriedade', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('categoria', models.CharField(choices=[('CAR','CAR'),('CCIR','CCIR'),('ITR','ITR'),('Comodato','Contrato de comodato'),('Escritura','Escritura / matrícula'),('Outro','Outro')], max_length=30)),
        ('titulo', models.CharField(max_length=160)),
        ('arquivo', models.FileField(upload_to='documentos_propriedades/%Y/%m/')),
        ('numero', models.CharField(blank=True, max_length=100)),
        ('emitido_em', models.DateField(blank=True, null=True)),
        ('validade', models.DateField(blank=True, null=True)),
        ('observacoes', models.TextField(blank=True)),
        ('enviado_em', models.DateTimeField(auto_now_add=True)),
        ('propriedade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='core.propriedade')),
    ], options={'ordering':['categoria','-enviado_em']})]
