from django.db import models
from django.utils import timezone

def ano_atual():
    return timezone.now().year  

# Define o turno da turma
TURNO_CHOICES = [
    ('MANHA', 'Manhã'),
    ('TARDE', 'Tarde'),
    ('NOITE', 'Noite'),
]

# Define o status da matrícula do aluno na turma
STATUS_CHOICES = [
    ('ATIVA', 'Matricula Ativa'),
    ('TRANSFERIDA', 'Transferida'),
    ('CANCELADA', 'Cancelada'),
    ('CONCLUIDA', 'Concluida')
]

# Create your models here.

# Classe de turma, que possui um relacionamento com a tabela de professores.
class Turma(models.Model):
    # Define o nome da turma
    nome = models.CharField(max_length=50)
    
    # Define o ano da turma, com valor padrão sendo o ano atual
    ano = models.IntegerField(default=ano_atual)
    
    # Define o turno da turma
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)

    # Professor regente da turma, que possui um relacionamento com a tabela de professores. Se o professor for deletado, o campo será definido como NULL.
    professor_regente = models.ForeignKey('usuarios.Professor', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'turmas'

    def __str__(self):
        return f"{self.nome} - {self.ano} - {self.turno}"

# Classe de disciplina, que possui um relacionamento com a tabela de turmas e professores.
class Disciplina(models.Model):
    # Define o nome da disciplina
    nome = models.CharField(max_length=100)
    
    # Define as turmas que oferecem esta disciplina
    turmas = models.ManyToManyField('Turma')
    
    # Define o professor que leciona a disciplina, relação many to many porque um professor pode lecionar varias disciplinas e uma disciplina pode pode ter vários professores.
    professor = models.ManyToManyField('usuarios.Professor')
    
    class Meta:
        db_table = 'disciplinas'

    def __str__(self):
        return f"{self.nome}"

class Matricula(models.Model):
    # Define o aluno que está matriculado, que possui um relacionamento com a tabela de alunos.
    aluno = models.ForeignKey('usuarios.Aluno', on_delete=models.CASCADE, related_name='matriculas')
    
    # Define a turma em que o aluno está matriculado, que possui um relacionamento com a tabela de turmas.
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE)
    
    # Define a data de matrícula do aluno na turma
    data_matricula = models.DateField(default=timezone.now)
    
    # Define o status da matrícula do aluno na turma
    status = models.CharField(max_length=20, default='ATIVA', choices=STATUS_CHOICES)
    
    class Meta:
        db_table = 'matriculas'
        unique_together = ('aluno', 'turma')  # Garante que um aluno não possa se matricular na mesma turma mais de uma vez

    def __str__(self):
        return f"Aluno: {self.aluno} - Turma: {self.turma} - Ano: {self.status}"

class Aula(models.Model):
    # Define a turma em que a aula será ministrada, que possui um relacionamento com a tabela de turmas.
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='aulas')
    
    # Define a disciplina que será ministrada na aula, que possui um relacionamento com a tabela de disciplinas.
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='aulas')
    
    # Define o professor que ministrará a aula, que possui um relacionamento com a tabela de professores. Se o professor for deletado, o campo será definido como NULL.
    professor = models.ForeignKey('usuarios.Professor', on_delete=models.SET_NULL, blank=True, null=True, related_name='aulas')
    
    # Define a data da aula
    data = models.DateField()
    
    # Define o conteúdo da aula, que é um campo de texto que pode ser deixado em branco ou nulo.
    conteudo = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'aulas'
    
    def __str__(self):
        return f"{self.disciplina} - {self.turma} - {self.data}"