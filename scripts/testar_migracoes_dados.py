"""Simula atualização de dados legados para campos Fernet em SQLite descartável.

Uso na pasta principal: python scripts/testar_migracoes_dados.py
Não se conecta ao Supabase e nunca usa DATABASE_URL de produção.
"""
import os
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings_test'
os.environ.setdefault('SECRET_KEY', 'chave-somente-para-ensaio-local')
os.environ.setdefault('DEBUG', 'True')

import django
django.setup()
from django.conf import settings
from django.db import connections
from django.db.migrations.executor import MigrationExecutor


with tempfile.TemporaryDirectory(prefix='educontroll-migracoes-') as pasta:
  banco = str(Path(pasta) / 'ensaio.sqlite3')
  settings.DATABASES['default']['NAME'] = banco
  connection = connections['default']
  connection.settings_dict['NAME'] = banco

  # Até este ponto, observação, justificativa e assunto são texto simples.
  anteriores = [
    ('usuarios', '0015_proteger_consentimentos'),
    ('academico', '0007_validar_periodos'),
    ('atividades', '0003_merge_integracao'),
    ('avaliacoes', '0001_initial'),
    ('frequencia', '0001_initial'),
    ('comunicacao', '0002_alter_aviso_options_aviso_fixado'),
  ]
  executor = MigrationExecutor(connection)
  executor.migrate(anteriores)
  apps = executor.loader.project_state(anteriores).apps

  Usuario = apps.get_model('usuarios', 'Usuario')
  Aluno = apps.get_model('usuarios', 'Aluno')
  Professor = apps.get_model('usuarios', 'Professor')
  Turma = apps.get_model('academico', 'Turma')
  Disciplina = apps.get_model('academico', 'Disciplina')
  Matricula = apps.get_model('academico', 'Matricula')
  Aula = apps.get_model('academico', 'Aula')
  Avaliacao = apps.get_model('avaliacoes', 'Avaliacao')
  Nota = apps.get_model('avaliacoes', 'Nota')
  Registro = apps.get_model('frequencia', 'RegistroFrequencia')
  Mensagem = apps.get_model('comunicacao', 'Mensagem')

  admin = Usuario.objects.create(email='admin-ensaio@example.test', nome='Adm', perfil='ADMIN')
  pessoa = Usuario.objects.create(email='aluno-ensaio@example.test', nome='Aluno', perfil='ALUNO')
  professor = Professor.objects.create(usuario=admin, formacao='Ensino')
  aluno = Aluno.objects.create(usuario=pessoa, matricula='A-00001')
  turma = Turma.objects.create(nome='1A', turno='MANHA', ano=2026, professor_regente=professor)
  disciplina = Disciplina.objects.create(nome='Matemática')
  matricula = Matricula.objects.create(aluno=aluno, turma=turma)
  aula = Aula.objects.create(turma=turma, disciplina=disciplina, professor=professor, data='2026-04-01')
  avaliacao = Avaliacao.objects.create(turma=turma, disciplina=disciplina, nome='Exame', data_avaliacao='2026-04-01')
  nota = Nota.objects.create(avaliacao=avaliacao, matricula=matricula, valor='8.00', observacao='Observação pessoal antiga')
  registro = Registro.objects.create(aula=aula, matricula=matricula, status='J', justificativa='Justificativa familiar antiga')
  mensagem = Mensagem.objects.create(remetente=admin, destinatario=pessoa, assunto='Assunto pessoal antigo', texto='Texto antigo')

  executor = MigrationExecutor(connection)
  executor.migrate(executor.loader.graph.leaf_nodes())

  from apps.avaliacoes.models import Nota as NotaAtual
  from apps.frequencia.models import RegistroFrequencia as RegistroAtual
  from apps.comunicacao.models import Mensagem as MensagemAtual

  assert NotaAtual.objects.get(pk=nota.pk).observacao == 'Observação pessoal antiga'
  assert RegistroAtual.objects.get(pk=registro.pk).justificativa == 'Justificativa familiar antiga'
  assert MensagemAtual.objects.get(pk=mensagem.pk).assunto == 'Assunto pessoal antigo'

  with connection.cursor() as cursor:
    cursor.execute('SELECT observacao FROM notas WHERE id = %s', [nota.pk])
    assert 'Observação pessoal antiga' not in str(cursor.fetchone()[0])
    cursor.execute('SELECT justificativa FROM registros_frequencia WHERE id = %s', [registro.pk])
    assert 'Justificativa familiar antiga' not in str(cursor.fetchone()[0])
    cursor.execute('SELECT assunto FROM mensagens_escola WHERE id = %s', [mensagem.pk])
    assert 'Assunto pessoal antigo' not in str(cursor.fetchone()[0])

  print('APROVADO: dados antigos preservados na ORM e criptografados no SQLite.')
  connection.close()
