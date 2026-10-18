# Testes de regressão para privacidade, limites de escrita e trilha do Django Admin.
from django.contrib import admin
from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.usuarios.models import Aluno, AlunoResponsavel, LogOperacao, Responsavel, Usuario
from apps.usuarios.admin import AlunoResponsavelAdmin
from .admin import AvisoAdmin
from .models import Aviso, Mensagem


class ComunicacaoEntregaTest(TestCase):
  def setUp(self):
    cache.clear()
    self.admin = Usuario.objects.create_superuser(
      email='auditoria-admin@example.test', password='Senha@12345', nome='Admin',
    )
    self.destinatario = Usuario.objects.create_user(
      email='destinatario@example.test', password='Senha@12345', nome='Aluno', perfil='ALUNO',
    )

  def test_assunto_e_criptografado_no_banco(self):
    mensagem = Mensagem.objects.create(
      remetente=self.admin, destinatario=self.destinatario,
      assunto='Informação pessoal e familiar', texto='Texto restrito',
    )
    with connection.cursor() as cursor:
      cursor.execute('SELECT assunto FROM mensagens_escola WHERE id = %s', [mensagem.pk])
      valor_banco = cursor.fetchone()[0]
    self.assertNotEqual(valor_banco, 'Informação pessoal e familiar')
    mensagem.refresh_from_db()
    self.assertEqual(mensagem.assunto, 'Informação pessoal e familiar')

  def test_limite_de_avisos_bloqueia_requisicao_21(self):
    self.client.force_login(self.admin)
    for numero in range(20):
      resposta = self.client.post(reverse('aviso_criar'), {
        'titulo': f'Aviso {numero}', 'texto': 'Texto de teste',
      })
      self.assertEqual(resposta.status_code, 302)
    resposta = self.client.post(reverse('aviso_criar'), {
      'titulo': 'Aviso excessivo', 'texto': 'Texto de teste',
    })
    self.assertEqual(resposta.status_code, 403)
    self.assertEqual(Aviso.objects.count(), 20)

  def test_admin_aviso_registra_criacao_edicao_exclusao(self):
    request = RequestFactory().post('/admin/comunicacao/aviso/')
    request.user = self.admin
    painel = AvisoAdmin(Aviso, admin.site)
    aviso = Aviso(titulo='Aviso escolar', texto='Teste', autor=self.admin)
    painel.save_model(request, aviso, form=None, change=False)
    aviso.titulo = 'Aviso revisado'
    painel.save_model(request, aviso, form=None, change=True)
    painel.delete_model(request, aviso)
    self.assertEqual(list(LogOperacao.objects.filter(
      evento__in=['ADMIN_CRIOU_AVISO', 'ADMIN_ALTEROU_AVISO', 'ADMIN_EXCLUIU_AVISO']
    ).order_by('pk').values_list('evento', flat=True)), [
      'ADMIN_CRIOU_AVISO', 'ADMIN_ALTEROU_AVISO', 'ADMIN_EXCLUIU_AVISO',
    ])

  def test_admin_vinculo_responsavel_e_auditado(self):
    aluno = Aluno.objects.create(usuario=self.destinatario, matricula='A-100')
    usr = Usuario.objects.create_user(
      email='responsavel@example.test', password='Senha@12345', nome='Responsável', perfil='RESP'
    )
    responsavel = Responsavel.objects.create(usuario=usr)
    request = RequestFactory().post('/admin/usuarios/alunoresponsavel/')
    request.user = self.admin
    painel = AlunoResponsavelAdmin(AlunoResponsavel, admin.site)
    vinculo = AlunoResponsavel(aluno=aluno, responsavel=responsavel)
    painel.save_model(request, vinculo, form=None, change=False)
    self.assertTrue(LogOperacao.objects.filter(
      evento='ADMIN_CRIOU_ALUNORESPONSAVEL', objeto_id=vinculo.pk
    ).exists())
