from django.db import models
from encrypted_model_fields.fields import EncryptedTextField, EncryptedCharField
from apps.academico.models import Turma
from apps.usuarios.models import Usuario


# Aviso do mural: um aviso geral é permitido apenas para administradores.
class Aviso(models.Model):
    titulo = models.CharField(max_length=120)
    texto = EncryptedTextField(max_length=3000)
    autor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='avisos_criados')
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, null=True, blank=True, related_name='avisos')
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    # NOVO: avisos fixados aparecem primeiro
    fixado = models.BooleanField(default=False)

    class Meta:
        db_table = 'avisos_escola'
        ordering = ['-fixado', '-criado_em']  # NOVO

    def __str__(self):
        return self.titulo


# Mensagem interna individual, restrita ao remetente e destinatário.
class Mensagem(models.Model):
    remetente = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='mensagens_enviadas')
    destinatario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='mensagens_recebidas')
    assunto = EncryptedCharField(max_length=120)
    texto = EncryptedTextField(max_length=3000)
    enviada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mensagens_escola'
        ordering = ['-enviada_em']

    def __str__(self):
        return self.assunto
