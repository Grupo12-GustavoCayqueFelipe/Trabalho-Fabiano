"""Regressoes para o relatorio da disciplina. Usar sempre core.settings_test."""
import datetime
from decimal import Decimal
import hashlib
from tempfile import TemporaryDirectory
import pyotp

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.test import RequestFactory, TestCase, override_settings
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone

from apps.academico.models import AlocacaoDocente, Aula, Disciplina, Matricula, Turma
from apps.atividades.models import Atividade, Entrega
from apps.avaliacoes.models import Avaliacao, Nota
from apps.comunicacao.models import Aviso, Mensagem
from apps.frequencia.models import RegistroFrequencia
from apps.usuarios.models import (Usuario, Professor, Aluno, Responsavel,
    AlunoResponsavel, ConsentimentoUsuario, LogAcesso, LogRecuperacaoSenha, LogOperacao)
from apps.usuarios.views import _media_avaliacoes_normalizada


class CorrigirDesafioTOTPTest(TestCase):
  def setUp(self):
    cache.clear()
    self.usuario = Usuario.objects.create_user(
      email='totp-correcao@example.org', nome='TOTP Teste',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    self.usuario.otp_secret = pyotp.random_base32()
    self.usuario.otp_ativado = True
    self.usuario.save(update_fields=['otp_secret', 'otp_ativado'])

  def test_apos_cinco_erros_desafio_e_encerrado(self):
    self.client.post(reverse('login'), {
      'email': self.usuario.email, 'senha': 'SenhaFort3!2026'
    })
    for _ in range(5):
      self.client.post(reverse('2fa_verificar'), {'codigo': 'errado'})
    self.assertNotIn('pre_2fa_user_id', self.client.session)
    self.assertNotIn('pre_2fa_tentativas', self.client.session)
    self.client.post(reverse('2fa_verificar'), {
      'codigo': pyotp.TOTP(self.usuario.otp_secret).now()
    })
    self.assertNotIn('_auth_user_id', self.client.session)
    self.assertEqual(LogAcesso.objects.filter(usuario=self.usuario, evento='2FA_FALHA').count(), 5)

  def test_destino_e_limpo_quando_desafio_expira(self):
    self.client.post(reverse('login'), {
      'email': self.usuario.email, 'senha': 'SenhaFort3!2026', 'next': '/meus-dados/'
    })
    for _ in range(5):
      self.client.post(reverse('2fa_verificar'), {'codigo': 'invalido'})
    for chave in ('pre_2fa_user_id', 'pre_2fa_next', 'pre_2fa_portal', 'pre_2fa_iniciado'):
      self.assertNotIn(chave, self.client.session)


class RecuperacaoAuditoriaTest(TestCase):
  def setUp(self):
    cache.clear()

  def test_token_inexistente_gera_log_com_hash(self):
    token = 'token-que-nao-existe'
    self.client.get(reverse('redefinir_senha_view', args=[token]))
    log = LogRecuperacaoSenha.objects.get(evento='FALHA_TOKEN_INVALIDO')
    self.assertIsNone(log.usuario)
    self.assertEqual(log.token_hash, hashlib.sha256(token.encode()).hexdigest())

  def test_excesso_de_tokens_invalidos_e_limitado(self):
    for i in range(20):
      self.client.get(reverse('redefinir_senha_view', args=[f'nao-existe-{i}']))
    self.assertLessEqual(LogRecuperacaoSenha.objects.filter(evento='FALHA_TOKEN_INVALIDO').count(), 15)


class PermissaoDocenteRevogadaTest(TestCase):
  def setUp(self):
    cache.clear()
    self.usuario = Usuario.objects.create_user(
      email='docente-antigo@example.org', nome='Docente Antigo',
      password='SenhaFort3!2026', perfil='PROF'
    )
    self.professor = Professor.objects.create(usuario=self.usuario, formacao='Licenciatura')

    self.aluno_usuario = Usuario.objects.create_user(
      email='aluno-alvo-revogado@example.org', nome='Aluno Alvo',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    self.aluno = Aluno.objects.create(
      usuario=self.aluno_usuario, matricula='REV-001',
      data_nascimento=datetime.date(2010, 5, 10)
    )
    self.resp_usuario = Usuario.objects.create_user(
      email='resp-orfao@example.org', nome='Resp Orfao',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    self.resp_orfao = Responsavel.objects.create(usuario=self.resp_usuario, telefone='11900000000')
    AlunoResponsavel.objects.create(aluno=self.aluno, responsavel=self.resp_orfao, parentesco='Pai')

    self.turma = Turma.objects.create(
      nome='9A', ano=2026, turno='MANHA', professor_regente=self.professor
    )
    self.disciplina = Disciplina.objects.create(nome='História')
    self.disciplina.turmas.add(self.turma)
    self.disciplina.professores.add(self.professor)
    AlocacaoDocente.objects.create(
      professor=self.professor, disciplina=self.disciplina, turma=self.turma
    )
    self.matricula = Matricula.objects.create(
      aluno=self.aluno, turma=self.turma, status='ATIVA'
    )

    self.atividade = Atividade.objects.create(
      titulo='Pesquisa Histórica', descricao='Resumo',
      turma=self.turma, disciplina=self.disciplina,
      professor=self.professor, prazo=timezone.now() + datetime.timedelta(days=3)
    )
    self.entrega = Entrega.objects.create(
      atividade=self.atividade, aluno=self.aluno, resposta='Texto entregue'
    )
    self.avaliacao = Avaliacao.objects.create(
      nome='Prova 1', turma=self.turma, disciplina=self.disciplina,
      data_avaliacao=datetime.date(2026, 4, 15),
      nota_maxima=Decimal('10.00'), peso=Decimal('1.00')
    )
    self.aula = Aula.objects.create(
      turma=self.turma, disciplina=self.disciplina,
      professor=self.professor, data=datetime.date(2026, 4, 10),
      conteudo='Revolução Industrial'
    )

    # Troca o perfil para ALUNO manteniendo o registro órfão de Professor para testar todas as barreiras.
    self.usuario.perfil = 'ALUNO'
    self.usuario.save(update_fields=['perfil'])
    self.client.force_login(self.usuario)

  def test_perfil_aluno_nao_publica_atividade(self):
    resposta = self.client.post(reverse('atividade_criar'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_perfil_aluno_nao_cria_avaliacao(self):
    resposta = self.client.post(reverse('avaliacao_criar'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_perfil_aluno_nao_registra_aula(self):
    resposta = self.client.post(reverse('registrar_aula_view'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_perfil_aluno_nao_envia_aviso(self):
    resposta = self.client.post(reverse('aviso_criar'))
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))

  def test_ex_professor_nao_corrige_entrega_anterior(self):
    resposta = self.client.post(
      reverse('entrega_corrigir', args=[self.atividade.pk, self.entrega.pk]),
      {'nota': '9.00', 'comentario': 'Tentativa após revogação'}
    )
    self.assertEqual(resposta.status_code, 302)
    self.entrega.refresh_from_db()
    self.assertIsNone(self.entrega.nota)

  def test_ex_professor_nao_salva_nota(self):
    resposta = self.client.post(
      reverse('nota_salvar', args=[self.avaliacao.pk]),
      {'matricula': self.matricula.pk, 'valor': '8.50'}
    )
    self.assertEqual(resposta.status_code, 302)
    self.assertFalse(Nota.objects.filter(avaliacao=self.avaliacao).exists())

  def test_ex_professor_nao_salva_frequencia(self):
    resposta = self.client.post(
      reverse('frequencia_salvar', args=[self.aula.pk]),
      {'matricula': self.matricula.pk, 'status': 'P'}
    )
    self.assertEqual(resposta.status_code, 302)
    self.assertFalse(RegistroFrequencia.objects.filter(aula=self.aula).exists())

  def test_ex_professor_nao_envia_mensagem(self):
    resposta = self.client.post(
      reverse('mensagem_enviar'),
      {'destinatario': self.aluno_usuario.pk, 'assunto': 'Oi', 'texto': 'Mensagem'}
    )
    self.assertEqual(resposta.status_code, 302)
    self.assertEqual(resposta.url, reverse('dashboard'))
    self.assertFalse(Mensagem.objects.exists())

  def test_ex_professor_nao_baixa_arquivo_de_entrega(self):
    with TemporaryDirectory() as pasta:
      with override_settings(MEDIA_ROOT=pasta):
        self.entrega.arquivo = SimpleUploadedFile(
          'entrega.pdf', b'%PDF-1.7\nconteudo', content_type='application/pdf'
        )
        self.entrega.save()
        resposta = self.client.get(reverse('entrega_arquivo', args=[self.entrega.pk]))
        self.assertEqual(resposta.status_code, 404)

  def test_vinculo_orfao_nao_permite_atualizar_telefone_nem_assinar_termo_de_responsavel(self):
    # Mesmo com objeto Responsavel órfão no banco, perfil ALUNO não pode atualizar telefone nem representar aluno.
    self.client.force_login(self.resp_usuario)
    self.client.post(reverse('atualizar_telefone_view'), {'telefone': '11988887777'})
    self.resp_orfao.refresh_from_db()
    self.assertEqual(self.resp_orfao.telefone, '11900000000')

    self.client.post(reverse('termos_view'), {
      'acao': 'conceder',
      'tipo': 'USO_IMAGEM',
      'aluno_id': str(self.aluno.pk),
    })
    self.assertFalse(
      ConsentimentoUsuario.objects.filter(
        usuario=self.resp_usuario, aluno_representado=self.aluno
      ).exists()
    )

    resposta_meus_dados = self.client.get(reverse('meus_dados_view'))
    self.assertIsNone(resposta_meus_dados.context['telefone'])
    resposta_termos = self.client.get(reverse('termos_view'))
    self.assertEqual(list(resposta_termos.context['alunos_vinculados']), [])

  def test_admin_save_model_remove_vinculos_docentes_ao_trocar_perfil(self):
    from django.contrib import admin
    gestor = Usuario.objects.create_superuser(
      email='gestor-rbac@example.org', nome='Gestor RBAC',
      password='SenhaFort3!2026'
    )
    requisicao = RequestFactory().post('/admin/usuarios/usuario/')
    requisicao.user = gestor
    admin.site._registry[Usuario].save_model(requisicao, self.usuario, form=None, change=True)
    self.turma.refresh_from_db()
    self.assertIsNone(self.turma.professor_regente)
    self.assertFalse(self.disciplina.professores.filter(pk=self.professor.pk).exists())
    self.assertFalse(AlocacaoDocente.objects.filter(professor=self.professor).exists())


class IsolamentoDocentePorTurmaTest(TestCase):
  def setUp(self):
    cache.clear()
    self.user_prof1 = Usuario.objects.create_user(
      email='prof1-mat@example.org', nome='Prof 1 Mat',
      password='SenhaFort3!2026', perfil='PROF'
    )
    self.prof1 = Professor.objects.create(usuario=self.user_prof1, formacao='Matemática')

    self.user_prof2 = Usuario.objects.create_user(
      email='prof2-mat@example.org', nome='Prof 2 Mat',
      password='SenhaFort3!2026', perfil='PROF'
    )
    self.prof2 = Professor.objects.create(usuario=self.user_prof2, formacao='Matemática')

    self.turma_7a = Turma.objects.create(
      nome='7A', ano=2026, turno='MANHA', professor_regente=self.prof1
    )
    self.turma_7b = Turma.objects.create(
      nome='7B', ano=2026, turno='TARDE', professor_regente=self.prof2
    )

    self.matematica = Disciplina.objects.create(nome='Matemática')
    self.matematica.turmas.add(self.turma_7a, self.turma_7b)
    self.matematica.professores.add(self.prof1, self.prof2)
    AlocacaoDocente.objects.create(
      professor=self.prof1, disciplina=self.matematica, turma=self.turma_7a
    )
    AlocacaoDocente.objects.create(
      professor=self.prof2, disciplina=self.matematica, turma=self.turma_7b
    )

    self.user_aluno_7b = Usuario.objects.create_user(
      email='aluno-7b@example.org', nome='Aluno 7B',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    self.aluno_7b = Aluno.objects.create(
      usuario=self.user_aluno_7b, matricula='MAT-7B',
      data_nascimento=datetime.date(2012, 3, 15)
    )
    self.matricula_7b = Matricula.objects.create(
      aluno=self.aluno_7b, turma=self.turma_7b, status='ATIVA'
    )

    self.atividade_7b = Atividade.objects.create(
      titulo='Lista 7B', descricao='Exercícios',
      turma=self.turma_7b, disciplina=self.matematica,
      professor=self.prof2, prazo=timezone.now() + datetime.timedelta(days=2)
    )
    self.entrega_7b = Entrega.objects.create(
      atividade=self.atividade_7b, aluno=self.aluno_7b, resposta='Resolução 7B'
    )
    self.avaliacao_7b = Avaliacao.objects.create(
      nome='Avaliação 7B', turma=self.turma_7b, disciplina=self.matematica,
      data_avaliacao=datetime.date(2026, 5, 10),
      nota_maxima=Decimal('10.00'), peso=Decimal('1.00')
    )
    self.aula_7b = Aula.objects.create(
      turma=self.turma_7b, disciplina=self.matematica,
      professor=self.prof2, data=datetime.date(2026, 5, 8),
      conteudo='Equações na 7B'
    )
    self.client.force_login(self.user_prof1)

  def test_prof1_nao_registra_aula_na_turma_7b(self):
    self.client.post(reverse('registrar_aula_view'), {
      'turma': self.turma_7b.pk,
      'disciplina': self.matematica.pk,
      'data': '2026-05-12',
      'conteudo': 'Tentativa indevida na 7B',
    })
    self.assertFalse(
      Aula.objects.filter(turma=self.turma_7b, professor=self.prof1).exists()
    )

  def test_prof1_nao_cria_nem_corrige_atividade_na_turma_7b(self):
    self.client.post(reverse('atividade_criar'), {
      'titulo': 'Atividade Indevida 7B',
      'descricao': 'Descrição',
      'turma': self.turma_7b.pk,
      'disciplina': self.matematica.pk,
      'prazo': (timezone.now() + datetime.timedelta(days=3)).isoformat(),
    })
    self.assertFalse(
      Atividade.objects.filter(titulo='Atividade Indevida 7B').exists()
    )

    self.client.post(
      reverse('entrega_corrigir', args=[self.atividade_7b.pk, self.entrega_7b.pk]),
      {'nota': '10.00', 'comentario': 'Correção cruzada'}
    )
    self.entrega_7b.refresh_from_db()
    self.assertIsNone(self.entrega_7b.nota)

  def test_prof1_nao_cria_avaliacao_nem_lanca_nota_na_turma_7b(self):
    self.client.post(reverse('avaliacao_criar'), {
      'nome': 'Prova Cruzada 7B',
      'turma': self.turma_7b.pk,
      'disciplina': self.matematica.pk,
      'data_avaliacao': '2026-05-20',
      'nota_maxima': '10.00',
      'peso': '1.00',
    })
    self.assertFalse(
      Avaliacao.objects.filter(nome='Prova Cruzada 7B').exists()
    )

    self.client.post(
      reverse('nota_salvar', args=[self.avaliacao_7b.pk]),
      {'matricula': self.matricula_7b.pk, 'valor': '9.50'}
    )
    self.assertFalse(Nota.objects.filter(avaliacao=self.avaliacao_7b).exists())

  def test_prof1_nao_lanca_frequencia_na_turma_7b(self):
    self.client.post(
      reverse('frequencia_salvar', args=[self.aula_7b.pk]),
      {'matricula': self.matricula_7b.pk, 'status': 'F'}
    )
    self.assertFalse(
      RegistroFrequencia.objects.filter(aula=self.aula_7b).exists()
    )

  def test_prof1_nao_envia_aviso_nem_mensagem_para_turma_7b(self):
    self.client.post(reverse('aviso_criar'), {
      'titulo': 'Aviso para 7B',
      'texto': 'Conteúdo',
      'turma': self.turma_7b.pk,
    })
    self.assertFalse(Aviso.objects.filter(turma=self.turma_7b).exists())

    self.client.post(reverse('mensagem_enviar'), {
      'destinatario': self.user_aluno_7b.pk,
      'assunto': 'Mensagem 7B',
      'texto': 'Conteúdo',
    })
    self.assertFalse(
      Mensagem.objects.filter(destinatario=self.user_aluno_7b).exists()
    )

  def test_regente_sem_disciplina_na_turma_nao_cria_atividade_em_disciplina_alheia(self):
    # D.3: ser professor_regente da 7A não autoriza publicar atividade em disciplina que não leciona na 7A.
    geografia = Disciplina.objects.create(nome='Geografia')
    geografia.turmas.add(self.turma_7a)
    geografia.professores.add(self.prof2)
    AlocacaoDocente.objects.create(
      professor=self.prof2, disciplina=geografia, turma=self.turma_7a
    )
    self.client.post(reverse('atividade_criar'), {
      'titulo': 'Atividade Geografia Indevida',
      'descricao': 'Descrição',
      'turma': self.turma_7a.pk,
      'disciplina': geografia.pk,
      'prazo': (timezone.now() + datetime.timedelta(days=3)).isoformat(),
    })
    self.assertFalse(
      Atividade.objects.filter(titulo='Atividade Geografia Indevida').exists()
    )


class MediaPonderadaTest(TestCase):
  def test_media_respeita_peso_e_nota_maxima(self):
    class NotasFicticias:
      def values_list(self, *campos):
        return [(Decimal('5'), Decimal('10'), Decimal('1')),
                (Decimal('2'), Decimal('2'), Decimal('3'))]
    self.assertEqual(_media_avaliacoes_normalizada(NotasFicticias()), Decimal('8.75'))

  def test_media_sem_notas_retorna_none(self):
    class SemNotas:
      def values_list(self, *campos):
        return []
    self.assertIsNone(_media_avaliacoes_normalizada(SemNotas()))


class ExportacaoPorRepresentacaoTest(TestCase):
  def test_aluno_consulta_consentimentos_assinados_pelo_responsavel(self):
    aluno_usuario = Usuario.objects.create_user(
      email='aluno-export@example.org', nome='Aluno Export',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    aluno = Aluno.objects.create(usuario=aluno_usuario, matricula='EXP2026-1')
    resp_usuario = Usuario.objects.create_user(
      email='resp-export@example.org', nome='Responsavel Export',
      password='SenhaFort3!2026', perfil='RESP'
    )
    resp = Responsavel.objects.create(usuario=resp_usuario)
    AlunoResponsavel.objects.create(aluno=aluno, responsavel=resp, parentesco='Mae')
    ConsentimentoUsuario.objects.create(usuario=resp_usuario,
      aluno_representado=aluno, tipo='USO_IMAGEM', aceito=True)
    self.client.force_login(aluno_usuario)
    resposta = self.client.get(reverse('exportar_dados_view'))
    self.assertEqual(resposta.status_code, 200)
    self.assertEqual(len(resposta.json()['consentimentos_por_responsaveis']), 1)

  def test_responsavel_exporta_so_aluno_vinculado(self):
    resp_usuario = Usuario.objects.create_user(
      email='resp-export2@example.org', nome='Responsavel Export',
      password='SenhaFort3!2026', perfil='RESP'
    )
    resp = Responsavel.objects.create(usuario=resp_usuario)
    for i in range(2):
      u = Usuario.objects.create_user(
        email=f'aluno-exp-{i}@example.org', nome='Aluno',
        password='SenhaFort3!2026', perfil='ALUNO'
      )
      aluno = Aluno.objects.create(usuario=u, matricula=f'EXP2026-{i+2}')
      if i == 0:
        AlunoResponsavel.objects.create(aluno=aluno, responsavel=resp)
    self.client.force_login(resp_usuario)
    resposta = self.client.get(reverse('exportar_dados_view'))
    self.assertEqual(resposta.status_code, 200)
    dados = resposta.json()['dados_alunos_representados']
    self.assertEqual(len(dados), 1)
    self.assertEqual(dados[0]['matricula'], 'EXP2026-2')


class AuditoriaAdminSenhaTest(TestCase):
  def test_troca_de_senha_do_admin_registra_log_sem_gravar_conteudo(self):
    from django.contrib import admin
    gestor = Usuario.objects.create_superuser(
      email='admin-gestor@example.org', nome='Gestor Teste',
      password='SenhaFort3!2026'
    )
    alvo = Usuario.objects.create_user(
      email='alvo-admin-senha@example.org', nome='Alvo',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    requisicao = RequestFactory().post('/admin/usuarios/usuario/1/password/')
    requisicao.user = gestor
    # Isola a auditoria: a validacao real do formulario continua no UserAdmin.
    with patch.object(UserAdmin, 'user_change_password', return_value=HttpResponseRedirect('/admin/')):
      admin.site._registry[Usuario].user_change_password(requisicao, str(alvo.pk))
    self.assertTrue(LogOperacao.objects.filter(
      usuario=gestor, evento='ADMIN_SENHA_USUARIO', objeto_id=alvo.pk
    ).exists())

  def test_abertura_do_formulario_nao_registra_troca_de_senha(self):
    from django.contrib import admin
    gestor = Usuario.objects.create_superuser(
      email='admin-gestor2@example.org', nome='Gestor Teste',
      password='SenhaFort3!2026'
    )
    alvo = Usuario.objects.create_user(
      email='alvo-admin-senha2@example.org', nome='Alvo',
      password='SenhaFort3!2026', perfil='ALUNO'
    )
    requisicao = RequestFactory().get('/admin/usuarios/usuario/1/password/')
    requisicao.user = gestor
    with patch.object(UserAdmin, 'user_change_password', return_value=HttpResponseRedirect('/admin/')):
      admin.site._registry[Usuario].user_change_password(requisicao, str(alvo.pk))
    self.assertFalse(LogOperacao.objects.filter(evento='ADMIN_SENHA_USUARIO').exists())


class ComprovacaoControlesProducaoTest(TestCase):
  def test_hash_pbkdf2_usa_salt_diferente(self):
    primeiro = make_password('SenhaFort3!2026', hasher='pbkdf2_sha256')
    segundo = make_password('SenhaFort3!2026', hasher='pbkdf2_sha256')
    self.assertTrue(primeiro.startswith('pbkdf2_sha256$'))
    self.assertNotEqual(primeiro, segundo)

  @override_settings(SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=3600)
  def test_redirecionamento_https_e_hsts(self):
    resposta_http = self.client.get('/login/')
    self.assertEqual(resposta_http.status_code, 301)
    self.assertTrue(resposta_http['Location'].startswith('https://'))
    resposta_https = self.client.get('/login/', secure=True)
    self.assertIn('Strict-Transport-Security', resposta_https)

  def test_tempo_configurado_para_sessao(self):
    from django.conf import settings
    self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
    self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
    self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

  def test_conversao_idempotente_de_otp_secret_legado_sem_dupla_cifragem(self):
    from django.db import connection
    from encrypted_model_fields.fields import decrypt_str
    from scripts.verificar_criptografia_legada import verificar

    usuario_legado = Usuario.objects.create_user(
      email='totp-legado@example.org', nome='TOTP Legado',
      password='SenhaFort3!2026', perfil='ADMIN'
    )
    segredo_puro = 'JBSWY3DPEHPK3PXP'
    with connection.cursor() as cursor:
      cursor.execute('UPDATE usuarios SET otp_secret = %s WHERE id = %s', [segredo_puro, usuario_legado.pk])

    # Primeira execução detecta 1 pendente e cifra; segunda execução confirma 0 pendentes sem recifrar.
    self.assertEqual(verificar(corrigir=False), 1)
    self.assertEqual(verificar(corrigir=True), 0)
    with connection.cursor() as cursor:
      cursor.execute('SELECT otp_secret FROM usuarios WHERE id = %s', [usuario_legado.pk])
      cifrado_primeira_vez = str(cursor.fetchone()[0])

    self.assertTrue(cifrado_primeira_vez.startswith('gAAAA'))
    self.assertEqual(decrypt_str(cifrado_primeira_vez), segredo_puro)

    # Execução repetida preserva o mesmo token Fernet e a leitura na ORM.
    self.assertEqual(verificar(corrigir=True), 0)
    with connection.cursor() as cursor:
      cursor.execute('SELECT otp_secret FROM usuarios WHERE id = %s', [usuario_legado.pk])
      cifrado_segunda_vez = str(cursor.fetchone()[0])
    self.assertEqual(cifrado_primeira_vez, cifrado_segunda_vez)
    usuario_legado.refresh_from_db()
    self.assertEqual(usuario_legado.otp_secret, segredo_puro)
