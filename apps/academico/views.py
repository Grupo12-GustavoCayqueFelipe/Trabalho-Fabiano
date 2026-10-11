import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Turma, Disciplina, Matricula, Aula, TURNO_CHOICES
from apps.usuarios.models import Aluno, Professor

# Confere se o usuário logado é administrador, usado em todas as telas e ações de gestão
def _eh_admin(usuario):
  return usuario.perfil == 'ADMIN'

# Mantém só os valores que são números, pra um id inválido no formulário não derrubar a página
def _ids_validos(valores):
  return [valor for valor in valores if str(valor).isdigit()]

# Volta pro painel do admin já na seção certa da página (ex: #turmas)
def _voltar_painel(secao):
  return redirect(reverse('academico_painel_view') + '#' + secao)

# Busca um objeto pelo id que veio na URL, sem dar erro 500 se o valor não for um número.
# Aceita um model (busca em todos) ou um queryset já filtrado (busca só dentro dele)
def _buscar_ou_none(origem, valor):
  if valor and str(valor).isdigit():
    consulta = origem.objects.all() if hasattr(origem, 'objects') else origem
    return consulta.filter(pk=valor).first()
  return None

# Painel único do admin: turmas, disciplinas, matrícula e últimas matrículas na mesma página
@login_required(login_url='login')
def academico_painel_view(request):
  if not _eh_admin(request.user):
    messages.error(request, 'Apenas administradores podem acessar essa página.')
    return redirect('dashboard')

  # Se veio ?editar_turma=<id> ou ?editar_disciplina=<id> na URL, carrega o registro pra edição
  turma_editando = _buscar_ou_none(Turma, request.GET.get('editar_turma'))
  disciplina_editando = _buscar_ou_none(Disciplina, request.GET.get('editar_disciplina'))

  # Ids já vinculados à disciplina em edição, pra marcar as opções do formulário
  disciplina_turmas_ids = []
  disciplina_professores_ids = []
  if disciplina_editando:
    disciplina_turmas_ids = list(disciplina_editando.turmas.values_list('pk', flat=True))
    disciplina_professores_ids = list(disciplina_editando.professores.values_list('pk', flat=True))

  return render(request, 'html/academico/acad_admin.html', {
    'turmas': Turma.objects.select_related('professor_regente__usuario').order_by('-ano', 'nome'),
    'disciplinas': Disciplina.objects.prefetch_related('turmas', 'professores').order_by('nome'),
    'alunos': Aluno.objects.select_related('usuario').order_by('usuario__nome'),
    'professores': Professor.objects.select_related('usuario').order_by('usuario__nome'),
    'matriculas': Matricula.objects.select_related('aluno__usuario', 'turma').order_by('-data_matricula', '-pk')[:10],
    'turma_editando': turma_editando,
    'disciplina_editando': disciplina_editando,
    'disciplina_turmas_ids': disciplina_turmas_ids,
    'disciplina_professores_ids': disciplina_professores_ids,
  })

# Cria ou atualiza uma turma, dependendo se veio um pk escondido no formulário
@login_required(login_url='login')
@require_POST
def salvar_turma_view(request):
  # Toda ação de escrita confere o perfil, não só a tela
  if not _eh_admin(request.user):
    messages.error(request, 'Apenas administradores podem gerenciar turmas.')
    return redirect('dashboard')

  nome = (request.POST.get('nome') or '').strip()
  ano = (request.POST.get('ano') or '').strip()
  turno = request.POST.get('turno')

  # Valida os dados no servidor, o HTML sozinho não garante nada
  if not nome or not ano.isdigit() or turno not in dict(TURNO_CHOICES):
    messages.error(request, 'Preencha nome, ano e turno corretamente.')
    return _voltar_painel('cadastro-turma')

  pk = request.POST.get('pk')
  turma = _buscar_ou_none(Turma, pk) if pk else Turma()
  if turma is None:
    messages.error(request, 'Turma não encontrada.')
    return _voltar_painel('turmas')

  turma.nome = nome
  turma.ano = int(ano)
  turma.turno = turno
  turma.professor_regente = _buscar_ou_none(Professor, request.POST.get('professor_regente'))
  turma.save()

  messages.success(request, 'Turma salva com sucesso.')
  return _voltar_painel('turmas')

