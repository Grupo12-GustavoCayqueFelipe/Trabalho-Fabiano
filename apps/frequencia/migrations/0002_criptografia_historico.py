from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


# Copia as justificativas antigas pelo campo Fernet antes de retirar texto simples.
def migrar_justificativas(apps, schema_editor):
    RegistroFrequencia = apps.get_model('frequencia', 'RegistroFrequencia')
    banco = schema_editor.connection.alias
    for registro in RegistroFrequencia.objects.using(banco).iterator(chunk_size=200):
        registro.justificativa_cifrada = registro.justificativa
        registro.save(using=banco, update_fields=['justificativa_cifrada'])


# Preserva os dados mesmo se a migration 0001 já tiver sido aplicada.
class Migration(migrations.Migration):
    dependencies = [
        ('frequencia', '0001_initial'),
        ('academico', '0006_merge_integracao'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrofrequencia',
            name='justificativa_cifrada',
            field=encrypted_model_fields.fields.EncryptedCharField(max_length=200, blank=True, null=True, help_text='Preencher em caso de falta justificada'),
        ),
        migrations.RunPython(migrar_justificativas, migrations.RunPython.noop),
        migrations.RemoveField(model_name='registrofrequencia', name='justificativa'),
        migrations.RenameField(model_name='registrofrequencia', old_name='justificativa_cifrada', new_name='justificativa'),
        migrations.CreateModel(
            name='HistoricoFrequencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_anterior', models.CharField(max_length=1, choices=[('P', 'Presente'), ('F', 'Falta'), ('J', 'Falta Justificada')], null=True, blank=True)),
                ('status_novo', models.CharField(max_length=1, choices=[('P', 'Presente'), ('F', 'Falta'), ('J', 'Falta Justificada')])),
                ('justificativa_anterior', encrypted_model_fields.fields.EncryptedCharField(max_length=200, blank=True, null=True)),
                ('justificativa_nova', encrypted_model_fields.fields.EncryptedCharField(max_length=200, blank=True, null=True)),
                ('alterado_em', models.DateTimeField(auto_now_add=True)),
                ('registro', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historico', to='frequencia.registrofrequencia')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.usuario')),
            ],
            options={'db_table': 'historico_frequencia', 'ordering': ['-alterado_em', '-pk']},
        ),
    ]
