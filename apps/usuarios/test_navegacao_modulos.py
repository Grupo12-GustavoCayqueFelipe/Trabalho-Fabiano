"""Verificações de navegação, isolamento de perfis e módulos do release."""
from django.test import TestCase
from django.urls import reverse
from apps.usuarios.models import Usuario


class NavegacaoModulosTest(TestCase):
  def setUp(self):
    self.admin = Usuario.objects.create_user(
      email='admin.navegacao@example.org', password='SenhaFort3!2026',
      nome='Admin Navegação', perfil='ADMIN'
    )
    self.aluno = Usuario.objects.create_user(
      email='aluno.navegacao@example.org', password='SenhaFort3!2026',
      nome='Aluno Navegação', perfil='ALUNO'
    )

  def test_gerenciamento_exige_autenticacao(self):
    resposta = self.client.get(reverse('gestao_usuarios'))
    self.assertEqual(resposta.status_code, 302)

  def test_aluno_nao_acessa_listagem_de_contas(self):
    self.client.force_login(self.aluno)
    resposta = self.client.get(reverse('gestao_usuarios'))
    self.assertEqual(resposta.status_code, 403)

  def test_admin_ve_usuario_sem_acesso_de_edicao(self):
    self.client.force_login(self.admin)
    resposta = self.client.get(reverse('gestao_usuarios'))
    self.assertEqual(resposta.status_code, 200)
    self.assertContains(resposta, 'Gestão de usuários')
    self.assertContains(resposta, self.aluno.email)
    self.assertNotContains(resposta, 'Abrir gerenciamento avançado no Django Admin')

  def test_login_portais_separados(self):
    resposta = self.client.get(reverse('login'))
    self.assertContains(resposta, reverse('login_academico'))
    self.assertContains(resposta, reverse('login_funcionarios'))
    self.assertContains(resposta, 'portal-entrada.css')

  def test_admin_tem_links_para_secoes_corretas(self):
    self.client.force_login(self.admin)
    resposta = self.client.get(reverse('dashboard'))
    self.assertEqual(resposta.status_code, 200)
    self.assertContains(resposta, reverse('gestao_usuarios'))
    self.assertContains(resposta, reverse('academico_painel_view') + '#periodos-letivos')
    self.assertContains(resposta, reverse('academico_painel_view') + '#matricula')
