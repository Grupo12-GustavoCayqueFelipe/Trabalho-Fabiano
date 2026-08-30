from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy

#Opções de tipos de usuário sendo (Professor, Aluno, Responsável e Administrador)
TIPO_USUARIO = [
    ('ADMIN', 'Administrador'),
    ('PROF', 'Professor'),
    ('ALUNO', 'Aluno'),
    ('RESP','Responsável'),
]
# Gerenciador que permite email como username
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O endereço de e-mail deve ser fornecido.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# Classe de usuário personalizada.
class Usuario(AbstractUser):
    
    # Remove os campos nativos de username do AbstractUser, pois vamos usar o email como campo de login
    username = None
    
    # Campo de tipo de usuário
    perfil = models.CharField(max_length=13, choices=TIPO_USUARIO, default='ALUNO', help_text='Define o tipo de usuário no sistema.')
    
    # Campos personalizados de usuário
    email = models.EmailField(gettext_lazy('email address'), unique=True)
    
    # Campo de nome completo do usuário
    nome = models.CharField(max_length=150, blank=False, null=False)
    
    # Faz o email ser o campo de login
    USERNAME_FIELD = 'email'
    
    # Chama a função nativa para verificar se está ativo
    is_active = models.BooleanField(default=True, db_column='ativo')
    
    # Define os campos obrigatorios, os nativos já são chamados automaticamente e o perfil já tem um valor default, então não precisa ser chamado.
    REQUIRED_FIELDS = ['nome']
    
    # Conecta o gerenciador acima
    objects = UsuarioManager()
    
    # Define o nome da tabela no banco de dados
    class Meta:
        db_table = 'usuarios'
    
class Aluno(models.Model):
    # Campo de relacionamento com a tabela de usuários.
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')
    
    # Campos personalizados de aluno
    matricula = models.CharField(max_length=20, unique=True)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=15, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    
    # Campo de relacionamento com a tabela de responsáveis, usando a tabela AlunoResponsavel.
    responsaveis = models.ManyToManyField('Responsavel', through='AlunoResponsavel', related_name='alunos_vinculados')
    
    # Define o nome da tabela no banco de dados
    class Meta:
        db_table = 'alunos'
    
    # Define a representação em string do objeto Aluno
    def __str__(self):
        return f"Aluno: {self.usuario.nome} - {self.matricula}"
    
class Professor(models.Model):
    # Campo de relacionamento com a tabela de usuários.
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')
    
    # Campos personalizados de professor
    formacao = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    
    # Define o nome da tabela no banco de dados
    class Meta:
        db_table = 'professores'
    
    # Define a representação em string do objeto Professor
    def __str__(self):
        return f"Professor: {self.usuario.nome} - {self.formacao}"
    
class Responsavel(models.Model):
    # Campo de relacionamento com a tabela de usuários.
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')
    
    # Campos personalizados de responsável
    telefone = models.CharField(max_length=15, blank=True, null=True)
    parentesco_principal = models.CharField(max_length=50, blank=True, null=True)
    
    # Define o nome da tabela no banco de dados
    class Meta:
        db_table = 'responsaveis'
    
    # Define a representação em string do objeto Responsável
    def __str__(self):
        return f"Responsável: {self.usuario.nome} - {self.parentesco_principal}"
    
class AlunoResponsavel(models.Model):
    # Campo de relacionamento com a tabela de alunos.
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, db_column='aluno_id')
    
    # Campo de relacionamento com a tabela de responsáveis.
    responsavel = models.ForeignKey(Responsavel, on_delete=models.CASCADE, db_column='responsavel_id')
    
    parentesco = models.CharField(max_length=50, blank=True, null=True)
    
    # Define o nome da tabela no banco de dados
    class Meta:
        db_table = 'aluno_responsavel'
    
    # Define a representação em string do objeto AlunoResponsavel
    def __str__(self):
        return f"Aluno: {self.aluno.usuario.nome} - Responsável: {self.responsavel.usuario.nome} - Parentesco: {self.parentesco}"