import django.core.validators
from django.db import migrations
import encrypted_model_fields.fields


class Migration(migrations.Migration):
  dependencies = [
    ('usuarios', '0016_converter_otp_secret_legado'),
  ]

  operations = [
    migrations.AlterField(
      model_name='aluno',
      name='endereco',
      field=encrypted_model_fields.fields.EncryptedTextField(
        blank=True,
        null=True,
        validators=[django.core.validators.MaxLengthValidator(500)],
      ),
    ),
  ]
