# Evita registrar aula em data incompatível com o período escolar.
import datetime

from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Professor, Usuario
from .models import Aula, Disciplina, PeriodoLetivo, Turma


class AulasPeriodoTest(TestCase):
  def setUp(self):
    usuario = Usuario.objects.create_user(
      email='docente@example.test', password='Senha@12345', nome='Docente', perfil='PROF',
    )
    self.professor = Professor.objects.create(usuario=usuario, formacao='Ensino')
    self.client.force_login(usuario)
    periodo = PeriodoLetivo.objects.create(
      ano=2026, semestre=1, data_inicio=datetime.date(2026, 2, 1), data_fim=datetime.date(2026, 6, 30)
    )
    self.turma = Turma.objects.create(
      nome='A1', ano=2026, turno='MANHA', professor_regente=self.professor, periodo_letivo=periodo
    )
    self.disciplina = Disciplina.objects.create(nome='História')
    self.disciplina.turmas.add(self.turma)
    self.disciplina.professores.add(self.professor)

  def test_aula_fora_do_periodo_rejeitada(self):
    resposta = self.client.post(reverse('registrar_aula_view'), {
      'turma': self.turma.pk, 'disciplina': self.disciplina.pk,
      'data': '2026-07-01', 'conteudo': 'Revisão',
    })
    self.assertEqual(resposta.status_code, 302)
    self.assertFalse(Aula.objects.exists())

  def test_aula_dentro_do_periodo_autorizada(self):
    resposta = self.client.post(reverse('registrar_aula_view'), {
      'turma': self.turma.pk, 'disciplina': self.disciplina.pk,
      'data': '2026-06-30', 'conteudo': 'Revisão',
    })
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(Aula.objects.count(), 1)
