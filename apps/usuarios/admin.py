from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Aluno, Professor, Responsavel, AlunoResponsavel
# Register your models here.

# Classe para garantir que o formulário use o hash de senha
class UsuarioAdmin(UserAdmin):
  
  # Qual tabela será protegida
  model = Usuario
  
  
  # Mostra para o admin as colunas nas tabelas
  list_display = ('email', 'nome', 'perfil', 'is_active')
  
  # Permite que o admin busque por email e nome
  search_fields = ('email', 'nome')
  
  # Ordena a tabela pelo nome
  ordering = ('nome',)
  
  # Define os campos que serão exibidos no formulário de edição de usuários
  fieldsets = (
    (None, {'fields': ('email', 'password')}),
    ('Informações Pessoais', {'fields': ('nome', 'perfil')}),
    ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
  )
  
  # Define os campos que serão exibidos no formulário de criação de usuários
  add_fieldsets = (
    (None, {
      'classes': ('wide',),
      'fields': ('email', 'nome', 'perfil', 'password1', 'password2'),
    }),
  )



# Registra o modelo Usuario com a classe UsuarioAdmin
admin.site.register(Usuario, UsuarioAdmin)

admin.site.register(Aluno)
admin.site.register(Professor)
admin.site.register(Responsavel)
admin.site.register(AlunoResponsavel)