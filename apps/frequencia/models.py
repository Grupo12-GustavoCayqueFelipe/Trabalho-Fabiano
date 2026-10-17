from django.db import models
from django.core.exceptions import ValidationError
from encrypted_model_fields.fields import EncryptedCharField

STATUS_FREQUENCIA = [
    ('P', 'Presente'),
    ('F', 'Falta'),
    ('J', 'Falta Justificada'),
]


# Presença ou falta de um aluno (via matrícula) em uma aula.
class RegistroFrequencia(models.Model):
    aula = models.ForeignKey('academico.Aula', on_delete=models.PROTECT, related_name='frequencias')
    matricula = models.ForeignKey('academico.Matricula', on_delete=models.PROTECT, related_name='frequencias')
    status = models.CharField(max_length=1, choices=STATUS_FREQUENCIA, default='P')
    # A justificativa pode conter informação pessoal e permanece criptografada.
    justificativa = EncryptedCharField(max_length=200, blank=True, null=True, help_text='Preencher em caso de falta justificada')

    class Meta:
        db_table = 'registros_frequencia'
        # Impede dois registros do mesmo aluno na mesma aula
        unique_together = ('aula', 'matricula')

    # A frequência só pode ser registrada para matrícula da mesma turma.
    def clean(self):
        super().clean()
        if self.aula_id and self.matricula_id:
            if self.aula.turma_id != self.matricula.turma_id:
                raise ValidationError({'matricula': 'Matrícula de outra turma.'})
            if not self.aula.disciplina.turmas.filter(pk=self.aula.turma_id).exists():
                raise ValidationError({'aula': 'Disciplina não vinculada à turma.'})
        if self.status == 'J' and not (self.justificativa or '').strip():
            raise ValidationError({'justificativa': 'Informe o motivo da falta justificada.'})

    def __str__(self):
        return f"{self.get_status_display()} - {self.matricula} ({self.aula})"


# Guarda as correções feitas nos registros de frequência escolar.
class HistoricoFrequencia(models.Model):
    registro = models.ForeignKey(RegistroFrequencia, on_delete=models.PROTECT, related_name='historico')
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT)
    status_anterior = models.CharField(max_length=1, choices=STATUS_FREQUENCIA, null=True, blank=True)
    status_novo = models.CharField(max_length=1, choices=STATUS_FREQUENCIA)
    justificativa_anterior = EncryptedCharField(max_length=200, blank=True, null=True)
    justificativa_nova = EncryptedCharField(max_length=200, blank=True, null=True)
    alterado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historico_frequencia'
        ordering = ['-alterado_em', '-pk']