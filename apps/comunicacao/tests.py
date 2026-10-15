import datetime
from django.test import TestCase
from django.urls import reverse
from apps.academico.models import Turma, Matricula
from apps.usuarios.models import Usuario, Professor, Aluno, Responsavel, AlunoResponsavel
from .models import Aviso, Mensagem


# Testa autorização no servidor, independentemente dos campos HTML.
class ComunicacaoSegurancaTest(TestCase):
    def setUp(self):
        self.adm = Usuario.objects.create_user(email='admin@teste.local', password='Senha@12345', nome='Admin', perfil='ADMIN')
        self.prof_user = Usuario.objects.create_user(email='prof@teste.local', password='Senha@12345', nome='Professor', perfil='PROF')
        self.prof = Professor.objects.create(usuario=self.prof_user, formacao='Pedagogia')
        self.outra_prof_user = Usuario.objects.create_user(email='outro@teste.local', password='Senha@12345', nome='Outro', perfil='PROF')
        self.outra_prof = Professor.objects.create(usuario=self.outra_prof_user, formacao='Pedagogia')
        self.aluno_user = Usuario.objects.create_user(email='aluno@teste.local', password='Senha@12345', nome='Aluno', perfil='ALUNO')
        self.aluno = Aluno.objects.create(usuario=self.aluno_user, matricula='A-01', data_nascimento=datetime.date(2009, 1, 1))
        self.estranho_user = Usuario.objects.create_user(email='estranho@teste.local', password='Senha@12345', nome='Estranho', perfil='ALUNO')
        self.estranho = Aluno.objects.create(usuario=self.estranho_user, matricula='A-02', data_nascimento=datetime.date(2009, 1, 1))
        self.resp_user = Usuario.objects.create_user(email='resp@teste.local', password='Senha@12345', nome='Responsável', perfil='RESP')
        self.resp = Responsavel.objects.create(usuario=self.resp_user)
        AlunoResponsavel.objects.create(aluno=self.aluno, responsavel=self.resp)
        self.turma = Turma.objects.create(nome='8B', ano=2026, turno='TARDE', professor_regente=self.prof)
        self.outra_turma = Turma.objects.create(nome='8C', ano=2026, turno='TARDE', professor_regente=self.outra_prof)
        Matricula.objects.create(aluno=self.aluno, turma=self.turma, status='ATIVA')
        Matricula.objects.create(aluno=self.estranho, turma=self.outra_turma, status='ATIVA')

    def test_aluno_nao_publica_aviso(self):
        self.client.force_login(self.aluno_user)
        self.client.post(reverse('aviso_criar'), {'titulo': 'Falso', 'texto': 'Texto', 'turma': self.turma.pk})
        self.assertFalse(Aviso.objects.exists())

    def test_professor_nao_publica_aviso_geral_ou_outra_turma(self):
        self.client.force_login(self.prof_user)
        self.client.post(reverse('aviso_criar'), {'titulo': 'Geral', 'texto': 'Mensagem'})
        self.client.post(reverse('aviso_criar'), {'titulo': 'Outro', 'texto': 'Mensagem', 'turma': self.outra_turma.pk})
        self.assertFalse(Aviso.objects.exists())

    def test_aluno_e_responsavel_so_veem_turma_autorizada(self):
        Aviso.objects.create(autor=self.adm, titulo='Aviso 8B', texto='Da turma', turma=self.turma)
        Aviso.objects.create(autor=self.adm, titulo='Segredo 8C', texto='Outra turma', turma=self.outra_turma)
        for usuario in [self.aluno_user, self.resp_user]:
            self.client.force_login(usuario)
            resposta = self.client.get(reverse('comunicacao_painel'))
            self.assertContains(resposta, 'Aviso 8B')
            self.assertNotContains(resposta, 'Segredo 8C')

    def test_professor_nao_envia_mensagem_para_aluno_estranho(self):
        self.client.force_login(self.prof_user)
        self.client.post(reverse('mensagem_enviar'), {'destinatario': self.estranho_user.pk, 'assunto': 'Título', 'texto': 'Mensagem'})
        self.assertFalse(Mensagem.objects.exists())

    def test_mensagens_visiveis_apenas_aos_participantes(self):
        Mensagem.objects.create(remetente=self.prof_user, destinatario=self.aluno_user, assunto='Recado reservado', texto='Olá aluno')
        self.client.force_login(self.estranho_user)
        self.assertNotContains(self.client.get(reverse('comunicacao_painel')), 'Recado reservado')
        self.client.force_login(self.aluno_user)
        self.assertContains(self.client.get(reverse('comunicacao_painel')), 'Recado reservado')

    def test_destinatario_permitido_e_texto_escapado(self):
        self.client.force_login(self.prof_user)
        self.client.post(reverse('mensagem_enviar'), {'destinatario': self.resp_user.pk, 'assunto': 'Reunião', 'texto': '<script>alert(1)</script>'})
        self.assertEqual(Mensagem.objects.count(), 1)
        self.client.force_login(self.resp_user)
        resposta = self.client.get(reverse('comunicacao_painel'))
        self.assertNotContains(resposta, '<script>alert(1)</script>', html=False)
        self.assertContains(resposta, '&lt;script&gt;')

    def test_id_fora_do_limite_nao_gera_erro_500(self):
        self.client.force_login(self.prof_user)
        resposta = self.client.post(reverse('mensagem_enviar'), {
            'destinatario': '9999999999999999999', 'assunto': 'Teste', 'texto': 'Texto',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Mensagem.objects.exists())
