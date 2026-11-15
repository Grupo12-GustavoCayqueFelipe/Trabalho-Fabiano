from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.academico.models import (Disciplina, Matricula, Turma, professor_leciona_na_turma, turmas_lecionadas_pelo_professor)
from apps.frequencia.models import RegistroFrequencia
from apps.usuarios.models import registrar_operacao
from apps.usuarios.views import _media_avaliacoes_normalizada
from .models import Avaliacao, HistoricoNota, Nota


# Só aceita IDs inteiros positivos que caibam no bigint do PostgreSQL.
def _pk_seguro(valor):
  texto = str(valor or '')
  if not texto.isascii() or not texto.isdecimal() or len(texto) > 19:
    return None
  numero = int(texto)
  return numero if 0 < numero <= 9223372036854775807 else None


# Converte notas e pesos sem aceitar números infinitos ou decimais longos.
def _decimal_seguro(texto, maximo, permite_zero=False):
  try:
    valor = Decimal(str(texto or '').strip())
  except (InvalidOperation, ValueError):
    return None
  if not valor.is_finite() or (valor < 0 if permite_zero else valor <= 0) or valor > maximo or valor.as_tuple().exponent < -2:
    return None
  return valor


# Professor precisa estar vinculado à combinação específica de disciplina e turma da avaliação.
def _professor_autorizado(usuario, avaliacao):
  return (
    usuario.perfil == 'PROF'
    and hasattr(usuario, 'professor')
    and professor_leciona_na_turma(usuario.professor, avaliacao.disciplina, avaliacao.turma)
  )


# Consolida média ponderada normalizada e situação por matrícula e disciplina no boletim.
def _montar_resumo_disciplinas(matriculas_consulta, notas_visiveis, professor=None):
  resumo = []
  for matricula in matriculas_consulta.select_related('aluno__usuario', 'turma').order_by('aluno__usuario__nome', 'pk'):
    disciplinas_turma = Disciplina.objects.filter(
      Q(turmas=matricula.turma) | Q(avaliacoes__notas__matricula=matricula)
    ).distinct().order_by('nome')
    for disc in disciplinas_turma:
      if professor is not None and not professor_leciona_na_turma(professor, disc, matricula.turma):
        continue
      notas_disc = notas_visiveis.filter(matricula=matricula, avaliacao__disciplina=disc)
      media = _media_avaliacoes_normalizada(notas_disc)
      freq_qs = RegistroFrequencia.objects.filter(matricula=matricula, aula__disciplina=disc)
      totais_freq = freq_qs.aggregate(
        total=Count('pk'),
        presentes=Count('pk', filter=Q(status__in=['P', 'J'])),
      )
      total_aulas = totais_freq['total'] or 0
      percentual_freq = round(100 * (totais_freq['presentes'] or 0) / total_aulas) if total_aulas else None
      if media is None:
        situacao = 'Em curso'
      elif percentual_freq is not None and percentual_freq < 75:
        situacao = 'Reprovado por frequência'
      elif media >= Decimal('6.00'):
        situacao = 'Aprovado'
      elif media >= Decimal('4.00'):
        situacao = 'Recuperação'
      else:
        situacao = 'Reprovado por nota'
      resumo.append({
        'matricula': matricula,
        'aluno': matricula.aluno,
        'disciplina': disc,
        'media': media,
        'percentual_frequencia': percentual_freq,
        'situacao': situacao,
      })
  return resumo


