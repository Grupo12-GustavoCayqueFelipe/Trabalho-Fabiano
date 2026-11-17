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

    # Decimais com mais de 2 casas ou falha em full_clean retornam redirect 302 sem erro 500.
    def test_decimais_com_tres_casas_ou_validation_error_retornam_302(self):
        from unittest.mock import patch
        self.client.force_login(self.usuario_prof)
        resposta_av = self.client.post(reverse('avaliacao_criar'), {
            'nome': 'Avaliação Decimal',
            'turma': self.turma.pk,
            'disciplina': self.disciplina.pk,
            'data_avaliacao': '2026-10-20',
            'nota_maxima': '10.00',
            'peso': '1.234',
        })
        self.assertEqual(resposta_av.status_code, 302)
        self.assertFalse(Avaliacao.objects.filter(nome='Avaliação Decimal').exists())

        resposta_nota = self.client.post(
            reverse('nota_salvar', args=[self.avaliacao.pk]),
            {'matricula': self.matricula.pk, 'valor': '8.123'},
        )
        self.assertEqual(resposta_nota.status_code, 302)
        self.assertFalse(Nota.objects.filter(avaliacao=self.avaliacao).exists())

        # Garante captura de ValidationError disparado por full_clean na transação.
        with patch.object(Avaliacao, 'full_clean', side_effect=ValidationError('Erro de modelo')):
            resposta_clean_av = self.client.post(reverse('avaliacao_criar'), {
                'nome': 'Avaliação Clean',
                'turma': self.turma.pk,
                'disciplina': self.disciplina.pk,
                'data_avaliacao': '2026-10-20',
                'nota_maxima': '10.00',
                'peso': '1.00',
            })
            self.assertEqual(resposta_clean_av.status_code, 302)
            self.assertFalse(Avaliacao.objects.filter(nome='Avaliação Clean').exists())

        with patch.object(Nota, 'full_clean', side_effect=ValidationError('Erro de modelo')):
            resposta_clean_nota = self.client.post(
                reverse('nota_salvar', args=[self.avaliacao.pk]),
                {'matricula': self.matricula.pk, 'valor': '8.00'},
            )
            self.assertEqual(resposta_clean_nota.status_code, 302)
            self.assertFalse(Nota.objects.filter(avaliacao=self.avaliacao).exists())

    # O boletim consolida a média ponderada normalizada e a situação por disciplina.
    def test_resumo_consolidado_por_disciplina_no_painel(self):
        avaliacao_2 = Avaliacao.objects.create(
            turma=self.turma,
            disciplina=self.disciplina,
            nome='Trabalho Prático',
            data_avaliacao=datetime.date(2026, 10, 22),
            nota_maxima=Decimal('2.00'),
            peso=Decimal('3.00'),
        )
        Nota.objects.create(avaliacao=self.avaliacao, matricula=self.matricula, valor=Decimal('5.00'))
        Nota.objects.create(avaliacao=avaliacao_2, matricula=self.matricula, valor=Decimal('2.00'))

        self.client.force_login(self.usuario_aluno)
        resposta = self.client.get(reverse('avaliacoes_painel'))
        self.assertEqual(resposta.status_code, 200)
        resumo = resposta.context['resumo_disciplinas']
        self.assertEqual(len(resumo), 1)
        self.assertEqual(resumo[0]['disciplina'], self.disciplina)
        self.assertEqual(resumo[0]['media'], Decimal('8.75'))
        self.assertEqual(resumo[0]['situacao'], 'Aprovado')
        self.assertContains(resposta, 'Matemática')
        self.assertContains(resposta, 'Aprovado')
