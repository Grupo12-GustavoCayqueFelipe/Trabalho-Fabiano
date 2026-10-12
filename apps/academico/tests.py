import datetime

from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .models import Turma, Disciplina, Matricula, Aula
from apps.usuarios.models import Usuario, Aluno, Professor, Responsavel, AlunoResponsavel


# Cria um usuário de cada perfil pra usar nos testes de permissão
class BaseAcademicoTest(TestCase):
  def setUp(self):
    self.admin = Usuario.objects.create_user(email='admin@t.com', password='Senha@12345', nome='Admin', perfil='ADMIN')

    usuario_prof = Usuario.objects.create_user(email='prof@t.com', password='Senha@12345', nome='Prof Um', perfil='PROF')
    self.professor = Professor.objects.create(usuario=usuario_prof, formacao='Matemática')
    self.usuario_prof = usuario_prof

    usuario_aluno = Usuario.objects.create_user(email='aluno@t.com', password='Senha@12345', nome='Aluno Um', perfil='ALUNO')
    self.aluno = Aluno.objects.create(usuario=usuario_aluno, matricula='A001', data_nascimento=datetime.date(2010, 1, 1))
    self.usuario_aluno = usuario_aluno

    self.turma = Turma.objects.create(nome='1A', ano=2026, turno='MANHA', professor_regente=self.professor)
    self.outra_turma = Turma.objects.create(nome='2B', ano=2026, turno='TARDE')


class PainelAcademicoTest(BaseAcademicoTest):
  # Aluno não entra no painel do admin, é mandado de volta pro dashboard
  def test_aluno_nao_acessa_painel(self):
    self.client.force_login(self.usuario_aluno)
    resposta = self.client.get(reverse('academico_painel_view'))
    self.assertRedirects(resposta, reverse('dashboard'), fetch_redirect_response=False)

  # Sem login manda pro login
  def test_painel_exige_login(self):
    resposta = self.client.get(reverse('academico_painel_view'))
    self.assertEqual(resposta.status_code, 302)

  # Admin vê o painel com as turmas cadastradas e o token CSRF nos formulários
  def test_admin_ve_painel_com_turmas(self):
    self.client.force_login(self.admin)
    resposta = self.client.get(reverse('academico_painel_view'))
    self.assertEqual(resposta.status_code, 200)
    self.assertContains(resposta, '1A')
    self.assertContains(resposta, 'csrfmiddlewaretoken')

  # Um id inválido na URL de edição não pode derrubar a página com erro 500
  def test_editar_com_id_invalido_nao_quebra(self):
    self.client.force_login(self.admin)
    for valor in ['abc', '99999', "1' OR '1'='1"]:
      resposta = self.client.get(reverse('academico_painel_view'), {'editar_turma': valor})
      self.assertEqual(resposta.status_code, 200)

  # Ao editar, o formulário vem preenchido com os dados da turma
  def test_editar_turma_preenche_formulario(self):
    self.client.force_login(self.admin)
    resposta = self.client.get(reverse('academico_painel_view'), {'editar_turma': self.turma.pk})
    self.assertContains(resposta, 'value="1A"')


class SalvarTurmaTest(BaseAcademicoTest):
  def dados(self, **extra):
    base = {'nome': '3C', 'ano': '2027', 'turno': 'NOITE', 'professor_regente': ''}
    base.update(extra)
    return base

  # Aluno logado não consegue criar turma nem mandando o POST na mão
  def test_aluno_nao_cria_turma(self):
    self.client.force_login(self.usuario_aluno)
    self.client.post(reverse('salvar_turma_view'), self.dados())
    self.assertFalse(Turma.objects.filter(nome='3C').exists())

  # Professor também não
  def test_professor_nao_cria_turma(self):
    self.client.force_login(self.usuario_prof)
    self.client.post(reverse('salvar_turma_view'), self.dados())
    self.assertFalse(Turma.objects.filter(nome='3C').exists())

  def test_admin_cria_turma(self):
    self.client.force_login(self.admin)
    self.client.post(reverse('salvar_turma_view'), self.dados(professor_regente=self.professor.pk))
    turma = Turma.objects.get(nome='3C')
    self.assertEqual(turma.ano, 2027)
    self.assertEqual(turma.professor_regente, self.professor)

  def test_admin_edita_turma_existente(self):
    self.client.force_login(self.admin)
    self.client.post(reverse('salvar_turma_view'), self.dados(pk=self.turma.pk, nome='1A Editada'))
    self.turma.refresh_from_db()
    self.assertEqual(self.turma.nome, '1A Editada')
    self.assertEqual(Turma.objects.count(), 2)

  # Dados inválidos não criam nada e não dão erro 500
  def test_dados_invalidos_nao_criam_turma(self):
    self.client.force_login(self.admin)
    for ruim in [{'ano': 'abc'}, {'turno': 'MADRUGADA'}, {'nome': '   '}]:
      resposta = self.client.post(reverse('salvar_turma_view'), self.dados(**ruim))
      self.assertEqual(resposta.status_code, 302)
    self.assertEqual(Turma.objects.count(), 2)

  # A ação de salvar só aceita POST
  def test_get_nao_permitido(self):
    self.client.force_login(self.admin)
    resposta = self.client.get(reverse('salvar_turma_view'))
    self.assertEqual(resposta.status_code, 405)


