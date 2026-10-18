# Migra assuntos legados de texto simples para Fernet sem tentar descriptografá-los.
from django.db import migrations
import encrypted_model_fields.fields


def migrar_assuntos(apps, schema_editor):
  Mensagem = apps.get_model('comunicacao', 'Mensagem')
  banco = schema_editor.connection.alias
  for mensagem in Mensagem.objects.using(banco).iterator(chunk_size=200):
    mensagem.assunto_cifrado = mensagem.assunto
    mensagem.save(using=banco, update_fields=['assunto_cifrado'])


class Migration(migrations.Migration):
  dependencies = [
    ('comunicacao', '0002_alter_aviso_options_aviso_fixado'),
  ]

  operations = [
    migrations.AddField(
      model_name='mensagem',
      name='assunto_cifrado',
      field=encrypted_model_fields.fields.EncryptedCharField(max_length=120, null=True, blank=True),
    ),
    migrations.RunPython(migrar_assuntos, migrations.RunPython.noop),
    migrations.RemoveField(model_name='mensagem', name='assunto'),
    migrations.RenameField(model_name='mensagem', old_name='assunto_cifrado', new_name='assunto'),
    migrations.AlterField(
      model_name='mensagem',
      name='assunto',
      field=encrypted_model_fields.fields.EncryptedCharField(max_length=120),
    ),
  ]
