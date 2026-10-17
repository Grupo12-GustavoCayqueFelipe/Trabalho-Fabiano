from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from encrypted_model_fields.fields import EncryptedTextField


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

    # Garante que a disciplina esteja cadastrada na turma.
    def clean(self):
        super().clean()
        if self.turma_id and self.disciplina_id:
            if not self.disciplina.turmas.filter(pk=self.turma_id).exists():
                raise ValidationError({'disciplina': 'Disciplina não pertence à turma.'})
        if self.nota_maxima is not None and self.nota_maxima <= 0:
            raise ValidationError({'nota_maxima': 'Informe uma nota máxima positiva.'})
        if self.peso is not None and self.peso <= 0:
            raise ValidationError({'peso': 'Informe um peso positivo.'})

    def __str__(self):
        return f"{self.nome} - {self.turma}"


# Nota de um aluno (via matrícula) em uma avaliação.
class Nota(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.PROTECT, related_name='notas')
    matricula = models.ForeignKey('academico.Matricula', on_delete=models.PROTECT, related_name='notas')
    valor = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    # Observação pode conter dado pessoal e deve ser criptografada.
    observacao = EncryptedTextField(blank=True, null=True)

    class Meta:
        db_table = 'notas'
        # Impede duas notas para o mesmo aluno na mesma avaliação
        unique_together = ('avaliacao', 'matricula')

    # Valida a matrícula e o valor sem depender somente do HTML.
    def clean(self):
        super().clean()
        if self.avaliacao_id and self.matricula_id:
            if self.avaliacao.turma_id != self.matricula.turma_id:
                raise ValidationError({'matricula': 'Matrícula de outra turma.'})
            if not self.avaliacao.disciplina.turmas.filter(pk=self.avaliacao.turma_id).exists():
                raise ValidationError({'avaliacao': 'Disciplina não pertence à turma.'})
            if self.valor is not None and self.valor > self.avaliacao.nota_maxima:
                raise ValidationError({'valor': 'Nota superior à nota máxima.'})

    def __str__(self):
        return f"Nota: {self.valor} - {self.matricula} em {self.avaliacao.nome}"


# Guarda a versão anterior e nova de cada lançamento de nota.
class HistoricoNota(models.Model):
    nota = models.ForeignKey(Nota, on_delete=models.PROTECT, related_name='historico')
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT)
    valor_anterior = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    valor_novo = models.DecimalField(max_digits=4, decimal_places=2)
    observacao_anterior = EncryptedTextField(blank=True, null=True)
    observacao_nova = EncryptedTextField(blank=True, null=True)
    alterado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historico_notas'
        ordering = ['-alterado_em', '-pk']