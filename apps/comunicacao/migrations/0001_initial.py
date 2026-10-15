from django.conf import settings
from django.db import migrations, models
import encrypted_model_fields.fields
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('usuarios', '0014_seguranca_lgpd'),
        ('academico', '0004_proteger_matricula'),
    ]

    operations = [
        migrations.CreateModel(
            name='Aviso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('texto', encrypted_model_fields.fields.EncryptedTextField(max_length=3000)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('ativo', models.BooleanField(default=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='avisos_criados', to=settings.AUTH_USER_MODEL)),
                ('turma', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='avisos', to='academico.turma')),
            ],
            options={'db_table': 'avisos_escola', 'ordering': ['-criado_em']},
        ),
        migrations.CreateModel(
            name='Mensagem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assunto', models.CharField(max_length=120)),
                ('texto', encrypted_model_fields.fields.EncryptedTextField(max_length=3000)),
                ('enviada_em', models.DateTimeField(auto_now_add=True)),
                ('lida_em', models.DateTimeField(blank=True, null=True)),
                ('remetente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mensagens_enviadas', to=settings.AUTH_USER_MODEL)),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mensagens_recebidas', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'mensagens_escola', 'ordering': ['-enviada_em']},
        ),
    ]
