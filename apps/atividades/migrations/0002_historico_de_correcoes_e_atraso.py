# Guarda revisões de notas e identifica respostas entregues fora do prazo.
from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


class Migration(migrations.Migration):
    dependencies = [
        ('atividades', '0001_initial'),
        ('academico', '0005_proteger_autoria_aula'),
        ('usuarios', '0015_proteger_consentimentos'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrega',
            name='atrasada',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='HistoricoCorrecao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nota_anterior', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('nota_nova', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('comentario_anterior', encrypted_model_fields.fields.EncryptedTextField(blank=True, max_length=2000)),
                ('comentario_novo', encrypted_model_fields.fields.EncryptedTextField(blank=True, max_length=2000)),
                ('alterado_em', models.DateTimeField(auto_now_add=True)),
                ('entrega', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historico_correcoes', to='atividades.entrega')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.professor')),
            ],
            options={
                'db_table': 'historico_correcoes',
                'ordering': ['-alterado_em', '-pk'],
            },
        ),
    ]
