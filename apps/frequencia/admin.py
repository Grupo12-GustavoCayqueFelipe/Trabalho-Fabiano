from django.contrib import admin
from apps.usuarios.admin import SomenteLeituraAdmin
from .models import HistoricoFrequencia, RegistroFrequencia


# Registros de frequência e seu histórico permanecem somente leitura no Admin.
@admin.register(RegistroFrequencia)
class RegistroFrequenciaAdmin(SomenteLeituraAdmin):
  list_display = ('aula', 'matricula', 'status')
  readonly_fields = ('aula', 'matricula', 'status', 'justificativa')


@admin.register(HistoricoFrequencia)
class HistoricoFrequenciaAdmin(SomenteLeituraAdmin):
  list_display = ('registro', 'usuario', 'status_anterior', 'status_novo', 'alterado_em')
  readonly_fields = (
    'registro', 'usuario', 'status_anterior', 'status_novo',
    'justificativa_anterior', 'justificativa_nova', 'alterado_em',
  )
