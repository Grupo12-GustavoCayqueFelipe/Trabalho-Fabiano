from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.academico.models import Aula, Matricula
from apps.usuarios.models import registrar_operacao
from .models import HistoricoFrequencia, RegistroFrequencia


# Valida IDs do formulário para não aceitar bigint inválido no banco.
def _pk_seguro(valor):
  texto = str(valor or '')
  if not texto.isascii() or not texto.isdecimal() or len(texto) > 19:
    return None
  numero = int(texto)
  return numero if 0 < numero <= 9223372036854775807 else None


# O professor só faz chamadas nas aulas de suas disciplinas e turmas atuais.
def _professor_da_aula(usuario, aula):
  return (
    hasattr(usuario, 'professor')
    and aula.professor_id == usuario.professor.pk
    and aula.disciplina.turmas.filter(pk=aula.turma_id).exists()
    and aula.disciplina.professores.filter(pk=usuario.professor.pk).exists()
  )


# Exibe frequência restrita à própria matrícula ou a familiares vinculados.
@login_required(login_url='login')
def frequencia_painel_view(request):
  usuario = request.user
  registros = RegistroFrequencia.objects.select_related('aula__disciplina', 'matricula__aluno__usuario')
  aulas = Aula.objects.none()
  matriculas = Matricula.objects.none()

  if usuario.perfil == 'ADMIN':
    aulas = Aula.objects.all().select_related('turma', 'disciplina')
    matriculas = Matricula.objects.filter(status='ATIVA')
  elif hasattr(usuario, 'professor'):
    aulas = Aula.objects.filter(professor=usuario.professor, disciplina__professores=usuario.professor, disciplina__turmas=F('turma')).distinct()
    matriculas = Matricula.objects.filter(turma__in=aulas.values('turma_id'), status='ATIVA')
    registros = registros.filter(aula__in=aulas)
  elif hasattr(usuario, 'aluno'):
    registros = registros.filter(matricula__aluno=usuario.aluno)
  elif hasattr(usuario, 'responsavel'):
    registros = registros.filter(matricula__aluno__in=usuario.responsavel.alunos_vinculados.all())
  else:
    registros = registros.none()

  # O histórico acompanha o mesmo filtro de acesso dos registros atuais.
  historico = HistoricoFrequencia.objects.filter(registro__in=registros).select_related('registro', 'usuario')
  return render(request, 'html/frequencia/painel.html', {
    'aulas': aulas.order_by('-data', '-pk'),
    'matriculas': matriculas.select_related('aluno__usuario', 'turma'),
    'registros': registros.order_by('-aula__data', '-pk'),
    'historico_frequencia': historico,
  })


# Registra presença/falta apenas de aluno matriculado na turma da aula.
@login_required(login_url='login')
@require_POST
@ratelimit(key='user', rate='20/m', block=False, method='POST')
def frequencia_salvar_view(request, aula_id):
  # Limita gravações repetidas sem impedir consultas da tela.
  if getattr(request, 'limited', False):
    messages.error(request, 'Muitas operações seguidas. Tente novamente mais tarde.')
    return redirect('frequencia_painel')
  aula = get_object_or_404(Aula.objects.select_related('turma', 'disciplina', 'professor'), pk=aula_id)
  if not _professor_da_aula(request.user, aula):
    return redirect('frequencia_painel')

  # Só aceita valores da lista fechada de estados.
  matricula_id = _pk_seguro(request.POST.get('matricula'))
  matricula = Matricula.objects.filter(pk=matricula_id, turma=aula.turma, status='ATIVA').first() if matricula_id else None
  status = (request.POST.get('status') or '').strip()
  justificativa = (request.POST.get('justificativa') or '').strip()
  if matricula is None or status not in ('P', 'F', 'J') or len(justificativa) > 200:
    messages.error(request, 'Aluno, presença ou justificativa inválida.')
    return redirect('frequencia_painel')
  if status == 'J' and not justificativa:
    messages.error(request, 'Falta justificada exige justificativa.')
    return redirect('frequencia_painel')
  if status != 'J':
    justificativa = None

  # Histórico e lançamento são confirmados juntos para não perder correções.
  with transaction.atomic():
    registro, criado = RegistroFrequencia.objects.select_for_update().get_or_create(
      aula=aula, matricula=matricula,
      defaults={'status': status, 'justificativa': justificativa}
    )
    anterior = None if criado else registro.status
    justificativa_anterior = None if criado else registro.justificativa
    registro.status = status
    registro.justificativa = justificativa
    registro.full_clean()
    registro.save()
    HistoricoFrequencia.objects.create(
      registro=registro, usuario=request.user,
      status_anterior=anterior, status_novo=status,
      justificativa_anterior=justificativa_anterior,
      justificativa_nova=justificativa
    )
    registrar_operacao(request.user, 'FREQUENCIA_SALVA', registro.pk)
  messages.success(request, 'Frequência registrada com histórico.')
  return redirect('frequencia_painel')
