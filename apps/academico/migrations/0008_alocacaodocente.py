import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0007_validar_periodos'),
        ('usuarios', '0015_proteger_consentimentos'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlocacaoDocente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disciplina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alocacoes', to='academico.disciplina')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alocacoes', to='usuarios.professor')),
                ('turma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alocacoes', to='academico.turma')),
            ],
            options={
                'db_table': 'alocacoes_docentes',
                'unique_together': {('professor', 'disciplina', 'turma')},
            },
        ),
    ]