# Lista apenas notas que pertencem ao próprio aluno ou ao responsável vinculado.
@login_required(login_url='login')
def avaliacoes_painel_view(request):
  usuario = request.user
  avaliacoes = Avaliacao.objects.select_related('turma', 'disciplina')
  notas = Nota.objects.select_related('avaliacao', 'matricula__aluno__usuario')
  turmas = Turma.objects.none()
  disciplinas = Disciplina.objects.none()
  matriculas_boletim = Matricula.objects.none()
  professor_filtro = None

  # Administradores consultam os dados, mas lançamento exige o professor vinculado.
  if usuario.perfil == 'ADMIN':
    turmas = Turma.objects.all().order_by('nome')
    disciplinas = Disciplina.objects.all().order_by('nome')
    matriculas_boletim = Matricula.objects.filter(status='ATIVA', turma__in=turmas)
  elif usuario.perfil == 'PROF' and hasattr(usuario, 'professor'):
    professor_filtro = usuario.professor
    disciplinas = Disciplina.objects.filter(professores=usuario.professor).distinct()
    turmas = turmas_lecionadas_pelo_professor(usuario.professor)
    avaliacoes_candidatas = avaliacoes.filter(disciplina__professores=usuario.professor, disciplina__turmas=F('turma'), turma__in=turmas)
    ids_autorizados = [
      av.pk for av in avaliacoes_candidatas
      if professor_leciona_na_turma(usuario.professor, av.disciplina, av.turma)
    ]
    avaliacoes = avaliacoes.filter(pk__in=ids_autorizados)
    notas = notas.filter(avaliacao__in=avaliacoes)
    matriculas_boletim = Matricula.objects.filter(status='ATIVA', turma__in=turmas)
  elif usuario.perfil == 'ALUNO' and hasattr(usuario, 'aluno'):
    matriculas = Matricula.objects.filter(aluno=usuario.aluno)
    avaliacoes = avaliacoes.filter(turma__in=matriculas.values('turma_id'))
    notas = notas.filter(matricula__in=matriculas)
    matriculas_boletim = matriculas
  elif usuario.perfil == 'RESP' and hasattr(usuario, 'responsavel'):
    matriculas = Matricula.objects.filter(aluno__in=usuario.responsavel.alunos_vinculados.all())
    avaliacoes = avaliacoes.filter(turma__in=matriculas.values('turma_id'))
    notas = notas.filter(matricula__in=matriculas)
    matriculas_boletim = matriculas
  else:
    avaliacoes = avaliacoes.none()
    notas = notas.none()

  # Recupera revisões apenas das notas já autorizadas para este perfil.
  notas_distintas = notas.distinct().order_by('-pk')
  historico_notas = HistoricoNota.objects.filter(nota__in=notas_distintas).select_related(
    'nota__avaliacao', 'nota__matricula__aluno__usuario', 'usuario'
  ).order_by('-alterado_em', '-pk')
  # Mostra os lançamentos e a lista de alunos somente aos profissionais autorizados.
  matriculas = Matricula.objects.filter(status='ATIVA', turma__in=turmas).select_related('aluno__usuario', 'turma')
  resumo_disciplinas = _montar_resumo_disciplinas(matriculas_boletim, notas_distintas, professor=professor_filtro)
  # Pagina notas e histórico de revisões para evitar decifrar todo o histórico Fernet em memória.
  pagina = request.GET.get('page') or request.GET.get('pagina')
  return render(request, 'html/avaliacoes/painel.html', {
    'avaliacoes': avaliacoes.distinct().order_by('-data_avaliacao', '-pk'),
    'notas': Paginator(notas_distintas, 50).get_page(pagina),
    'turmas': turmas,
    'disciplinas': disciplinas,
    'matriculas': matriculas,
    'historico_notas': Paginator(historico_notas, 50).get_page(pagina),
    'resumo_disciplinas': resumo_disciplinas,
  })


