from django.contrib import admin

from apps.academico.models import Aula, Disciplina, Matricula, Turma

# Register your models here.

# Classe de administração para o modelo Turma
class TurmaAdmin(admin.ModelAdmin):
    # Colunas que serão exibidas na lista de turmas no admin
    list_display = ('nome', 'ano', 'turno', 'professor_regente')
    
    # Filtros que serão exibidos na barra lateral do admin
    list_filter = ('ano', 'turno')
    
    # Busca por nome e ano da turma
    search_fields = ('nome', 'ano')

# Classe de administração para o modelo Disciplina
class DisciplinaAdmin(admin.ModelAdmin):
    # Colunas que serão exibidas na lista de disciplinas no admin
    list_display = ('nome',)
    
    # Busca por nome da disciplina
    search_fields = ('nome',)

# Classe de administração para o modelo Matricula
class MatriculaAdmin(admin.ModelAdmin):
    # Colunas que serão exibidas na lista de matrículas no admin
    list_display = ('aluno', 'turma', 'status', 'data_matricula')
    
    # Filtros que serão exibidos na barra lateral do admin
    list_filter = ('status', 'data_matricula')
    
    # Busca por nome do aluno e nome da turma
    search_fields = ('aluno__usuario__nome', 'turma__nome')

# Classe de administração para o modelo Aula
class AulaAdmin(admin.ModelAdmin):
    # Colunas que serão exibidas na lista de aulas no admin
    list_display = ('disciplina', 'turma', 'professor', 'data')
    
    # Filtros que serão exibidos na barra lateral do admin
    list_filter = ('data', 'turma')
    
    # Busca por nome da disciplina e nome da turma
    search_fields = ('disciplina__nome', 'turma__nome')

admin.site.register(Turma, TurmaAdmin)
admin.site.register(Disciplina, DisciplinaAdmin)
admin.site.register(Matricula, MatriculaAdmin)
admin.site.register(Aula, AulaAdmin)