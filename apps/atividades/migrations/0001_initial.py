from django.db import migrations, models
import encrypted_model_fields.fields
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('usuarios', '0014_seguranca_lgpd'),
        ('academico', '0004_proteger_matricula'),
    ]

    operations = [
        migrations.CreateModel(
            name='Atividade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('descricao', models.TextField(max_length=4000)),
                ('prazo', models.DateTimeField()),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('ativa', models.BooleanField(default=True)),
                ('turma', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='atividades', to='academico.turma')),
                ('disciplina', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='atividades', to='academico.disciplina')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='atividades', to='usuarios.professor')),
            ],
            options={'db_table': 'atividades', 'ordering': ['-criada_em']},
        ),
        migrations.CreateModel(
            name='Entrega',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resposta', encrypted_model_fields.fields.EncryptedTextField(max_length=5000)),
                ('entregue_em', models.DateTimeField(auto_now_add=True)),
                ('atualizada_em', models.DateTimeField(auto_now=True)),
                ('nota', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('comentario_professor', encrypted_model_fields.fields.EncryptedTextField(blank=True, max_length=2000)),
                ('corrigida_em', models.DateTimeField(blank=True, null=True)),
                ('atividade', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entregas', to='atividades.atividade')),
                ('aluno', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entregas', to='usuarios.aluno')),
            ],
            options={'db_table': 'entregas_atividades'},
        ),
        migrations.AddConstraint(
            model_name='entrega',
            constraint=models.UniqueConstraint(fields=('atividade', 'aluno'), name='uma_entrega_por_atividade_aluno'),
        ),
    ]
