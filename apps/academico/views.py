import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from apps.usuarios.models import registrar_operacao
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Turma, Disciplina, Matricula, Aula, PeriodoLetivo, TURNO_CHOICES
from apps.usuarios.models import Aluno, Professor

# Confere se o usuário logado é administrador, usado em todas as telas e ações de gestão
def _eh_admin(usuario):
  return usuario.perfil == 'ADMIN'

# Mantém só os valores que são números, pra um id inválido no formulário não derrubar a página
def _ids_validos(valores):
  return [numero for valor in valores if (numero := _id_valido(valor)) is not None]

# Impede identificadores Unicode inválidos, negativos ou maiores que bigint.
def _id_valido(valor):
  texto = str(valor or '')
  if not texto.isascii() or not texto.isdecimal() or len(texto) > 19:
    return None
  numero = int(texto)
  return numero if 0 < numero <= 9223372036854775807 else None

# Volta pro painel do admin já na seção certa da página (ex: #turmas)
def _voltar_painel(secao):
  return redirect(reverse('academico_painel_view') + '#' + secao)

# Busca um objeto pelo id que veio na URL, sem dar erro 500 se o valor não for um número.
# Aceita um model (busca em todos) ou um queryset já filtrado (busca só dentro dele)
def _buscar_ou_none(origem, valor):
  if _id_valido(valor) is not None:
    consulta = origem.objects.all() if hasattr(origem, 'objects') else origem
    return consulta.filter(pk=_id_valido(valor)).first()
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
    'periodos_letivos': PeriodoLetivo.objects.order_by('-ano', '-semestre'),
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
  if not nome or len(nome) > 50 or len(ano) != 4 or not ano.isascii() or not ano.isdecimal() or not 2000 <= int(ano) <= 2100 or turno not in dict(TURNO_CHOICES):
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
  # Um identificador preenchido deve pertencer a um período existente.
  periodo_id = (request.POST.get('periodo_letivo') or '').strip()
  periodo = _buscar_ou_none(PeriodoLetivo, periodo_id) if periodo_id else None
  if periodo_id and periodo is None:
    messages.error(request, 'Período letivo inválido.')
    return _voltar_painel('cadastro-turma')
  turma.periodo_letivo = periodo
  regente_id = request.POST.get('professor_regente')
  regente = _buscar_ou_none(Professor, regente_id)
  if regente_id and regente is None:
    messages.error(request, 'Professor regente não encontrado.')
    return _voltar_painel('cadastro-turma')
  turma.professor_regente = regente
  # Dados e registro de auditoria precisam ser confirmados juntos.
  with transaction.atomic():
    turma.save()
    registrar_operacao(request.user, 'TURMA_SALVA', turma.pk)

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
  if not nome or len(nome) > 100:
    messages.error(request, 'Informe um nome de disciplina válido.')
    return _voltar_painel('cadastro-disciplina')

  pk = request.POST.get('pk')
  disciplina = _buscar_ou_none(Disciplina, pk) if pk else Disciplina()
  if disciplina is None:
    messages.error(request, 'Disciplina não encontrada.')
    return _voltar_painel('disciplinas')

  # Rejeita IDs malformados ou inexistentes antes de alterar nome e vínculos.
  turmas_brutas = request.POST.getlist('turmas')
  professores_brutos = request.POST.getlist('professores')
  turmas_ids = _ids_validos(turmas_brutas)
  professores_ids = _ids_validos(professores_brutos)
  turmas_validas = Turma.objects.filter(pk__in=turmas_ids)
  professores_validos = Professor.objects.filter(pk__in=professores_ids)
  if (
    len(turmas_ids) != len(turmas_brutas)
    or len(professores_ids) != len(professores_brutos)
    or turmas_validas.count() != len(set(turmas_ids))
    or professores_validos.count() != len(set(professores_ids))
  ):
    messages.error(request, 'Uma ou mais turmas ou professores são inválidos.')
    return _voltar_painel('cadastro-disciplina')

  # A disciplina, os vínculos e o log permanecem na mesma transação.
  with transaction.atomic():
    disciplina.nome = nome
    disciplina.save()
    # Seleção vazia continua válida; seleção com ID inexistente não altera vínculos.
    disciplina.turmas.set(turmas_validas)
    disciplina.professores.set(professores_validos)
    registrar_operacao(request.user, 'DISCIPLINA_SALVA', disciplina.pk)

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
  # A matrícula e o histórico da operação são gravados juntos.
  with transaction.atomic():
    matricula, criada = Matricula.objects.select_for_update().get_or_create(aluno=aluno, turma=turma)
    mudou = criada
    if criada:
      messages.success(request, 'Aluno matriculado com sucesso.')
    elif matricula.status != 'ATIVA':
      matricula.status = 'ATIVA'
      matricula.save()
      mudou = True
      messages.success(request, 'Matrícula anterior reativada.')
    else:
      messages.info(request, 'Esse aluno já está matriculado nessa turma.')
    if mudou:
      registrar_operacao(request.user, 'MATRICULA_SALVA', matricula.pk)
  return _voltar_painel('historico')

