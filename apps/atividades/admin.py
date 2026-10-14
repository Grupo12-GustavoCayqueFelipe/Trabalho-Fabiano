from django.contrib import admin
from .models import Atividade, Entrega

# O Django Admin é protegido pelo segundo fator na configuração do projeto.
@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'turma', 'disciplina', 'professor', 'prazo', 'ativa')
    list_filter = ('ativa', 'turma')


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('atividade', 'aluno', 'entregue_em', 'corrigida_em', 'nota')
    readonly_fields = ('entregue_em', 'atualizada_em')