# Cria avaliações apenas para turmas e disciplinas do professor autenticado.
@login_required(login_url='login')
@require_POST
@ratelimit(key='user', rate='20/m', block=False, method='POST')
def avaliacao_criar_view(request):
  # Limita gravações repetidas sem impedir consultas da tela.
  if getattr(request, 'limited', False):
    messages.error(request, 'Muitas operações seguidas. Tente novamente mais tarde.')
    return redirect('avaliacoes_painel')
  if request.user.perfil != 'PROF' or not hasattr(request.user, 'professor'):
    return redirect('dashboard')

  # Normaliza cada entrada do POST sem utilizar ModelForm.
  nome = (request.POST.get('nome') or '').strip()
  turma_id = _pk_seguro(request.POST.get('turma'))
  disciplina_id = _pk_seguro(request.POST.get('disciplina'))
  data_texto = (request.POST.get('data_avaliacao') or '').strip()
  nota_maxima = _decimal_seguro(request.POST.get('nota_maxima'), Decimal('10'))
  peso = _decimal_seguro(request.POST.get('peso'), Decimal('99.99'))

  # Datas ISO inválidas são rejeitadas, sem quebrar a view.
  try:
    from datetime import date
    data_avaliacao = date.fromisoformat(data_texto)
  except ValueError:
    data_avaliacao = None

  # Identificadores precisam pertencer à combinação específica de disciplina e turma do docente.
  disciplina = Disciplina.objects.filter(pk=disciplina_id, professores=request.user.professor).first() if disciplina_id else None
  turma = Turma.objects.filter(pk=turma_id, disciplina=disciplina).first() if turma_id and disciplina else None
  if (
    not nome
    or len(nome) > 200
    or turma is None
    or not professor_leciona_na_turma(request.user.professor, disciplina, turma)
    or data_avaliacao is None
    or nota_maxima is None
    or peso is None
  ):
    messages.error(request, 'Dados inválidos ou turma sem autorização.')
    return redirect('avaliacoes_painel')

  # Garante que validação, persistência e log ocorram na mesma transação sem expor erro 500.
  try:
    with transaction.atomic():
      avaliacao = Avaliacao(nome=nome, turma=turma, disciplina=disciplina, data_avaliacao=data_avaliacao, nota_maxima=nota_maxima, peso=peso)
      avaliacao.full_clean()
      avaliacao.save()
      registrar_operacao(request.user, 'AVALIACAO_CRIADA', avaliacao.pk)
  except ValidationError:
    messages.error(request, 'Dados inválidos ou turma sem autorização.')
    return redirect('avaliacoes_painel')
  messages.success(request, 'Avaliação cadastrada.')
  return redirect('avaliacoes_painel')


# Registra ou corrige notas com bloqueio de linha e trilha histórica.
@login_required(login_url='login')
@require_POST
@ratelimit(key='user', rate='20/m', block=False, method='POST')
def nota_salvar_view(request, avaliacao_id):
  # Limita gravações repetidas sem impedir consultas da tela.
  if getattr(request, 'limited', False):
    messages.error(request, 'Muitas operações seguidas. Tente novamente mais tarde.')
    return redirect('avaliacoes_painel')
  avaliacao = get_object_or_404(Avaliacao.objects.select_related('turma', 'disciplina'), pk=avaliacao_id)
  if not _professor_autorizado(request.user, avaliacao):
    return redirect('avaliacoes_painel')

  # Só permite matrícula ativa da turma vinculada à avaliação.
  matricula_id = _pk_seguro(request.POST.get('matricula'))
  matricula = Matricula.objects.filter(pk=matricula_id, turma=avaliacao.turma, status='ATIVA').first() if matricula_id else None
  valor = _decimal_seguro(request.POST.get('valor'), avaliacao.nota_maxima, permite_zero=True)
  observacao = (request.POST.get('observacao') or '').strip()
  if matricula is None or valor is None or len(observacao) > 2000:
    messages.error(request, 'Matrícula, nota ou observação inválida.')
    return redirect('avaliacoes_painel')

  # select_for_update evita duas correções simultâneas perderem o valor anterior.
  try:
    with transaction.atomic():
      nota, criada = Nota.objects.select_for_update().get_or_create(
        avaliacao=avaliacao, matricula=matricula,
        defaults={'valor': valor, 'observacao': observacao}
      )
      anterior = None if criada else nota.valor
      observacao_anterior = None if criada else nota.observacao
      nota.valor = valor
      nota.observacao = observacao
      nota.full_clean()
      nota.save()
      HistoricoNota.objects.create(
        nota=nota, usuario=request.user, valor_anterior=anterior,
        valor_novo=valor, observacao_anterior=observacao_anterior,
        observacao_nova=observacao
      )
      registrar_operacao(request.user, 'NOTA_SALVA', nota.pk)
  except ValidationError:
    messages.error(request, 'Matrícula, nota ou observação inválida.')
    return redirect('avaliacoes_painel')
  messages.success(request, 'Nota registrada com histórico.')
  return redirect('avaliacoes_painel')
