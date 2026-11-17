from django.contrib import admin
from apps.usuarios.admin import SomenteLeituraAdmin
from .models import Avaliacao, HistoricoNota, Nota


# Avaliações, notas e histórico são somente leitura no Admin; lançamentos passam pelas views auditadas.
@admin.register(Avaliacao)
class AvaliacaoAdmin(SomenteLeituraAdmin):
  list_display = ('nome', 'turma', 'disciplina', 'data_avaliacao', 'nota_maxima', 'peso')
  list_filter = ('turma', 'disciplina')


@admin.register(Nota)
class NotaAdmin(SomenteLeituraAdmin):
  list_display = ('avaliacao', 'matricula', 'valor')
  readonly_fields = ('avaliacao', 'matricula', 'valor', 'observacao')


@admin.register(HistoricoNota)
class HistoricoNotaAdmin(SomenteLeituraAdmin):
  list_display = ('nota', 'usuario', 'valor_anterior', 'valor_novo', 'alterado_em')
  readonly_fields = (
    'nota', 'usuario', 'valor_anterior', 'valor_novo',
    'observacao_anterior', 'observacao_nova', 'alterado_em',
  )
