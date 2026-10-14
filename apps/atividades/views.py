from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from apps.academico.models import Turma, Disciplina, Matricula
from apps.usuarios.models import registrar_operacao
from .models import Atividade, Entrega


# Confere se o id informado cabe no bigint do PostgreSQL.
def _pk_seguro(valor):
  texto = str(valor or '')
  if not texto.isascii() or not texto.isdecimal() or len(texto) > 19:
    return None
  numero = int(texto)
  return numero if 0 < numero <= 9223372036854775807 else None


# Consulta só as turmas que o professor tem autorização para lecionar.
def _turmas_do_professor(professor):
  return Turma.objects.filter(Q(professor_regente=professor) | Q(disciplina__professores=professor)).distinct()


# Decide se o aluno tem matrícula ativa na turma da atividade.
def _aluno_pode_entregar(usuario, atividade):
  return (
    hasattr(usuario, 'aluno')
    and Matricula.objects.filter(aluno=usuario.aluno, turma=atividade.turma, status='ATIVA').exists()
  )


# Um professor só pode corrigir trabalhos das próprias atividades.
def _professor_da_atividade(usuario, atividade):
  return hasattr(usuario, 'professor') and atividade.professor_id == usuario.professor.pk


# Lista atividades com RBAC: cada perfil só consulta registros relacionados.
@login_required(login_url='login')
def atividades_lista_view(request):
  usuario = request.user
  atividades = Atividade.objects.select_related('turma', 'disciplina', 'professor__usuario')
  turmas = Turma.objects.none()
  disciplinas = Disciplina.objects.none()

  if usuario.perfil == 'ADMIN':
    pass
  elif hasattr(usuario, 'professor'):
    atividades = atividades.filter(professor=usuario.professor)
    turmas = _turmas_do_professor(usuario.professor)
    disciplinas = Disciplina.objects.filter(professores=usuario.professor).distinct()
  elif hasattr(usuario, 'aluno'):
    turmas_aluno = Matricula.objects.filter(aluno=usuario.aluno, status='ATIVA').values_list('turma_id', flat=True)
    atividades = atividades.filter(turma_id__in=turmas_aluno, ativa=True)
  elif hasattr(usuario, 'responsavel'):
    turmas_filhos = Matricula.objects.filter(aluno__in=usuario.responsavel.alunos_vinculados.all(), status='ATIVA').values_list('turma_id', flat=True)
    atividades = atividades.filter(turma_id__in=turmas_filhos, ativa=True)
  else:
    atividades = atividades.none()

  return render(request, 'html/atividades/lista.html', {
    'atividades': atividades.distinct(),
    'turmas': turmas,
    'disciplinas': disciplinas,
  })


# Cria atividade sem ModelForm, seguindo o padrão manual do projeto.
@login_required(login_url='login')
@require_POST
def atividade_criar_view(request):
  if not hasattr(request.user, 'professor'):
    return redirect('dashboard')

  professor = request.user.professor
  titulo = (request.POST.get('titulo') or '').strip()
  descricao = (request.POST.get('descricao') or '').strip()
  turma_id = request.POST.get('turma')
  disciplina_id = request.POST.get('disciplina')
  prazo = parse_datetime(request.POST.get('prazo') or '')

  # Recusa dados malformados, comprimento excessivo e prazo no passado.
  if not titulo or len(titulo) > 120 or not descricao or len(descricao) > 4000 or prazo is None:
    messages.error(request, 'Preencha o título, a descrição e o prazo corretamente.')
    return redirect('atividades_lista')
  if timezone.is_naive(prazo):
    prazo = timezone.make_aware(prazo, timezone.get_current_timezone())
  if prazo <= timezone.now():
    messages.error(request, 'O prazo precisa estar no futuro.')
    return redirect('atividades_lista')

  # Validar dentro do queryset impede publicar para turma de outro professor.
  turma = _turmas_do_professor(professor).filter(pk=_pk_seguro(turma_id)).first() if _pk_seguro(turma_id) else None
  disciplina = Disciplina.objects.filter(pk=_pk_seguro(disciplina_id), professores=professor, turmas=turma).first() if turma and _pk_seguro(disciplina_id) else None
  if turma is None or disciplina is None:
    messages.error(request, 'Turma ou disciplina não autorizada para este professor.')
    return redirect('atividades_lista')

  with transaction.atomic():
    atividade = Atividade.objects.create(titulo=titulo, descricao=descricao, turma=turma, disciplina=disciplina, professor=professor, prazo=prazo)
    registrar_operacao(request.user, 'ATIVIDADE_CRIADA', atividade.pk)
  messages.success(request, 'Atividade publicada.')
  return redirect('atividade_detalhe', atividade_id=atividade.pk)


