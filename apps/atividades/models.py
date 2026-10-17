from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedTextField
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.academico.models import Turma, Disciplina
from apps.usuarios.models import Aluno, Professor


# Atividade publicada por um professor para uma turma e disciplina específicas.
class Atividade(models.Model):
    titulo = models.CharField(max_length=120)
    descricao = models.TextField(max_length=4000)
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name='atividades')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, related_name='atividades')
    professor = models.ForeignKey(Professor, on_delete=models.PROTECT, related_name='atividades')
    prazo = models.DateTimeField()
    criada_em = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)
    # Nota máxima da atividade
    valor_nota = models.DecimalField(max_digits=4, decimal_places=2, default=10, validators=[MinValueValidator(0), MaxValueValidator(10)])

    class Meta:
        db_table = 'atividades'
        ordering = ['-criada_em']

    def __str__(self):
        return self.titulo

    # Indica se o prazo já passou
    @property
    def esta_atrasada(self):
        return timezone.now() > self.prazo


# Entrega de um aluno: uma única por atividade, podendo atualizar antes do prazo.
class Entrega(models.Model):
    atividade = models.ForeignKey(Atividade, on_delete=models.PROTECT, related_name='entregas')
    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT, related_name='entregas')
    resposta = EncryptedTextField(max_length=5000)
    entregue_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    comentario_professor = EncryptedTextField(max_length=2000, blank=True)
    corrigida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'entregas_atividades'
        constraints = [models.UniqueConstraint(fields=['atividade', 'aluno'], name='uma_entrega_por_atividade_aluno')]

    def __str__(self):
        return f'Entrega {self.pk} - atividade {self.atividade_id}'
