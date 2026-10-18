"""Regressões do parâmetro next nos dois portais e no TOTP (SQLite de testes)."""

import pyotp
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Usuario


SENHA = 'SenhaTeste@2026'


class RetornoAoPortalTest(TestCase):
  def setUp(self):
    cache.clear()
    self.aluno = Usuario.objects.create_user(
      email='aluno-retorno@example.invalid', nome='Aluno Retorno',
      perfil='ALUNO', password=SENHA,
    )
    self.admin = Usuario.objects.create_user(
      email='admin-retorno@example.invalid', nome='Admin Retorno',
      perfil='ADMIN', password=SENHA,
    )

  # A rota protegida continua exigindo autenticação antes de mostrar os dados.
  def test_pagina_privada_encaminha_para_escolha_do_portal(self):
    resposta = self.client.get(reverse('meus_dados_view'))
    self.assertRedirects(
      resposta, reverse('login') + '?next=' + reverse('meus_dados_view'),
      fetch_redirect_response=False,
    )

  # O seletor mantém o destino para os dois formulários sem escolher o perfil.
  def test_seletor_repassa_destino_para_os_portais(self):
    resposta = self.client.get(reverse('login'), {'next': '/frequencia/'})
    self.assertContains(resposta,'href="/login/?next=/frequencia/"')
    self.assertContains(resposta,'href="/funcionarios/login/?next=/frequencia/"')

  # O formulário acadêmico guarda o caminho na próxima requisição POST.
  def test_formulario_mantem_next_em_campo_oculto(self):
    resposta = self.client.get(reverse('login_academico'), {'next': '/meus-dados/'})
    self.assertContains(resposta, 'name="next" value="/meus-dados/"')

  # Com senha certa, o retorno funciona sem abrir mão do login por perfil.
  def test_login_aluno_retorna_a_pagina_interna(self):
    resposta = self.client.post(reverse('login_academico'), {
      'email': self.aluno.email, 'senha': SENHA, 'next': '/meus-dados/',
    })
    self.assertRedirects(resposta, '/meus-dados/', fetch_redirect_response=False)
    self.assertIn('_auth_user_id', self.client.session)

  # Mesmo depois de errar a senha, o formulário preserva a página solicitada.
  def test_senha_errada_nao_perde_next(self):
    resposta = self.client.post(reverse('login_academico'), {
      'email': self.aluno.email, 'senha': 'SenhaErrada!2026',
      'next': '/meus-dados/',
    })
    self.assertEqual(resposta.status_code, 200)
    self.assertContains(resposta, 'name="next" value="/meus-dados/"')

  # O POST legado da raiz continua funcionando para clientes e testes antigos.
  def test_login_legado_tambem_preserva_next(self):
    resposta = self.client.post(reverse('login'), {
      'email': self.aluno.email, 'senha': SENHA, 'next': '/meus-dados/',
    })
    self.assertRedirects(resposta, '/meus-dados/', fetch_redirect_response=False)

  # URLs absolutas, de outro host ou com barra invertida nunca viram redirecionamento.
  def test_redirecionamentos_externos_sao_rejeitados(self):
    destinos = (
      'https://site-externo.example/phishing',
      '//site-externo.example/phishing',
      '/\\site-externo.example/',
      'https://testserver/meus-dados/',
    )
    for destino in destinos:
      with self.subTest(destino=destino):
        cache.clear()
        resposta = self.client.post(reverse('login_academico'), {
          'email': self.aluno.email, 'senha': SENHA, 'next': destino,
        })
        self.assertRedirects(resposta, reverse('dashboard'), fetch_redirect_response=False)
        self.client.logout()

  # A presença de next não permite autenticar o perfil na tela errada.
  def test_conta_admin_nao_pode_entrar_pelo_portal_de_aluno(self):
    resposta = self.client.post(reverse('login_academico'), {
      'email': self.admin.email, 'senha': SENHA, 'next': '/admin/',
    })
    self.assertEqual(resposta.status_code, 200)
    self.assertNotIn('_auth_user_id', self.client.session)

  # A URL de retorno não concede acesso a páginas administrativas de outro perfil.
  def test_destino_proibido_continua_protegido(self):
    resposta = self.client.post(reverse('login_academico'), {
      'email': self.aluno.email, 'senha': SENHA, 'next': '/academico/',
    })
    self.assertRedirects(resposta, '/academico/', fetch_redirect_response=False)
    bloqueio = self.client.get('/academico/')
    self.assertNotEqual(bloqueio.status_code, 200)

  # Sem parâmetro next, mantém a navegação padrão para o dashboard.
  def test_login_sem_next_mantem_dashboard(self):
    resposta = self.client.post(reverse('login_academico'), {
      'email': self.aluno.email, 'senha': SENHA,
    })
    self.assertRedirects(resposta, reverse('dashboard'), fetch_redirect_response=False)

  # A escolha do portal não se transforma em formulário, mesmo com next inválido.
  def test_entrada_nao_propaga_next_externo(self):
    resposta = self.client.get(reverse('login'), {'next': '//site-externo.example/'})
    self.assertNotContains(resposta, '?next=')


class RetornoComDoisFatoresTest(TestCase):
  def setUp(self):
    cache.clear()
    self.usuario = Usuario.objects.create_user(
      email='admin-2fa-retorno@example.invalid', nome='Admin Dois Fatores',
      perfil='ADMIN', password=SENHA,
    )
    self.usuario.otp_secret = pyotp.random_base32()
    self.usuario.otp_ativado = True
    self.usuario.save(update_fields=['otp_secret', 'otp_ativado'])

  # Só a senha gera a sessão temporária, não a autenticação definitiva.
  def test_next_e_preservado_ate_validar_o_totp(self):
    resposta = self.client.post(reverse('login_funcionarios'), {
      'email': self.usuario.email, 'senha': SENHA,
      'next': '/academico/',
    })
    self.assertRedirects(resposta, reverse('2fa_verificar'), fetch_redirect_response=False)
    self.assertNotIn('_auth_user_id', self.client.session)
    self.assertEqual(self.client.session.get('pre_2fa_next'), '/academico/')

    # Código incorreto não autentica nem descarta a página solicitada.
    resposta = self.client.post(reverse('2fa_verificar'), {'codigo': 'xyz'})
    self.assertEqual(resposta.status_code, 200)
    self.assertNotIn('_auth_user_id', self.client.session)
    self.assertEqual(self.client.session.get('pre_2fa_next'), '/academico/')

    # Após conferir o TOTP, o navegador é enviado ao destino solicitado.
    codigo = pyotp.TOTP(self.usuario.otp_secret).now()
    resposta = self.client.post(reverse('2fa_verificar'), {'codigo': codigo})
    self.assertRedirects(resposta, '/academico/', fetch_redirect_response=False)
    self.assertIn('_auth_user_id', self.client.session)
    self.assertNotIn('pre_2fa_next', self.client.session)

  # Com destino externo ou ausente, o 2FA retorna ao dashboard normal.
  def test_totp_sem_destino_valido_volta_ao_dashboard(self):
    self.client.post(reverse('login_funcionarios'), {
      'email': self.usuario.email, 'senha': SENHA,
      'next': '//site-externo.example/',
    })
    codigo = pyotp.TOTP(self.usuario.otp_secret).now()
    resposta = self.client.post(reverse('2fa_verificar'), {'codigo': codigo})
    self.assertRedirects(resposta, reverse('dashboard'), fetch_redirect_response=False)
