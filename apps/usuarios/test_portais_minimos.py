"""Testes do release executados apenas no SQLite (core.settings_test)."""
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Aluno, Responsavel, Professor, AlunoResponsavel
from apps.academico.models import Turma, Disciplina, Matricula, Aula


class PortaisMinimosTest(TestCase):
  def setUp(self):
    self.usuario = Usuario.objects.create_user(
      email='aluno.minimo@example.org', password='SenhaFort3!2026',
      nome='Aluno Sem Dados', perfil='ALUNO'
    )

  def test_entrada_separada_e_post_legado(self):
    resposta = self.client.get(reverse('login'))
    self.assertEqual(resposta.status_code, 200)
    self.assertContains(resposta, reverse('login_academico'))
    self.assertContains(resposta, reverse('login_funcionarios'))
    self.assertNotContains(resposta, 'type="password"')
    resposta = self.client.post(reverse('login'), {
      'email': self.usuario.email, 'senha': 'SenhaFort3!2026'
    })
    self.assertEqual(resposta.status_code, 302)

  def test_conta_sem_vinculo_nao_recebe_dados_inventados(self):
    self.client.force_login(self.usuario)
    resposta = self.client.get(reverse('dashboard'))
    self.assertEqual(resposta.status_code, 200)
    self.assertTemplateUsed(resposta, 'html/alunos/aluno.html')
    self.assertEqual(resposta.context['total_matriculas'], 0)
    self.assertIsNone(resposta.context['percentual_presenca'])
    self.assertContains(resposta, 'Sem matrícula ativa')
    self.assertNotContains(resposta, 'Trabalho de Banco de Dados')

  def test_responsavel_sem_vinculos_nao_ve_turma_alheia(self):
    responsavel_usuario = Usuario.objects.create_user(
      email='resp.minimo@example.org', password='SenhaFort3!2026',
      nome='Responsavel Vazio', perfil='RESP'
    )
    Responsavel.objects.create(usuario=responsavel_usuario)
    self.client.force_login(responsavel_usuario)
    resposta = self.client.get(reverse('dashboard'))
    self.assertEqual(resposta.status_code, 200)
    self.assertEqual(resposta.context['total_matriculas'], 0)
    self.assertContains(resposta, 'Nenhuma mensagem recebida')
    self.assertNotContains(resposta, 'Carlos Mendes')

  def test_professor_acessa_formularios_e_frequencia(self):
    usuario = Usuario.objects.create_user(
      email='prof.minimo@example.org', password='SenhaFort3!2026',
      nome='Professor Minimo', perfil='PROF'
    )
    Professor.objects.create(usuario=usuario, formacao='Licenciatura')
    self.client.force_login(usuario)
    for nome in ('registrar_aula_view', 'frequencia_painel', 'atividades_lista', 'comunicacao_painel'):
      with self.subTest(rota=nome):
        resposta = self.client.get(reverse(nome))
        self.assertEqual(resposta.status_code, 200)

  def test_registro_aula_post_persiste_sem_erro(self):
    usuario = Usuario.objects.create_user(
      email='aula.minima@example.org', password='SenhaFort3!2026',
      nome='Professor Aula', perfil='PROF'
    )
    professor = Professor.objects.create(usuario=usuario, formacao='Licenciatura')
    turma = Turma.objects.create(nome='Turma Teste', ano=2026, turno='MANHA', professor_regente=professor)
    disciplina = Disciplina.objects.create(nome='Matemática')
    disciplina.professores.add(professor)
    disciplina.turmas.add(turma)
    self.client.force_login(usuario)
    resposta = self.client.post(reverse('registrar_aula_view'), {
      'turma': str(turma.pk), 'disciplina': str(disciplina.pk),
      'data': '2026-10-18', 'conteudo': 'Aula sobre frações',
    })
    self.assertEqual(resposta.status_code, 302)
    self.assertTrue(Aula.objects.filter(turma=turma, professor=professor).exists())
