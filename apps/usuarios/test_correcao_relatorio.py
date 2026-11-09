"""Regressoes para o relatorio da disciplina. Usar sempre core.settings_test."""
from decimal import Decimal
import hashlib
import pyotp

from django.core.cache import cache
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.test import RequestFactory, TestCase, override_settings
from unittest.mock import patch
from django.urls import reverse

from apps.usuarios.models import (Usuario, Professor, Aluno, Responsavel,
    AlunoResponsavel, ConsentimentoUsuario, LogAcesso, LogRecuperacaoSenha, LogOperacao)
from apps.usuarios.views import _media_avaliacoes_normalizada


class CorrigirDesafioTOTPTest(TestCase):
  def setUp(self):
    cache.clear()
    self.usuario = Usuario.objects.create_user(
      email='totp-correcao@example.org', nome='TOTP Teste',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    self.usuario.otp_secret = pyotp.random_base32()
    self.usuario.otp_ativado = True
    self.usuario.save(update_fields=['otp_secret', 'otp_ativado'])

  def test_apos_cinco_erros_desafio_e_encerrado(self):
    self.client.post(reverse('login'), {
      'email': self.usuario.email, 'senha': 'SenhaFort3!2026'
    })
    for _ in range(5):
      self.client.post(reverse('2fa_verificar'), {'codigo': 'errado'})
    self.assertNotIn('pre_2fa_user_id', self.client.session)
    self.assertNotIn('pre_2fa_tentativas', self.client.session)
    self.client.post(reverse('2fa_verificar'), {
      'codigo': pyotp.TOTP(self.usuario.otp_secret).now()
    })
    self.assertNotIn('_auth_user_id', self.client.session)
    self.assertEqual(LogAcesso.objects.filter(usuario=self.usuario, evento='2FA_FALHA').count(), 5)

  def test_destino_e_limpo_quando_desafio_expira(self):
    self.client.post(reverse('login'), {
      'email': self.usuario.email, 'senha': 'SenhaFort3!2026', 'next': '/meus-dados/'
    })
    for _ in range(5):
      self.client.post(reverse('2fa_verificar'), {'codigo': 'invalido'})
    for chave in ('pre_2fa_user_id', 'pre_2fa_next', 'pre_2fa_portal', 'pre_2fa_iniciado'):
      self.assertNotIn(chave, self.client.session)


class RecuperacaoAuditoriaTest(TestCase):
  def setUp(self):
    cache.clear()

  def test_token_inexistente_gera_log_com_hash(self):
    token = 'token-que-nao-existe'
    self.client.get(reverse('redefinir_senha_view', args=[token]))
    log = LogRecuperacaoSenha.objects.get(evento='FALHA_TOKEN_INVALIDO')
    self.assertIsNone(log.usuario)
    self.assertEqual(log.token_hash, hashlib.sha256(token.encode()).hexdigest())

  def test_excesso_de_tokens_invalidos_e_limitado(self):
    for i in range(20):
      self.client.get(reverse('redefinir_senha_view', args=[f'nao-existe-{i}']))
    self.assertLessEqual(LogRecuperacaoSenha.objects.filter(evento='FALHA_TOKEN_INVALIDO').count(), 15)


class PermissaoDocenteRevogadaTest(TestCase):
  def setUp(self):
    cache.clear()
    self.usuario = Usuario.objects.create_user(
      email='docente-antigo@example.org', nome='Docente Antigo',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    # Simula o vinculo que continua no banco depois da troca de perfil.
    Professor.objects.create(usuario=self.usuario, formacao='Licenciatura')
    self.client.force_login(self.usuario)

  def test_perfil_aluno_nao_publica_atividade(self):
    resposta = self.client.post(reverse('atividade_criar'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_perfil_aluno_nao_cria_avaliacao(self):
    resposta = self.client.post(reverse('avaliacao_criar'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_perfil_aluno_nao_registra_aula(self):
    resposta = self.client.post(reverse('registrar_aula_view'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_perfil_aluno_nao_envia_aviso(self):
    resposta = self.client.post(reverse('aviso_criar'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))


class MediaPonderadaTest(TestCase):
  def test_media_respeita_peso_e_nota_maxima(self):
    class NotasFicticias:
      def values_list(self, *campos):
        return [(Decimal('5'), Decimal('10'), Decimal('1')),
                (Decimal('2'), Decimal('2'), Decimal('3'))]
    self.assertEqual(_media_avaliacoes_normalizada(NotasFicticias()), Decimal('8.75'))

  def test_media_sem_notas_retorna_none(self):
    class SemNotas:
      def values_list(self, *campos):
        return []
    self.assertIsNone(_media_avaliacoes_normalizada(SemNotas()))


class ExportacaoPorRepresentacaoTest(TestCase):
  def test_aluno_consulta_consentimentos_assinados_pelo_responsavel(self):
    aluno_usuario = Usuario.objects.create_user(
      email='aluno-export@example.org', nome='Aluno Export',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    aluno = Aluno.objects.create(usuario=aluno_usuario, matricula='EXP2026-1')
    resp_usuario = Usuario.objects.create_user(
      email='resp-export@example.org', nome='Responsavel Export',
      password='SenhaFort3!2026', perfil='RESP'
    )
    resp = Responsavel.objects.create(usuario=resp_usuario)
    AlunoResponsavel.objects.create(aluno=aluno, responsavel=resp, parentesco='Mae')
    ConsentimentoUsuario.objects.create(usuario=resp_usuario,
      aluno_representado=aluno, tipo='USO_IMAGEM', aceito=True)
    self.client.force_login(aluno_usuario)
    resposta = self.client.get(reverse('exportar_dados_view'))
    self.assertEqual(resposta.status_code, 200)
    self.assertEqual(len(resposta.json()['consentimentos_por_responsaveis']), 1)

  def test_responsavel_exporta_so_aluno_vinculado(self):
    resp_usuario = Usuario.objects.create_user(
      email='resp-export2@example.org', nome='Responsavel Export',
      password='SenhaFort3!2026', perfil='RESP'
    )
    resp = Responsavel.objects.create(usuario=resp_usuario)
    for i in range(2):
      u = Usuario.objects.create_user(
        email=f'aluno-exp-{i}@example.org', nome='Aluno',
        password='SenhaFort3!2026', perfil='ALUNO'
      )
      aluno = Aluno.objects.create(usuario=u, matricula=f'EXP2026-{i+2}')
      if i == 0:
        AlunoResponsavel.objects.create(aluno=aluno, responsavel=resp)
    self.client.force_login(resp_usuario)
    resposta = self.client.get(reverse('exportar_dados_view'))
    self.assertEqual(resposta.status_code, 200)
    dados = resposta.json()['dados_alunos_representados']
    self.assertEqual(len(dados), 1)
    self.assertEqual(dados[0]['matricula'], 'EXP2026-2')


class AuditoriaAdminSenhaTest(TestCase):
  def test_troca_de_senha_do_admin_registra_log_sem_gravar_conteudo(self):
    from django.contrib import admin
    gestor = Usuario.objects.create_superuser(
      email='admin-gestor@example.org', nome='Gestor Teste',
      password='SenhaFort3!2026'
    )
    alvo = Usuario.objects.create_user(
      email='alvo-admin-senha@example.org', nome='Alvo',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    requisicao = RequestFactory().post('/admin/usuarios/usuario/1/password/')
    requisicao.user = gestor
    # Isola a auditoria: a validacao real do formulario continua no UserAdmin.
    with patch.object(UserAdmin, 'user_change_password', return_value=HttpResponseRedirect('/admin/')):
      admin.site._registry[Usuario].user_change_password(requisicao, str(alvo.pk))
    self.assertTrue(LogOperacao.objects.filter(
      usuario=gestor, evento='ADMIN_SENHA_USUARIO', objeto_id=alvo.pk
    ).exists())

  def test_abertura_do_formulario_nao_registra_troca_de_senha(self):
    from django.contrib import admin
    gestor = Usuario.objects.create_superuser(
      email='admin-gestor2@example.org', nome='Gestor Teste',
      password='SenhaFort3!2026'
    )
    alvo = Usuario.objects.create_user(
      email='alvo-admin-senha2@example.org', nome='Alvo',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    requisicao = RequestFactory().get('/admin/usuarios/usuario/1/password/')
    requisicao.user = gestor
    with patch.object(UserAdmin, 'user_change_password', return_value=HttpResponseRedirect('/admin/')):
      admin.site._registry[Usuario].user_change_password(requisicao, str(alvo.pk))
    self.assertFalse(LogOperacao.objects.filter(evento='ADMIN_SENHA_USUARIO').exists())


class ComprovacaoControlesProducaoTest(TestCase):
  def test_hash_pbkdf2_usa_salt_diferente(self):
    primeiro = make_password('SenhaFort3!2026', hasher='pbkdf2_sha256')
    segundo = make_password('SenhaFort3!2026', hasher='pbkdf2_sha256')
    self.assertTrue(primeiro.startswith('pbkdf2_sha256$'))
    self.assertNotEqual(primeiro, segundo)

  @override_settings(SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=3600)
  def test_redirecionamento_https_e_hsts(self):
    resposta_http = self.client.get('/login/')
    self.assertEqual(resposta_http.status_code, 301)
    self.assertTrue(resposta_http['Location'].startswith('https://'))
    resposta_https = self.client.get('/login/', secure=True)
    self.assertIn('Strict-Transport-Security', resposta_https)

  def test_tempo_configurado_para_sessao(self):
    from django.conf import settings
    self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
    self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
    self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
