from django.db import models

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
    justificativa = models.CharField(max_length=200, blank=True, null=True, help_text='Preencher em caso de falta justificada')

    class Meta:
        db_table = 'registros_frequencia'
        # Impede dois registros do mesmo aluno na mesma aula
        unique_together = ('aula', 'matricula')

    def __str__(self):
        return f"{self.get_status_display()} - {self.matricula} ({self.aula})"