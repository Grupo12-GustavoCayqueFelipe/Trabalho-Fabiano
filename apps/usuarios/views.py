from django.core.checks import messages
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.
def login_view(request):
  # Se o usuario estiver logado, redireciona para a página principal
  if request.user.is_authenticated:
    return redirect('dashboard') 
  
  # Para o botão entrar
  if request.method == 'POST':
    # Pegando os dados do formulário
    email = request.POST.get('email')
    senha = request.POST.get('senha')

    # Pega a senha do usuário faz o hash e compara com a senha do banco de dados
    usuario = authenticate (request, email=email, password=senha)
    
    if usuario is not None:
      # Se o hash da senha for igual, o usuário é autenticado e redirecionado para a página principal
      login(request, usuario)
      return redirect('dashboard')
    else:
      # Mensagem de erro genérico
      messages.error(request, 'E-mail ou senha inválidos.')

  # Se acessou o site sem estar logado, renderiza a página de login
  return render(request, 'usuarios/index.html')
  
def dashboard_view(request):
  # Bloqueia o acesso a página principal se o usuário não estiver logado
  if not request.user.is_authenticated:
    return redirect('login')
  
  # Template de dashboard para cada perfil de usuário
  templates_por_perfil = {
    'ALUNO': 'html/alunos/aluno.html',
    'RESP': 'html/responsaveis/responsaveis.html',
  }
  # Se o usuário estiver logado, renderiza a página principal
  template = templates_por_perfil.get(request.user.perfil, 'usuarios/dashboard.html')
  return render(request, template) 

@login_required(login_url='login')
def logout_view(request):
  # Desloga o usuário e redireciona para a página de login
  logout(request)
  return redirect('login')