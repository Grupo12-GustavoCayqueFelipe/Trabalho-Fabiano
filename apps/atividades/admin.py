from django.contrib import admin
from .models import Atividade, Entrega, HistoricoCorrecao

# O Django Admin é protegido pelo segundo fator na configuração do projeto.
@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'turma', 'disciplina', 'professor', 'prazo', 'ativa')
    list_filter = ('ativa', 'turma')

    # Toda publicação e edição deve registrar um evento pela view protegida.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # Evita excluir atividades que são parte do histórico acadêmico.
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('atividade', 'aluno', 'entregue_em', 'corrigida_em', 'nota')
    readonly_fields = ('entregue_em', 'atualizada_em')

    # As mudanças de entrega devem passar pelas views com histórico e auditoria.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Histórico só é consultado; os professores registram pela view de correção.
@admin.register(HistoricoCorrecao)
class HistoricoCorrecaoAdmin(admin.ModelAdmin):
    list_display = ('entrega', 'professor', 'alterado_em')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
