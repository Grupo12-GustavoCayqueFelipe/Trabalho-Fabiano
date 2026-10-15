from django.contrib import admin
from .models import Aviso, Mensagem

# Exibe os registros sem permitir alterar mensagens já enviadas.
@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'turma', 'criado_em', 'ativo')


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ('assunto', 'remetente', 'destinatario', 'enviada_em')
    readonly_fields = ('remetente', 'destinatario', 'assunto', 'texto', 'enviada_em', 'lida_em')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