class SalvarDisciplinaTest(BaseAcademicoTest):
  def test_aluno_nao_cria_disciplina(self):
    self.client.force_login(self.usuario_aluno)
    self.client.post(reverse('salvar_disciplina_view'), {'nome': 'Física'})
    self.assertFalse(Disciplina.objects.filter(nome='Física').exists())

  # Admin cria a disciplina já vinculando turmas e professores (campo no plural)
  def test_admin_cria_disciplina_com_vinculos(self):
    self.client.force_login(self.admin)
    self.client.post(reverse('salvar_disciplina_view'), {
      'nome': 'Física', 'turmas': [self.turma.pk, self.outra_turma.pk], 'professores': [self.professor.pk],
    })
    disciplina = Disciplina.objects.get(nome='Física')
    self.assertEqual(disciplina.turmas.count(), 2)
    self.assertEqual(list(disciplina.professores.all()), [self.professor])

  # Ids que não existem são ignorados em vez de quebrar
  def test_ids_inexistentes_sao_ignorados(self):
    self.client.force_login(self.admin)
    resposta = self.client.post(reverse('salvar_disciplina_view'), {'nome': 'Química', 'turmas': ['99999', 'abc']})
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(Disciplina.objects.get(nome='Química').turmas.count(), 0)


class MatriculaTest(BaseAcademicoTest):
  def test_aluno_nao_matricula(self):
    self.client.force_login(self.usuario_aluno)
    self.client.post(reverse('matricular_aluno_view'), {'aluno': self.aluno.pk, 'turma': self.turma.pk})
    self.assertEqual(Matricula.objects.count(), 0)

  def test_admin_matricula_aluno(self):
    self.client.force_login(self.admin)
    self.client.post(reverse('matricular_aluno_view'), {'aluno': self.aluno.pk, 'turma': self.turma.pk})
    self.assertEqual(Matricula.objects.get().status, 'ATIVA')

  # Matricular duas vezes na mesma turma não duplica e não dá erro 500
  def test_matricula_repetida_nao_duplica(self):
    self.client.force_login(self.admin)
    for _ in range(2):
      resposta = self.client.post(reverse('matricular_aluno_view'), {'aluno': self.aluno.pk, 'turma': self.turma.pk})
      self.assertEqual(resposta.status_code, 302)
    self.assertEqual(Matricula.objects.count(), 1)

  # Matrícula cancelada na mesma turma é reativada em vez de bater na regra de unicidade
  def test_matricula_cancelada_e_reativada(self):
    Matricula.objects.create(aluno=self.aluno, turma=self.turma, status='CANCELADA')
    self.client.force_login(self.admin)
    self.client.post(reverse('matricular_aluno_view'), {'aluno': self.aluno.pk, 'turma': self.turma.pk})
    self.assertEqual(Matricula.objects.get().status, 'ATIVA')

  def test_sem_selecionar_nada_nao_quebra(self):
    self.client.force_login(self.admin)
    resposta = self.client.post(reverse('matricular_aluno_view'), {'aluno': '', 'turma': ''})
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(Matricula.objects.count(), 0)


