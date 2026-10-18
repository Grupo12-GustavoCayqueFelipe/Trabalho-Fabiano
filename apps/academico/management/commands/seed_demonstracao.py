"""Cria dados sintéticos de demonstração apenas após autorização explícita.

Nunca é executado em deploy ou migrações. Não use com dados reais.
"""
import os
import secrets
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone


class Command(BaseCommand):
  help = 'Dados EDU-DEMO para validar os quatro portais sem usar dados pessoais.'

  def add_arguments(self, parser):
    parser.add_argument('--confirmar', action='store_true', help='Executa a criação de dados sintéticos')
    parser.add_argument('--permitir-postgres', action='store_true', help='Autoriza explicitamente um banco compartilhado')

  def handle(self, *args, **options):
    if not options['confirmar']:
      self.stdout.write('MODO PRÉVIA: nenhuma gravação. Será criado um professor, um aluno, um responsável, turma, disciplina, aulas, frequência, notas, atividades, avisos e mensagens sintéticos. Para executar use --confirmar.')
      return
    if connection.vendor != 'sqlite':
      if not options['permitir_postgres'] or os.getenv('EDU_DEMO_APROVADO') != 'SIM':
        raise CommandError('Banco não SQLite. Exige --permitir-postgres e variável EDU_DEMO_APROVADO=SIM. Confirme backup, tabelas e ambiente antes.')
    from apps.usuarios.models import Usuario, Aluno, Professor, Responsavel, AlunoResponsavel
    from apps.academico.models import Turma, Disciplina, Matricula, Aula
    from apps.frequencia.models import RegistroFrequencia
    from apps.avaliacoes.models import Avaliacao, Nota
    from apps.atividades.models import Atividade, Entrega
    from apps.comunicacao.models import Aviso, Mensagem

    senhas = {}

    def usuario_demo(email, nome, perfil):
      atual = Usuario.objects.filter(email=email).first()
      if atual:
        if atual.perfil != perfil or atual.nome != nome:
          raise CommandError('E-mail DEMO existente não corresponde à identidade sintética esperada: ' + email)
        return atual
      senha = secrets.token_urlsafe(14)
      atual = Usuario.objects.create_user(email=email, nome=nome, perfil=perfil, password=senha)
      senhas[email] = senha
      return atual

    hoje = timezone.localdate()
    prazo = timezone.now() + timedelta(days=8)
    with transaction.atomic():
      prof_u = usuario_demo('professor.edu-demo@example.invalid', 'Professor EDU-DEMO', 'PROF')
      aluno_u = usuario_demo('aluno.edu-demo@example.invalid', 'Aluno EDU-DEMO', 'ALUNO')
      resp_u = usuario_demo('responsavel.edu-demo@example.invalid', 'Responsável EDU-DEMO', 'RESP')
      professor, _ = Professor.objects.get_or_create(usuario=prof_u, defaults={'formacao': 'Licenciatura (demo)'})
      aluno, _ = Aluno.objects.get_or_create(usuario=aluno_u, defaults={'matricula': 'EDU-DEMO-2026-001'})
      responsavel, _ = Responsavel.objects.get_or_create(usuario=resp_u)
      AlunoResponsavel.objects.get_or_create(aluno=aluno, responsavel=responsavel, defaults={'parentesco': 'Vínculo sintético'})
      turma, _ = Turma.objects.get_or_create(nome='EDU-DEMO - 1º Ano A', ano=hoje.year, turno='MANHA', defaults={'professor_regente': professor})
      disciplina, _ = Disciplina.objects.get_or_create(nome='EDU-DEMO - Matemática')
      disciplina.turmas.add(turma)
      disciplina.professores.add(professor)
      matricula, _ = Matricula.objects.get_or_create(aluno=aluno, turma=turma, defaults={'status': 'ATIVA'})
      if matricula.status != 'ATIVA':
        raise CommandError('Matrícula DEMO existe mas não está ativa; não altera registros existentes.')
      aula, _ = Aula.objects.get_or_create(turma=turma, disciplina=disciplina, professor=professor, data=hoje, defaults={'conteudo': 'Introdução aos números (conteúdo sintético).'})
      RegistroFrequencia.objects.get_or_create(aula=aula, matricula=matricula, defaults={'status': 'P'})
      avaliacao, _ = Avaliacao.objects.get_or_create(turma=turma, disciplina=disciplina, nome='EDU-DEMO - Avaliação diagnóstica', defaults={'data_avaliacao': hoje, 'nota_maxima': Decimal('10.00')})
      Nota.objects.get_or_create(avaliacao=avaliacao, matricula=matricula, defaults={'valor': Decimal('8.50')})
      Atividade.objects.get_or_create(turma=turma, disciplina=disciplina, professor=professor, titulo='EDU-DEMO - Atividade pendente', defaults={'descricao': 'Resolva três exercícios fictícios de matemática.', 'prazo': prazo, 'valor_nota': Decimal('10.00')})
      entregue, _ = Atividade.objects.get_or_create(turma=turma, disciplina=disciplina, professor=professor, titulo='EDU-DEMO - Atividade entregue', defaults={'descricao': 'Escreva um resumo dos exercícios.', 'prazo': prazo, 'valor_nota': Decimal('10.00')})
      Entrega.objects.get_or_create(atividade=entregue, aluno=aluno, defaults={'resposta': 'Resposta de demonstração sem dados pessoais.'})
      Aviso.objects.get_or_create(titulo='EDU-DEMO - Reunião escolar', autor=prof_u, turma=turma, defaults={'texto': 'Aviso sintético de reunião para teste dos portais.'})
      Mensagem.objects.get_or_create(remetente=prof_u, destinatario=resp_u, assunto='EDU-DEMO - Mensagem de teste', defaults={'texto': 'Mensagem sintética para conferir os vínculos e a caixa postal.'})
    self.stdout.write(self.style.SUCCESS('Dados sintéticos EDU-DEMO preparados. Nenhuma informação real foi usada.'))
    if senhas:
      self.stdout.write('CREDENCIAIS NOVAS (copie agora; não serão exibidas novamente):')
      for email, senha in senhas.items():
        self.stdout.write(f'{email} | {senha}')
    else:
      self.stdout.write('Contas DEMO já existiam; nenhuma senha foi redefinida.')
