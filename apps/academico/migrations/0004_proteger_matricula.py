from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('academico', '0003_rename_professor_disciplina_professores_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matricula',
            name='aluno',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='matriculas', to='usuarios.aluno'),
        ),
    ]
