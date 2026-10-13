# Migração incremental: não altera as migrações já aplicadas no Supabase.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0013_alter_usuario_otp_secret'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aluno',
            name='data_nascimento',
            field=encrypted_model_fields.fields.EncryptedDateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='logacesso',
            name='usuario',
            field=models.ForeignKey(blank=True, db_column='usuario_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='logrecuperacaosenha',
            name='usuario',
            field=models.ForeignKey(blank=True, db_column='usuario_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consentimentousuario',
            name='aluno_representado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos_responsaveis', to='usuarios.aluno'),
        ),
        migrations.AlterField(
            model_name='logacesso',
            name='evento',
            field=models.CharField(choices=[
                ('LOGIN_FALHA', 'Falha de login'),
                ('LOGIN_SUCESSO', 'Login bem-sucedido'),
                ('CONTA_BLOQUEADA', 'Conta bloqueada devido a múltiplas tentativas de login falhas'),
                ('2FA_SUCESSO', 'Autenticação de dois fatores bem-sucedida'),
                ('2FA_FALHA', 'Falha na autenticação de dois fatores'),
                ('2FA_ATIVADO', 'Segundo fator ativado'),
                ('2FA_DESATIVADO', 'Segundo fator desativado'),
            ], max_length=50),
        ),
        migrations.CreateModel(
            name='LogOperacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evento', models.CharField(max_length=60)),
                ('objeto_id', models.PositiveBigIntegerField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'log_operacao'},
        ),
    ]