# Cria ou atualiza uma disciplina, incluindo os vínculos com turmas e professores
@login_required(login_url='login')
@require_POST
def salvar_disciplina_view(request):
  if not _eh_admin(request.user):
    messages.error(request, 'Apenas administradores podem gerenciar disciplinas.')
    return redirect('dashboard')

  nome = (request.POST.get('nome') or '').strip()
  if not nome:
    messages.error(request, 'Informe o nome da disciplina.')
    return _voltar_painel('cadastro-disciplina')

  pk = request.POST.get('pk')
  disciplina = _buscar_ou_none(Disciplina, pk) if pk else Disciplina()
  if disciplina is None:
    messages.error(request, 'Disciplina não encontrada.')
    return _voltar_painel('disciplinas')

  disciplina.nome = nome
  disciplina.save()

  # Só aceita ids que existem de verdade, e substitui a seleção anterior pela nova
  disciplina.turmas.set(Turma.objects.filter(pk__in=_ids_validos(request.POST.getlist('turmas'))))
  disciplina.professores.set(Professor.objects.filter(pk__in=_ids_validos(request.POST.getlist('professores'))))

  messages.success(request, 'Disciplina salva com sucesso.')
  return _voltar_painel('disciplinas')

# Matricula um aluno numa turma
@login_required(login_url='login')
@require_POST
def matricular_aluno_view(request):
  if not _eh_admin(request.user):
    messages.error(request, 'Apenas administradores podem matricular alunos.')
    return redirect('dashboard')

  aluno = _buscar_ou_none(Aluno, request.POST.get('aluno'))
  turma = _buscar_ou_none(Turma, request.POST.get('turma'))
  if aluno is None or turma is None:
    messages.error(request, 'Selecione o aluno e a turma.')
    return _voltar_painel('matricula')

  # A combinação aluno + turma é única, então reaproveita a matrícula se ela já existir
  matricula, criada = Matricula.objects.get_or_create(aluno=aluno, turma=turma)
  if criada:
    messages.success(request, 'Aluno matriculado com sucesso.')
  elif matricula.status != 'ATIVA':
    matricula.status = 'ATIVA'
    matricula.save()
    messages.success(request, 'Matrícula anterior reativada.')
  else:
    messages.info(request, 'Esse aluno já está matriculado nessa turma.')
  return _voltar_painel('historico')

# Histórico de matrículas do aluno logado, ou do primeiro aluno vinculado ao responsável logado
@login_required(login_url='login')
def historico_matriculas_view(request):
  aluno = None
  if hasattr(request.user, 'aluno'):
    aluno = request.user.aluno
  elif hasattr(request.user, 'responsavel'):
    aluno = request.user.responsavel.alunos_vinculados.first()

  # Quem não é aluno nem responsável não vê matrícula de ninguém por aqui
  matriculas = []
  if aluno:
    matriculas = Matricula.objects.filter(aluno=aluno).select_related('turma__professor_regente__usuario').order_by('-data_matricula', '-pk')

  return render(request, 'html/academico/acad_aluno_resp.html', {
    'aluno': aluno,
    'matriculas': matriculas,
  })

# Professor registra o conteúdo dado numa aula
@login_required(login_url='login')
def registrar_aula_view(request):
  if not hasattr(request.user, 'professor'):
    messages.error(request, 'Apenas professores podem registrar aulas.')
    return redirect('dashboard')

  professor = request.user.professor
  # O professor só enxerga as turmas em que é regente ou em que leciona alguma disciplina
  turmas = Turma.objects.filter(Q(professor_regente=professor) | Q(disciplina__professores=professor)).distinct().order_by('nome')
  disciplinas = Disciplina.objects.filter(professores=professor).order_by('nome')

  if request.method == 'POST':
    turma = _buscar_ou_none(turmas, request.POST.get('turma'))
    disciplina = _buscar_ou_none(disciplinas, request.POST.get('disciplina'))
    conteudo = (request.POST.get('conteudo') or '').strip()

    try:
      data = datetime.date.fromisoformat(request.POST.get('data') or '')
    except ValueError:
      data = None

    if turma is None or disciplina is None or data is None or not conteudo:
      messages.error(request, 'Preencha turma, disciplina, data e conteúdo corretamente.')
    elif not disciplina.turmas.filter(pk=turma.pk).exists():
      messages.error(request, 'Essa disciplina não é oferecida nessa turma.')
    else:
      Aula.objects.create(turma=turma, disciplina=disciplina, professor=professor, data=data, conteudo=conteudo)
      messages.success(request, 'Aula registrada com sucesso.')
    return redirect('registrar_aula_view')

  return render(request, 'html/academico/acad_prof.html', {'turmas': turmas, 'disciplinas': disciplinas})