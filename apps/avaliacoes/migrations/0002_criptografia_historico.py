from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


# Copia o conteúdo existente antes de retirar a coluna de texto simples.
def migrar_observacoes(apps, schema_editor):
    Nota = apps.get_model('avaliacoes', 'Nota')
    banco = schema_editor.connection.alias
    # O campo novo já usa Fernet; não copia dados para os logs.
    for nota in Nota.objects.using(banco).iterator(chunk_size=200):
        nota.observacao_cifrada = nota.observacao
        nota.save(using=banco, update_fields=['observacao_cifrada'])


# A migration inicial pode ter sido executada no Supabase: preserva dados existentes.
class Migration(migrations.Migration):
    dependencies = [
        ('avaliacoes', '0001_initial'),
        ('academico', '0006_merge_integracao'),
    ]

    operations = [
        # Campo temporário criptografado evita que o valor antigo seja interpretado errado.
        migrations.AddField(
            model_name='nota',
            name='observacao_cifrada',
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True, null=True),
        ),
        migrations.RunPython(migrar_observacoes, migrations.RunPython.noop),
        # A coluna antiga só é removida depois de todos os dados serem copiados.
        migrations.RemoveField(model_name='nota', name='observacao'),
        migrations.RenameField(model_name='nota', old_name='observacao_cifrada', new_name='observacao'),
        migrations.CreateModel(
            name='HistoricoNota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_anterior', models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)),
                ('valor_novo', models.DecimalField(max_digits=4, decimal_places=2)),
                ('observacao_anterior', encrypted_model_fields.fields.EncryptedTextField(blank=True, null=True)),
                ('observacao_nova', encrypted_model_fields.fields.EncryptedTextField(blank=True, null=True)),
                ('alterado_em', models.DateTimeField(auto_now_add=True)),
                ('nota', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historico', to='avaliacoes.nota')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.usuario')),
            ],
            options={'db_table': 'historico_notas', 'ordering': ['-alterado_em', '-pk']},
        ),
    ]