# Mostra detalhes somente ao professor autor, à administração e aos alunos da turma.
@login_required(login_url='login')
def atividade_detalhe_view(request, atividade_id):
  atividade = get_object_or_404(Atividade.objects.select_related('turma', 'disciplina', 'professor__usuario'), pk=atividade_id)
  entregas = Entrega.objects.none()
  minha_entrega = None

  if request.user.perfil == 'ADMIN' or _professor_da_atividade(request.user, atividade):
    entregas = atividade.entregas.select_related('aluno__usuario').order_by('aluno__usuario__nome')
  elif atividade.ativa and _aluno_pode_entregar(request.user, atividade):
    minha_entrega = Entrega.objects.filter(atividade=atividade, aluno=request.user.aluno).first()
  elif atividade.ativa and hasattr(request.user, 'responsavel'):
    alunos = request.user.responsavel.alunos_vinculados.filter(matriculas__turma=atividade.turma, matriculas__status='ATIVA').distinct()
    if not alunos.exists():
      return redirect('atividades_lista')
    entregas = atividade.entregas.filter(aluno__in=alunos).select_related('aluno__usuario')
  else:
    # Sem autorização, não revela título, conteúdo nem respostas da atividade.
    return redirect('atividades_lista')

  return render(request, 'html/atividades/detalhe.html', {
    'atividade': atividade,
    'entregas': entregas,
    'minha_entrega': minha_entrega,
    'pode_entregar': _aluno_pode_entregar(request.user, atividade) and atividade.ativa and timezone.now() <= atividade.prazo,
  })


# Entrega ou atualiza a resposta do próprio aluno antes da data-limite.
@login_required(login_url='login')
@require_POST
def entrega_salvar_view(request, atividade_id):
  atividade = get_object_or_404(Atividade, pk=atividade_id, ativa=True)
  if not _aluno_pode_entregar(request.user, atividade) or timezone.now() > atividade.prazo:
    return redirect('atividades_lista')

  resposta = (request.POST.get('resposta') or '').strip()
  if not resposta or len(resposta) > 5000:
    messages.error(request, 'A resposta deve conter de 1 a 5000 caracteres.')
    return redirect('atividade_detalhe', atividade_id=atividade.pk)

  with transaction.atomic():
    # Não é permitido sobrescrever entrega já corrigida.
    entrega, criada = Entrega.objects.select_for_update().get_or_create(atividade=atividade, aluno=request.user.aluno, defaults={'resposta': resposta})
    if not criada:
      if entrega.corrigida_em is not None:
        messages.error(request, 'Essa entrega já foi corrigida.')
        return redirect('atividade_detalhe', atividade_id=atividade.pk)
      entrega.resposta = resposta
      entrega.save(update_fields=['resposta', 'atualizada_em'])
    registrar_operacao(request.user, 'ENTREGA_SALVA', entrega.pk)
  messages.success(request, 'Resposta enviada com sucesso.')
  return redirect('atividade_detalhe', atividade_id=atividade.pk)


# Professor autor faz correção manual com nota opcional de zero a dez.
@login_required(login_url='login')
@require_POST
def entrega_corrigir_view(request, atividade_id, entrega_id):
  atividade = get_object_or_404(Atividade, pk=atividade_id)
  if not _professor_da_atividade(request.user, atividade):
    return redirect('atividades_lista')
  entrega = get_object_or_404(Entrega, pk=entrega_id, atividade=atividade)
  comentario = (request.POST.get('comentario') or '').strip()
  nota_texto = (request.POST.get('nota') or '').strip()

  try:
    nota = Decimal(nota_texto) if nota_texto else None
  except (InvalidOperation, ValueError):
    nota = None
    nota_texto = 'invalida'
  if len(comentario) > 2000 or (nota_texto and (nota is None or not nota.is_finite() or nota < 0 or nota > 10 or nota.as_tuple().exponent < -2)):
    messages.error(request, 'Informe nota entre 0 e 10 (até duas casas) e comentário válido.')
    return redirect('atividade_detalhe', atividade_id=atividade.pk)
  if not comentario and nota is None:
    messages.error(request, 'Informe uma nota ou comentário para corrigir.')
    return redirect('atividade_detalhe', atividade_id=atividade.pk)

  with transaction.atomic():
    entrega.nota = nota
    entrega.comentario_professor = comentario
    entrega.corrigida_em = timezone.now()
    entrega.save(update_fields=['nota', 'comentario_professor', 'corrigida_em'])
    registrar_operacao(request.user, 'ENTREGA_CORRIGIDA', entrega.pk)
  messages.success(request, 'Correção registrada.')
  return redirect('atividade_detalhe', atividade_id=atividade.pk)
