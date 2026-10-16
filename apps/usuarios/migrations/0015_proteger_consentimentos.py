# Protege o histórico de autorizações e revogações contra exclusão em cascata.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0014_seguranca_lgpd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consentimentousuario',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos', to=settings.AUTH_USER_MODEL),
        ),
    ]
