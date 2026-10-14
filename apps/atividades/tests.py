import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academico.models import Turma, Disciplina, Matricula
from apps.usuarios.models import Usuario, Professor, Aluno, LogOperacao
from .models import Atividade, Entrega


# Os testes usam SQLite isolado, sem acessar banco ou S3 de produção.
class AtividadesSegurancaTest(TestCase):
    def setUp(self):
        self.prof_user = Usuario.objects.create_user(email='prof@teste.local', password='Senha@12345', nome='Prof', perfil='PROF')
        self.prof = Professor.objects.create(usuario=self.prof_user, formacao='Licenciatura')
        self.outro_user = Usuario.objects.create_user(email='outro@teste.local', password='Senha@12345', nome='Outro', perfil='PROF')
        self.outro = Professor.objects.create(usuario=self.outro_user, formacao='Licenciatura')
        self.aluno_user = Usuario.objects.create_user(email='aluno@teste.local', password='Senha@12345', nome='Aluno', perfil='ALUNO')
        self.aluno = Aluno.objects.create(usuario=self.aluno_user, matricula='AL-01', data_nascimento=datetime.date(2008, 4, 8))
        self.outro_aluno_user = Usuario.objects.create_user(email='estranho@teste.local', password='Senha@12345', nome='Estranho', perfil='ALUNO')
        self.outro_aluno = Aluno.objects.create(usuario=self.outro_aluno_user, matricula='AL-02', data_nascimento=datetime.date(2008, 4, 8))
        self.turma = Turma.objects.create(nome='7A', ano=2026, turno='MANHA', professor_regente=self.prof)
        self.disciplina = Disciplina.objects.create(nome='Português')
        self.disciplina.turmas.add(self.turma)
        self.disciplina.professores.add(self.prof)
        Matricula.objects.create(aluno=self.aluno, turma=self.turma, status='ATIVA')
        self.atividade = Atividade.objects.create(titulo='Redação', descricao='Escreva um texto', turma=self.turma, disciplina=self.disciplina, professor=self.prof, prazo=timezone.now() + datetime.timedelta(days=2))

    def test_anonimo_e_redirecionado(self):
        resposta = self.client.get(reverse('atividades_lista'))
        self.assertEqual(resposta.status_code, 302)

    def test_outro_aluno_nao_acessa_atividade(self):
        self.client.force_login(self.outro_aluno_user)
        resposta = self.client.get(reverse('atividade_detalhe', args=[self.atividade.pk]))
        self.assertEqual(resposta.status_code, 302)
        resposta = self.client.post(reverse('entrega_salvar', args=[self.atividade.pk]), {'resposta': 'Invasão'})
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Entrega.objects.exists())

    def test_outro_professor_nao_corrige(self):
        entrega = Entrega.objects.create(atividade=self.atividade, aluno=self.aluno, resposta='Minha resposta')
        self.client.force_login(self.outro_user)
        self.client.post(reverse('entrega_corrigir', args=[self.atividade.pk, entrega.pk]), {'nota': '10'})
        entrega.refresh_from_db()
        self.assertIsNone(entrega.nota)

    def test_professor_nao_publica_em_turma_estranha(self):
        self.client.force_login(self.outro_user)
        resposta = self.client.post(reverse('atividade_criar'), {
            'titulo': 'Invasão', 'descricao': 'Descrição', 'turma': self.turma.pk,
            'disciplina': self.disciplina.pk, 'prazo': (timezone.now() + datetime.timedelta(days=2)).isoformat(),
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Atividade.objects.count(), 1)

    def test_aluno_entrega_uma_vez_e_professor_corrige(self):
        self.client.force_login(self.aluno_user)
        destino = reverse('entrega_salvar', args=[self.atividade.pk])
        self.client.post(destino, {'resposta': 'Primeira versão'})
        self.client.post(destino, {'resposta': 'Texto final'})
        self.assertEqual(Entrega.objects.count(), 1)
        entrega = Entrega.objects.get()
        self.assertEqual(entrega.resposta, 'Texto final')
        self.client.force_login(self.prof_user)
        self.client.post(reverse('entrega_corrigir', args=[self.atividade.pk, entrega.pk]), {'nota': '8.50', 'comentario': 'Bom'})
        entrega.refresh_from_db()
        self.assertEqual(str(entrega.nota), '8.50')
        self.assertEqual(entrega.comentario_professor, 'Bom')
        self.assertTrue(LogOperacao.objects.filter(evento='ENTREGA_CORRIGIDA').exists())
        self.client.force_login(self.aluno_user)
        self.client.post(destino, {'resposta': 'Alterar após correção'})
        entrega.refresh_from_db()
        self.assertEqual(entrega.resposta, 'Texto final')

    def test_entrega_fora_do_prazo_e_bloqueada(self):
        self.atividade.prazo = timezone.now() - datetime.timedelta(seconds=1)
        self.atividade.save()
        self.client.force_login(self.aluno_user)
        self.client.post(reverse('entrega_salvar', args=[self.atividade.pk]), {'resposta': 'Atrasada'})
        self.assertFalse(Entrega.objects.exists())

    def test_id_de_turma_excessivo_nao_gera_erro_500(self):
        self.client.force_login(self.prof_user)
        resposta = self.client.post(reverse('atividade_criar'), {
            'titulo': 'Teste', 'descricao': 'Descrição', 'turma': '9999999999999999999',
            'disciplina': self.disciplina.pk,
            'prazo': (timezone.now() + datetime.timedelta(days=2)).isoformat(),
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Atividade.objects.count(), 1)
