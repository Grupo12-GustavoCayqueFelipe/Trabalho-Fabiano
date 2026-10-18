import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.academico.models import Aula, Disciplina, Matricula, Turma
from apps.usuarios.models import Aluno, Professor, Usuario, LogOperacao
from .models import HistoricoFrequencia, RegistroFrequencia


# Protege a chamada e o histórico dos alunos contra alteração não autorizada.
class FrequenciaSegurancaTest(TestCase):
    def setUp(self):
        self.usuario_prof = Usuario.objects.create_user(email='prof-fr@teste.local', nome='Prof', perfil='PROF', password='Senha@12345')
        self.prof = Professor.objects.create(usuario=self.usuario_prof, formacao='Licenciatura')
        self.usuario_aluno = Usuario.objects.create_user(email='aluno-fr@teste.local', nome='Aluno', perfil='ALUNO', password='Senha@12345')
        self.aluno = Aluno.objects.create(usuario=self.usuario_aluno, matricula='FR-01')
        self.turma = Turma.objects.create(nome='9A', ano=2026, turno='MANHA')
        self.turma_outra = Turma.objects.create(nome='9B', ano=2026, turno='TARDE')
        self.disciplina = Disciplina.objects.create(nome='História')
        self.disciplina.turmas.add(self.turma)
        self.disciplina.professores.add(self.prof)
        self.matricula = Matricula.objects.create(aluno=self.aluno, turma=self.turma, status='ATIVA')
        self.matricula_outra = Matricula.objects.create(aluno=self.aluno, turma=self.turma_outra, status='ATIVA')
        self.aula = Aula.objects.create(turma=self.turma, disciplina=self.disciplina, professor=self.prof, data=datetime.date(2026, 10, 16), conteudo='História')

    # O model recusa falta vinculada à matrícula de turma incorreta.
    def test_model_rejeita_turma_incorreta(self):
        registro = RegistroFrequencia(aula=self.aula, matricula=self.matricula_outra, status='F')
        with self.assertRaises(ValidationError):
            registro.full_clean()

    # Aluno não pode marcar presença para si mesmo por POST.
    def test_aluno_nao_lanca_frequencia(self):
        self.client.force_login(self.usuario_aluno)
        resposta = self.client.post(reverse('frequencia_salvar', args=[self.aula.pk]), {'matricula': self.matricula.pk, 'status': 'P'})
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(RegistroFrequencia.objects.exists())

    # Falta justificada sem motivo é rejeitada sem criar registros.
    def test_falta_justificada_exige_motivo(self):
        self.client.force_login(self.usuario_prof)
        self.client.post(reverse('frequencia_salvar', args=[self.aula.pk]), {'matricula': self.matricula.pk, 'status': 'J'})
        self.assertFalse(RegistroFrequencia.objects.exists())

    # A correção da chamada registra os estados anteriores e os eventos.
    def test_correcao_preserva_historico(self):
        self.client.force_login(self.usuario_prof)
        url = reverse('frequencia_salvar', args=[self.aula.pk])
        self.client.post(url, {'matricula': self.matricula.pk, 'status': 'P'})
        self.client.post(url, {'matricula': self.matricula.pk, 'status': 'J', 'justificativa': 'Declaração apresentada'})
        registro = RegistroFrequencia.objects.get()
        self.assertEqual(registro.status, 'J')
        self.assertEqual(HistoricoFrequencia.objects.filter(registro=registro).count(), 2)
        self.assertEqual(HistoricoFrequencia.objects.filter(registro=registro).first().status_anterior, 'P')
        self.assertEqual(LogOperacao.objects.filter(evento='FREQUENCIA_SALVA').count(), 2)
