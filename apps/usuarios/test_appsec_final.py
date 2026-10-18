"""Regressoes pontuais para controles do Django Admin (SQLite isolado)."""
import pyotp
from django.contrib import admin
from django.test import RequestFactory, TestCase

from .models import Usuario, Aluno, LogOperacao, TokenRecuperacaoSenha


class AdminRestritoAppSecTest(TestCase):
  # Um usuario staff com perfil de professor nao pode usar o Admin.
  def test_staff_professor_com_2fa_nao_acessa_admin(self):
    usuario = Usuario.objects.create_user(
      email='staff-prof-appsec@example.org', password='SenhaFort3!2026',
      nome='Professor Staff', perfil='PROF', is_staff=True,
    )
    usuario.otp_ativado = True
    usuario.otp_secret = pyotp.random_base32()
    usuario.save(update_fields=['otp_ativado', 'otp_secret'])
    self.client.force_login(usuario)
    sessao = self.client.session
    sessao['2fa_verificado'] = usuario.pk
    sessao.save()
    resposta = self.client.get('/admin/')
    self.assertNotEqual(resposta.status_code, 200)

  # O superusuario ADMIN com segundo fator validado continua autorizado.
  def test_superusuario_admin_com_2fa_consegue_acessar(self):
    usuario = Usuario.objects.create_superuser(
      email='staff-admin-appsec@example.org', password='SenhaFort3!2026',
      nome='Admin AppSec',
    )
    usuario.otp_ativado = True
    usuario.otp_secret = pyotp.random_base32()
    usuario.save(update_fields=['otp_ativado', 'otp_secret'])
    self.client.force_login(usuario)
    sessao = self.client.session
    sessao['2fa_verificado'] = usuario.pk
    sessao.save()
    self.assertEqual(self.client.get('/admin/').status_code, 200)

  # Tokens so sao criados pelo fluxo de recuperacao, nao pelo painel Admin.
  def test_tokens_recuperacao_nao_expostos_no_admin(self):
    self.assertNotIn(TokenRecuperacaoSenha, admin.site._registry)

  # A auditoria central registra edicoes no UserAdmin sem alterar senhas.
  def test_alteracao_usuario_gera_log_operacao(self):
    gestor = Usuario.objects.create_superuser(
      email='gestor-appsec@example.org', password='SenhaFort3!2026',
      nome='Gestor AppSec',
    )
    alvo = Usuario.objects.create_user(
      email='alvo-appsec@example.org', password='SenhaFort3!2026',
      nome='Usuario Original', perfil='ALUNO',
    )
    senha_anterior = alvo.password
    alvo.perfil = 'PROF'
    request = RequestFactory().post('/admin/usuarios/usuario/')
    request.user = gestor
    admin.site._registry[Usuario].save_model(request, alvo, None, True)
    self.assertTrue(LogOperacao.objects.filter(
      usuario=gestor, evento='ADMIN_ALTEROU_USUARIO', objeto_id=alvo.pk,
    ).exists())
    alvo.refresh_from_db()
    self.assertEqual(alvo.perfil, 'PROF')
    self.assertEqual(alvo.password, senha_anterior)

  # Alteracoes de perfis vinculados tambem geram LogOperacao.
  def test_alteracao_perfil_gera_log_operacao(self):
    gestor = Usuario.objects.create_superuser(
      email='gestor2-appsec@example.org', password='SenhaFort3!2026',
      nome='Gestor AppSec',
    )
    aluno_u = Usuario.objects.create_user(
      email='aluno-appsec@example.org', password='SenhaFort3!2026',
      nome='Aluno AppSec', perfil='ALUNO',
    )
    aluno = Aluno.objects.create(usuario=aluno_u, matricula='APPSEC-001')
    aluno.matricula = 'APPSEC-002'
    request = RequestFactory().post('/admin/usuarios/aluno/')
    request.user = gestor
    admin.site._registry[Aluno].save_model(request, aluno, None, True)
    self.assertTrue(LogOperacao.objects.filter(
      usuario=gestor, evento='ADMIN_ALTEROU_ALUNO', objeto_id=aluno.pk,
    ).exists())
    aluno.refresh_from_db()
    self.assertEqual(aluno.matricula, 'APPSEC-002')
