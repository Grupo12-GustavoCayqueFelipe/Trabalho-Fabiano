from django.db import migrations, models


# Essas restrições são avaliadas pelo próprio PostgreSQL e pelo SQLite.
class Migration(migrations.Migration):
    dependencies = [
        ('academico', '0006_merge_integracao'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='periodoletivo',
            constraint=models.CheckConstraint(condition=models.Q(data_fim__gte=models.F('data_inicio')), name='periodo_datas_validas'),
        ),
        migrations.AddConstraint(
            model_name='periodoletivo',
            constraint=models.CheckConstraint(condition=models.Q(semestre__in=[1, 2]), name='periodo_semestre_valido'),
        ),
    ]
