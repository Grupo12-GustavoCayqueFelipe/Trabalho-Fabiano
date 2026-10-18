# Testes de privacidade cadastral e bloqueio de exclusão física.
from django.contrib import admin
from django.test import TestCase
from django.urls import reverse

from .admin import UsuarioAdmin
from .models import Aluno, LogOperacao, Usuario


class UsuariosEntregaTest(TestCase):
  def setUp(self):
    self.usuario = Usuario.objects.create_user(
      email='cadastro@example.test', password='Senha@12345', nome='Pessoa', perfil='ALUNO'
    )
    Aluno.objects.create(usuario=self.usuario, matricula='A-300')

  def test_django_admin_nao_pode_excluir_usuario(self):
    painel = UsuarioAdmin(Usuario, admin.site)
    self.assertFalse(painel.has_delete_permission(None, self.usuario))

  def test_atualizacao_telefone_gera_auditoria(self):
    self.client.force_login(self.usuario)
    resposta = self.client.post(reverse('atualizar_telefone_view'), {
      'telefone': '11912345678',
    })
    self.assertEqual(resposta.status_code, 302)
    self.assertTrue(LogOperacao.objects.filter(
      usuario=self.usuario, evento='TELEFONE_ATUALIZADO'
    ).exists())
    self.usuario.aluno.refresh_from_db()
    self.assertEqual(self.usuario.aluno.telefone, '11912345678')

  def test_exportacao_dados_tem_no_store(self):
    self.client.force_login(self.usuario)
    resposta = self.client.get(reverse('exportar_dados_view'))
    self.assertEqual(resposta.status_code, 200)
    self.assertIn('no-store', resposta.get('Cache-Control', ''))