class HistoricoMatriculasTest(BaseAcademicoTest):
  # Aluno vê só as próprias matrículas
  def test_aluno_ve_apenas_as_proprias(self):
    outro_usuario = Usuario.objects.create_user(email='outro@t.com', password='Senha@12345', nome='Outro', perfil='ALUNO')
    outro = Aluno.objects.create(usuario=outro_usuario, matricula='A002', data_nascimento=datetime.date(2010, 2, 2))
    Matricula.objects.create(aluno=self.aluno, turma=self.turma)
    Matricula.objects.create(aluno=outro, turma=self.outra_turma)

    self.client.force_login(self.usuario_aluno)
    resposta = self.client.get(reverse('historico_matriculas_view'))
    self.assertContains(resposta, '1A')
    self.assertNotContains(resposta, '2B')

  # Responsável vê as matrículas do aluno vinculado a ele
  def test_responsavel_ve_aluno_vinculado(self):
    usuario_resp = Usuario.objects.create_user(email='resp@t.com', password='Senha@12345', nome='Resp', perfil='RESP')
    resp = Responsavel.objects.create(usuario=usuario_resp)
    AlunoResponsavel.objects.create(aluno=self.aluno, responsavel=resp, parentesco='Mãe')
    Matricula.objects.create(aluno=self.aluno, turma=self.turma)

    self.client.force_login(usuario_resp)
    resposta = self.client.get(reverse('historico_matriculas_view'))
    self.assertContains(resposta, 'Aluno Um')
    self.assertContains(resposta, '1A')

  # Quem não é aluno nem responsável abre a tela sem ver matrícula de ninguém
  def test_professor_nao_ve_matriculas_alheias(self):
    Matricula.objects.create(aluno=self.aluno, turma=self.turma)
    self.client.force_login(self.usuario_prof)
    resposta = self.client.get(reverse('historico_matriculas_view'))
    self.assertEqual(resposta.status_code, 200)
    self.assertNotContains(resposta, 'Aluno Um')


class RegistrarAulaTest(BaseAcademicoTest):
  def setUp(self):
    super().setUp()
    self.disciplina = Disciplina.objects.create(nome='Matemática')
    self.disciplina.turmas.add(self.turma)
    self.disciplina.professores.add(self.professor)
    self.dados = {
      'turma': self.turma.pk, 'disciplina': self.disciplina.pk,
      'data': '2026-03-10', 'conteudo': 'Frações',
    }

  def test_aluno_nao_registra_aula(self):
    self.client.force_login(self.usuario_aluno)
    self.client.post(reverse('registrar_aula_view'), self.dados)
    self.assertEqual(Aula.objects.count(), 0)

  def test_professor_registra_aula(self):
    self.client.force_login(self.usuario_prof)
    self.client.post(reverse('registrar_aula_view'), self.dados)
    aula = Aula.objects.get()
    self.assertEqual(aula.professor, self.professor)
    self.assertEqual(aula.conteudo, 'Frações')

  # Professor não registra aula numa turma que não é dele
  def test_professor_nao_registra_em_turma_alheia(self):
    self.client.force_login(self.usuario_prof)
    self.client.post(reverse('registrar_aula_view'), {**self.dados, 'turma': self.outra_turma.pk})
    self.assertEqual(Aula.objects.count(), 0)

  # Disciplina que não é oferecida na turma escolhida é recusada
  def test_disciplina_fora_da_turma_e_recusada(self):
    self.disciplina.turmas.remove(self.turma)
    self.client.force_login(self.usuario_prof)
    self.client.post(reverse('registrar_aula_view'), self.dados)
    self.assertEqual(Aula.objects.count(), 0)

  # Data inválida e conteúdo vazio não criam aula nem dão erro 500
  def test_dados_invalidos_nao_criam_aula(self):
    self.client.force_login(self.usuario_prof)
    for ruim in [{'data': '31/02/2026'}, {'data': ''}, {'conteudo': '   '}]:
      resposta = self.client.post(reverse('registrar_aula_view'), {**self.dados, **ruim})
      self.assertEqual(resposta.status_code, 302)
    self.assertEqual(Aula.objects.count(), 0)

  # Professor que só leciona a disciplina na turma (sem ser regente) também consegue registrar
  def test_professor_nao_regente_registra_aula(self):
    self.turma.professor_regente = None
    self.turma.save()
    self.client.force_login(self.usuario_prof)
    resposta = self.client.get(reverse('registrar_aula_view'))
    self.assertContains(resposta, '1A')


class ProtecaoDeHistoricoTest(BaseAcademicoTest):
  # Turma com matrícula não pode ser apagada
  def test_turma_com_matricula_nao_e_apagada(self):
    Matricula.objects.create(aluno=self.aluno, turma=self.turma)
    with self.assertRaises(ProtectedError):
      self.turma.delete()

  # Disciplina com aula registrada não pode ser apagada
  def test_disciplina_com_aula_nao_e_apagada(self):
    disciplina = Disciplina.objects.create(nome='Artes')
    Aula.objects.create(turma=self.turma, disciplina=disciplina, professor=self.professor, data=datetime.date(2026, 3, 1))
    with self.assertRaises(ProtectedError):
      disciplina.delete()
