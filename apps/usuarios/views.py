import pyotp
import qrcode
import base64
import io
import datetime

from .models import Usuario
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit

# Create your views here.
TENTATIVAS_MAX = 5
TEMPO_BLOQUEIO_MINUTOS = 15
# Função de Rate Limit para limitar o número de tentativas de login
@ratelimit(key='ip', rate='5/m', block=False)

# Função de login, verifica se o usuário está logado, se não estiver, pega os dados do formulário e autentica
def login_view(request):
  if getattr(request, 'limited', False):
    messages.error(request, 'Muitas tentativas de login. Tente novamente mais tarde.')
    return render(request, 'usuarios/index.html')
  
  # Se o usuario estiver logado, redireciona para a página principal
  if request.user.is_authenticated:
    return redirect('dashboard') 
  
  # Para o botão entrar
  if request.method == 'POST':
    # Pegando os dados do formulário
    email = request.POST.get('email')
    senha = request.POST.get('senha')

    # Confere se já existe um usuario com esse email para poder checar o bloqueio antes de logar
    usuario_existente = Usuario.objects.filter(email=email).first()
    
    # Se o usuário estiver bloqueado e confere o tempo de bloqueio já passou
    if usuario_existente and usuario_existente.bloqueado_ate:
      if timezone.now() < usuario_existente.bloqueado_ate:
        messages.error(request, 'Conta temporariamente por excesso de tentativas. Tente novamente mais tarde.')
        return render(request, 'usuarios/index.html')
      else:
        # Depois que passou o tempo libera e zera o contador
        usuario_existente.bloqueado_ate = None
        usuario_existente.tentativas_login = 0
        usuario_existente.save()
        
    # Pega a senha do usuário faz o hash e compara com a senha do banco de dados
    usuario = authenticate (request, email=email, password=senha)
    
    if usuario is not None:
      # Zera o contador de tentativas com o login certo
      usuario.tentativas_login = 0
      usuario.bloqueado_ate = None
      usuario.save()
      
      # Se o usuário tiver o 2FA ligado, não loga e guarda o id na sessão
      if usuario.otp_ativado:
        request.session['pre_2fa_user_id'] = usuario.pk
        return redirect('2fa_verificar')
      # Se o hash da senha for igual, o usuário é autenticado e redirecionado para a página principal
      login(request, usuario)
      return redirect('dashboard')
    else:
      if usuario_existente:
        usuario_existente.tentativas_login += 1
        usuario_existente.ultimo_login_falha = timezone.now()
        
        # Bateu o limite de tentativas bloqueando a conta pelo tempo definido
        if usuario_existente.tentativas_login >= TENTATIVAS_MAX:
          usuario_existente.bloqueado_ate = timezone.now() + datetime.timedelta(minutes=TEMPO_BLOQUEIO_MINUTOS)
          
        usuario_existente.save()
      # Mensagem de erro genérico
      messages.error(request, 'Email ou senha inválidos.')

  # Se acessou o site sem estar logado, renderiza a página de login
  return render(request, 'usuarios/index.html')
# Segunda etapa do login pra quem tem 2FA ligado, pede o código de 6 dígitos
def dois_fatores_verificar_view(request):
  # Confere se veio de um login válido, se não veio manda pro login normal
  usuario_id = request.session.get('pre_2fa_user_id')
  if not usuario_id:
    return redirect('login')
  
  # Pega o usuário pelo id guardado na sessão
  usuario = Usuario.objects.get(pk=usuario_id)
  if request.method == 'POST':
    codigo = request.POST.get('codigo')
    totp = pyotp.TOTP(usuario.otp_secret)

    # Confere se o código bate com o que o app autenticador devia estar gerando
    if totp.verify(codigo):
      del request.session['pre_2fa_user_id']
      login(request, usuario)
      return redirect('dashboard')
    else:
      messages.error(request, 'Código de verificação inválido ou expirado.')

  return render(request, 'usuarios/2fa_verificar.html', {'email': usuario.email})

# Tela onde o usuário logado ativa ou desativa o 2FA na própria conta
@login_required(login_url='login')
def dois_fatores_configurar_view(request):
  usuario = request.user

  if request.method == 'POST':
    # Botão de desativar
    if request.POST.get('acao') == 'desativar':
      usuario.otp_ativado = False
      usuario.otp_secret = None
      usuario.save()
      return redirect('2fa_configurar')

    # Confirma o código pra ativar de vez
    codigo = request.POST.get('codigo')
    totp = pyotp.TOTP(usuario.otp_secret)
    if totp.verify(codigo):
      usuario.otp_ativado = True
      usuario.save()
      messages.success(request, 'Autenticação de dois fatores ativada com sucesso.')
      return redirect('2fa_configurar')
    else:
      messages.error(request, 'Código inválido, tenta escanear o QR Code de novo.')

  # Gera a chave secreta na primeira vez que o usuário acessa essa tela
  if not usuario.otp_secret:
    usuario.otp_secret = pyotp.random_base32()
    usuario.save()

  qr_base64 = None
  if not usuario.otp_ativado:
    # Monta a URI padrão que qualquer app autenticador entende e transforma num QR Code
    totp = pyotp.TOTP(usuario.otp_secret)
    uri = totp.provisioning_uri(name=usuario.email, issuer_name='EduControll')

    imagem = qrcode.make(uri)
    buffer = io.BytesIO()
    imagem.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

  return render(request, 'usuarios/2fa_configurar.html', {
    'otp_ativado': usuario.otp_ativado,
    'otp_secret': usuario.otp_secret,
    'qr_base64': qr_base64,
  })

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