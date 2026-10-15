from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.academico.models import Matricula, Turma
from apps.usuarios.models import Usuario, registrar_operacao
from .models import Aviso, Mensagem


# Confere se o id informado cabe no bigint do PostgreSQL.
def _pk_seguro(valor):
  texto = str(valor or '')
  if not texto.isascii() or not texto.isdecimal() or len(texto) > 19:
    return None
  numero = int(texto)
  return numero if 0 < numero <= 9223372036854775807 else None


# Busca as turmas onde o professor leciona ou é regente.
def _turmas_professor(professor):
  return Turma.objects.filter(Q(professor_regente=professor) | Q(disciplina__professores=professor)).distinct()


# Retorna apenas os destinatários permitidos para este usuário.
def _destinatarios_autorizados(usuario):
  destinatarios = Usuario.objects.filter(is_active=True, perfil__in=['ALUNO', 'RESP'])
  if usuario.perfil == 'ADMIN':
    return destinatarios
  if not hasattr(usuario, 'professor'):
    return destinatarios.none()

  # Inclui alunos ativos das turmas e responsáveis associados a esses alunos.
  alunos_ids = Matricula.objects.filter(turma__in=_turmas_professor(usuario.professor), status='ATIVA').values_list('aluno_id', flat=True)
  return destinatarios.filter(Q(aluno__id__in=alunos_ids) | Q(responsavel__alunos_vinculados__id__in=alunos_ids)).distinct()


# Mural e caixa postal: visibilidade limitada por matrícula e vínculo familiar.
@login_required(login_url='login')
def comunicacao_painel_view(request):
  usuario = request.user
  avisos = Aviso.objects.filter(ativo=True).select_related('turma', 'autor')
  turmas = Turma.objects.none()

  if usuario.perfil == 'ADMIN':
    turmas = Turma.objects.all().order_by('nome')
  elif hasattr(usuario, 'professor'):
    turmas = _turmas_professor(usuario.professor)
    avisos = avisos.filter(Q(turma__isnull=True) | Q(turma__in=turmas))
  elif hasattr(usuario, 'aluno'):
    ids = Matricula.objects.filter(aluno=usuario.aluno, status='ATIVA').values_list('turma_id', flat=True)
    avisos = avisos.filter(Q(turma__isnull=True) | Q(turma_id__in=ids))
  elif hasattr(usuario, 'responsavel'):
    ids = Matricula.objects.filter(aluno__in=usuario.responsavel.alunos_vinculados.all(), status='ATIVA').values_list('turma_id', flat=True)
    avisos = avisos.filter(Q(turma__isnull=True) | Q(turma_id__in=ids))
  else:
    avisos = avisos.none()

  # Cada usuário só enxerga suas próprias mensagens, nunca a caixa postal alheia.
  mensagens_recebidas = Mensagem.objects.filter(destinatario=usuario).select_related('remetente')
  mensagens_enviadas = Mensagem.objects.filter(remetente=usuario).select_related('destinatario')
  return render(request, 'html/comunicacao/painel.html', {
    'avisos': avisos.distinct(),
    'turmas': turmas,
    'mensagens_recebidas': mensagens_recebidas,
    'mensagens_enviadas': mensagens_enviadas,
    'destinatarios': _destinatarios_autorizados(usuario),
  })


# Publica aviso somente na turma autorizada; aviso geral é exclusivo do admin.
@login_required(login_url='login')
@require_POST
def aviso_criar_view(request):
  usuario = request.user
  if usuario.perfil != 'ADMIN' and not hasattr(usuario, 'professor'):
    return redirect('dashboard')

  titulo = (request.POST.get('titulo') or '').strip()
  texto = (request.POST.get('texto') or '').strip()
  turma_id = (request.POST.get('turma') or '').strip()
  if not titulo or len(titulo) > 120 or not texto or len(texto) > 3000:
    messages.error(request, 'Informe título e texto válidos.')
    return redirect('comunicacao_painel')

  turma = None
  if turma_id:
    if _pk_seguro(turma_id) is None:
      return redirect('comunicacao_painel')
    turmas = Turma.objects.all() if usuario.perfil == 'ADMIN' else _turmas_professor(usuario.professor)
    turma = turmas.filter(pk=_pk_seguro(turma_id)).first()
    if turma is None:
      return redirect('comunicacao_painel')
  elif usuario.perfil != 'ADMIN':
    messages.error(request, 'Professor deve selecionar uma turma.')
    return redirect('comunicacao_painel')

  with transaction.atomic():
    aviso = Aviso.objects.create(titulo=titulo, texto=texto, autor=usuario, turma=turma)
    registrar_operacao(usuario, 'AVISO_PUBLICADO', aviso.pk)
  messages.success(request, 'Aviso publicado com sucesso.')
  return redirect('comunicacao_painel')


# Envia mensagem interna sem expor destinatários de outras turmas.
@login_required(login_url='login')
@require_POST
def mensagem_enviar_view(request):
  usuario = request.user
  if usuario.perfil != 'ADMIN' and not hasattr(usuario, 'professor'):
    return redirect('dashboard')

  destinatario_id = (request.POST.get('destinatario') or '').strip()
  assunto = (request.POST.get('assunto') or '').strip()
  texto = (request.POST.get('texto') or '').strip()
  if _pk_seguro(destinatario_id) is None or not assunto or len(assunto) > 120 or not texto or len(texto) > 3000:
    messages.error(request, 'Preencha destinatário, assunto e mensagem corretamente.')
    return redirect('comunicacao_painel')

  destinatario = _destinatarios_autorizados(usuario).filter(pk=_pk_seguro(destinatario_id)).first()
  if destinatario is None:
    messages.error(request, 'Destinatário não autorizado.')
    return redirect('comunicacao_painel')

  with transaction.atomic():
    mensagem = Mensagem.objects.create(remetente=usuario, destinatario=destinatario, assunto=assunto, texto=texto)
    registrar_operacao(usuario, 'MENSAGEM_ENVIADA', mensagem.pk)
  messages.success(request, 'Mensagem enviada.')
  return redirect('comunicacao_painel')
