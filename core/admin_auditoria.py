# Centraliza auditoria de operações no Django Admin sem armazenar dados pessoais no log.
from django.contrib import admin
from django.db import transaction

from apps.usuarios.models import registrar_operacao


class AdminComAuditoria(admin.ModelAdmin):
  # A ação de exclusão em lote não deve contornar a auditoria individual.
  actions = None

  def _registrar(self, request, acao, obj):
    registrar_operacao(request.user, f'ADMIN_{acao}_{obj._meta.model_name.upper()}', obj.pk)

  def save_model(self, request, obj, form, change):
    with transaction.atomic():
      super().save_model(request, obj, form, change)
      self._registrar(request, 'ALTEROU' if change else 'CRIOU', obj)

  def delete_model(self, request, obj):
    with transaction.atomic():
      self._registrar(request, 'EXCLUIU', obj)
      super().delete_model(request, obj)

  def delete_queryset(self, request, queryset):
    # Protege também chamadas futuras de exclusão em lote.
    with transaction.atomic():
      for obj in queryset:
        self.delete_model(request, obj)
