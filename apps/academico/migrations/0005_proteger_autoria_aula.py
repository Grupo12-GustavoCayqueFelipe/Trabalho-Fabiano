# Preserva quem ministrou a aula mesmo se alguém tentar apagar o professor.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('academico', '0004_proteger_matricula'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aula',
            name='professor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='aulas', to='usuarios.professor'),
        ),
    ]
