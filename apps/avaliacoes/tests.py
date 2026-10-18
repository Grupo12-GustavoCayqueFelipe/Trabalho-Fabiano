import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.academico.models import Disciplina, Matricula, Turma
from apps.usuarios.models import Aluno, Professor, Usuario, LogOperacao
from .models import Avaliacao, HistoricoNota, Nota


# Testa permissões de cada perfil com banco SQLite isolado do Supabase.
class AvaliacoesSegurancaTest(TestCase):
    def setUp(self):
        # Cria professor, aluno e usuário sem vínculo com os mesmos dados.
        self.usuario_prof = Usuario.objects.create_user(email='prof-av@teste.local', nome='Prof', perfil='PROF', password='Senha@12345')
        self.prof = Professor.objects.create(usuario=self.usuario_prof, formacao='Licenciatura')
        self.usuario_aluno = Usuario.objects.create_user(email='aluno-av@teste.local', nome='Aluno', perfil='ALUNO', password='Senha@12345')
        self.aluno = Aluno.objects.create(usuario=self.usuario_aluno, matricula='AV-01')
        self.usuario_estranho = Usuario.objects.create_user(email='estranho-av@teste.local', nome='Estranho', perfil='ALUNO', password='Senha@12345')
        self.estranho = Aluno.objects.create(usuario=self.usuario_estranho, matricula='AV-02')
        self.turma = Turma.objects.create(nome='7A', ano=2026, turno='MANHA')
        self.turma_outra = Turma.objects.create(nome='8B', ano=2026, turno='TARDE')
        self.disciplina = Disciplina.objects.create(nome='Matemática')
        self.disciplina.turmas.add(self.turma)
        self.disciplina.professores.add(self.prof)
        self.matricula = Matricula.objects.create(aluno=self.aluno, turma=self.turma, status='ATIVA')
        self.matricula_outra = Matricula.objects.create(aluno=self.estranho, turma=self.turma_outra, status='ATIVA')
        self.avaliacao = Avaliacao.objects.create(turma=self.turma, disciplina=self.disciplina, nome='Prova 1', data_avaliacao=datetime.date(2026, 10, 16), nota_maxima=Decimal('10'), peso=Decimal('1'))

    # Uma matrícula de outra turma nunca deve receber nota desta avaliação.
    def test_model_rejeita_matricula_de_outra_turma(self):
        nota = Nota(avaliacao=self.avaliacao, matricula=self.matricula_outra, valor=Decimal('8'))
        with self.assertRaises(ValidationError):
            nota.full_clean()

    # Aluno não pode lançar ou alterar notas, mesmo conhecendo a rota.
    def test_aluno_nao_lanca_nota(self):
        self.client.force_login(self.usuario_aluno)
        resposta = self.client.post(reverse('nota_salvar', args=[self.avaliacao.pk]), {'matricula': self.matricula.pk, 'valor': '10'})
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Nota.objects.exists())

    # Professor autorizado lança e corrige com eventos e valores anteriores.
    def test_lancamento_e_correcao_geram_historico(self):
        self.client.force_login(self.usuario_prof)
        url = reverse('nota_salvar', args=[self.avaliacao.pk])
        self.client.post(url, {'matricula': self.matricula.pk, 'valor': '7.50', 'observacao': 'Primeira correção'})
        self.client.post(url, {'matricula': self.matricula.pk, 'valor': '8.50', 'observacao': 'Nota revisada'})
        nota = Nota.objects.get()
        self.assertEqual(nota.valor, Decimal('8.50'))
        self.assertEqual(HistoricoNota.objects.filter(nota=nota).count(), 2)
        self.assertEqual(HistoricoNota.objects.filter(nota=nota).first().valor_anterior, Decimal('7.50'))
        self.assertEqual(LogOperacao.objects.filter(evento='NOTA_SALVA').count(), 2)

    # Aluno matriculado vê a própria nota, sem visualizar a de outra turma.
    def test_consulta_de_aluno_filtra_matricula(self):
        Nota.objects.create(avaliacao=self.avaliacao, matricula=self.matricula, valor=Decimal('9'))
        self.client.force_login(self.usuario_estranho)
        resposta = self.client.get(reverse('avaliacoes_painel'))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, '9 /')
