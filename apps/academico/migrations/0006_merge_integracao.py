from django.db import migrations


# As duas migrations 0005 já existem e não podem ser renomeadas após o deploy.
class Migration(migrations.Migration):
    dependencies = [
        ('academico', '0005_proteger_autoria_aula'),
        ('academico', '0005_periodoletivo_turma_periodo_letivo'),
    ]

    # Nenhuma tabela é recriada: o merge apenas organiza as dependências.
    operations = []
