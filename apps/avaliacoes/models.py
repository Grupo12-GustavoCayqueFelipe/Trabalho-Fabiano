from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Avaliação aplicada a uma turma em uma disciplina (prova, seminário etc.).
class Avaliacao(models.Model):
    turma = models.ForeignKey('academico.Turma', on_delete=models.PROTECT, related_name='avaliacoes')
    disciplina = models.ForeignKey('academico.Disciplina', on_delete=models.PROTECT, related_name='avaliacoes')
    nome = models.CharField(max_length=200, help_text='Ex: Prova 1, Seminário Final')
    data_avaliacao = models.DateField()
    nota_maxima = models.DecimalField(max_digits=4, decimal_places=2, default=10, validators=[MinValueValidator(0), MaxValueValidator(10)])
    peso = models.DecimalField(max_digits=4, decimal_places=2, default=1, help_text='Multiplicador para média ponderada')

    class Meta:
        db_table = 'avaliacoes'
        ordering = ['data_avaliacao']

    def __str__(self):
        return f"{self.nome} - {self.turma}"


# Nota de um aluno (via matrícula) em uma avaliação.
class Nota(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.PROTECT, related_name='notas')
    matricula = models.ForeignKey('academico.Matricula', on_delete=models.PROTECT, related_name='notas')
    valor = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'notas'
        # Impede duas notas para o mesmo aluno na mesma avaliação
        unique_together = ('avaliacao', 'matricula')

    def __str__(self):
        return f"Nota: {self.valor} - {self.matricula} em {self.avaliacao.nome}"