from django.contrib import admin
from core.admin_auditoria import AdminComAuditoria
from .models import Aviso, Mensagem

# Avisos institucionais podem ser editados, mas cada alteração deve ser auditada.
@admin.register(Aviso)
class AvisoAdmin(AdminComAuditoria):
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