# Histórico de matrículas do aluno logado, ou do primeiro aluno vinculado ao responsável logado
@login_required(login_url='login')
def historico_matriculas_view(request):
  # Consulta apenas o aluno logado ou os alunos vinculados ao responsável.
  aluno = request.user.aluno if hasattr(request.user, 'aluno') else None
  matriculas = Matricula.objects.none()
  if aluno:
    matriculas = Matricula.objects.filter(aluno=aluno)
  elif hasattr(request.user, 'responsavel'):
    matriculas = Matricula.objects.filter(aluno__in=request.user.responsavel.alunos_vinculados.all())
  matriculas = matriculas.select_related('aluno__usuario', 'turma__professor_regente__usuario').order_by('-data_matricula', '-pk')

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
    elif turma.periodo_letivo_id and not (
      turma.periodo_letivo.data_inicio <= data <= turma.periodo_letivo.data_fim
    ):
      messages.error(request, 'Data fora do período letivo da turma.')
    else:
      # Evita registrar uma aula sem a evidência da operação.
      with transaction.atomic():
        aula = Aula.objects.create(turma=turma, disciplina=disciplina, professor=professor, data=data, conteudo=conteudo[:4000])
        registrar_operacao(request.user, 'AULA_REGISTRADA', aula.pk)
      messages.success(request, 'Aula registrada com sucesso.')
    return redirect('registrar_aula_view')

  return render(request, 'html/academico/acad_prof.html', {'turmas': turmas, 'disciplinas': disciplinas})

# Cadastra períodos letivos somente pelo administrador autorizado.
@login_required(login_url='login')
@require_POST
def periodo_criar_view(request):
  if not _eh_admin(request.user):
    return redirect('dashboard')

  # Normaliza o ano, semestre e datas recebidos manualmente pelo POST.
  ano_texto = (request.POST.get('ano') or '').strip()
  semestre_texto = (request.POST.get('semestre') or '').strip()
  inicio_texto = (request.POST.get('data_inicio') or '').strip()
  fim_texto = (request.POST.get('data_fim') or '').strip()

  # Não converte números inválidos diretamente para inteiro.
  if (len(ano_texto) != 4 or not ano_texto.isascii()
      or not ano_texto.isdecimal() or semestre_texto not in ('1', '2')):
    messages.error(request, 'Ano ou semestre inválido.')
    return _voltar_painel('cadastro-turma')
  if not 2000 <= int(ano_texto) <= 2100:
    messages.error(request, 'Informe um ano letivo válido.')
    return _voltar_painel('cadastro-turma')

  # Converte ISO, rejeitando datas impossíveis sem gerar erro 500.
  try:
    data_inicio = datetime.date.fromisoformat(inicio_texto)
    data_fim = datetime.date.fromisoformat(fim_texto)
  except ValueError:
    messages.error(request, 'Datas do período inválidas.')
    return _voltar_painel('cadastro-turma')

  # A validação do model complementa a validação manual da view.
  periodo = PeriodoLetivo(
    ano=int(ano_texto), semestre=int(semestre_texto),
    data_inicio=data_inicio, data_fim=data_fim
  )
  try:
    periodo.full_clean()
  except ValidationError:
    messages.error(request, 'Período inválido, repetido ou com datas invertidas.')
    return _voltar_painel('cadastro-turma')

  # O cadastro e a prova da operação são confirmados juntos.
  try:
    with transaction.atomic():
      periodo.save()
      registrar_operacao(request.user, 'PERIODO_CRIADO', periodo.pk)
  except IntegrityError:
    messages.error(request, 'Este período letivo já foi cadastrado.')
    return _voltar_painel('cadastro-turma')
  messages.success(request, 'Período letivo cadastrado.')
  return _voltar_painel('cadastro-turma')
