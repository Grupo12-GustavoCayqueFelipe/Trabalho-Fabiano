import pyotp
import qrcode
import base64
import io
import datetime
import secrets
import hashlib

from core.settings import PASSWORD_RESET_TIMEOUT

from .models import Usuario, registrar_log_recuperacao_senha, TokenRecuperacaoSenha
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit, settings

from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

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

# Usuário solicita a recuperação de senha, se o email existir, gera um token e envia o email
def solicitacao_recuperacao_senha_view(request):
  # Se o usuário estiver logado, redireciona para a página principal
  if request.method == 'POST':
    # Pega o email do formulário e procura o usuário no banco de dados
    email = request.POST.get('email')
    usuario = Usuario.objects.filter(email=email).first()

    # Se o usuário existir, gera um token de recuperação de senha e envia o email
    if usuario:
      # Gera um token aleatório e seguro, guarda só o hash dele no banco
      token = secrets.token_urlsafe(32)
      token_hash = hashlib.sha256(token.encode()).hexdigest()
      
      # Define o tempo de expiração do token com base na configuração do Django
      TokenRecuperacaoSenha.objects.create(
        usuario=usuario,
        token_hash=token_hash,
        expira_em=timezone.now() + datetime.timedelta(hours=PASSWORD_RESET_TIMEOUT),
        ip=request.META.get('REMOTE_ADDR'),
      )

      # Monta o link de recuperação de senha com o token em texto puro (só existe aqui, nunca é salvo)
      link = request.build_absolute_uri(reverse('redefinir_senha_view', kwargs={'token': token}))

      # Envia o email com o link de recuperação de senha
      send_mail(
        'Recuperação de senha - EduControll',
        f'Clique no link abaixo para redefinir sua senha:\n{link}\n\nSe você não solicitou a recuperação de senha, ignore este email.',
        settings.DEFAULT_FROM_EMAIL,
        [usuario.email],
        fail_silently=False,
      )
      # Registra o log de solicitação de recuperação de senha
      registrar_log_recuperacao_senha(usuario, evento='SOLICITACAO', ip=request.META.get('REMOTE_ADDR'))

    # Mensagem genérica para não revelar se o email existe ou não no sistema
    messages.success(request, 'Se o email existir em nosso sistema, um link de recuperação de senha foi enviado.')
    return redirect('login')

  return render(request, 'html/senha/senha.html')

# Tela onde o usuário redefine a senha, acessando o link enviado por email
def redefinir_senha_view(request, token):
  # Faz o hash do token que veio na URL pra comparar com o que está salvo
  token_hash = hashlib.sha256(token.encode()).hexdigest()
  token_recuperacao = TokenRecuperacaoSenha.objects.filter(token_hash=token_hash).first()

  # Confere se o token existe, não expirou e ainda não foi usado
  token_valido = (
    token_recuperacao is not None
    and token_recuperacao.usado_em is None
    and token_recuperacao.expira_em > timezone.now()
  )
  # Se o token não for válido, registra o log de falha e mostra a mensagem de erro
  if not token_valido:
    # Se o token existir, registra o log de falha com o evento correto
    if token_recuperacao:
      evento = 'FALHA_TOKEN_EXPIRADO' if token_recuperacao.expira_em <= timezone.now() else 'FALHA_TOKEN_INVALIDO'
      registrar_log_recuperacao_senha(token_recuperacao.usuario, evento=evento, ip=request.META.get('REMOTE_ADDR'), token=token)
    # Se o token não existir, registra o log de falha com o evento de token inválido
    messages.error(request, 'Link de recuperação inválido ou expirado.')
    return redirect('login')
  
  # Se o token for válido, pega o usuário relacionado a ele
  usuario = token_recuperacao.usuario
  
  # Se o usuário enviar o formulário com a nova senha, atualiza a senha do usuário, marca o token como usado e registra o log de sucesso
  if request.method == 'POST':
    nova_senha = request.POST.get('nova_senha')
    usuario.set_password(nova_senha)
    usuario.save()

    # Marca o token como usado, pra ele não poder ser reaproveitado
    token_recuperacao.usado_em = timezone.now()
    token_recuperacao.save()
    
    # Registra o log de sucesso da redefinição de senha
    registrar_log_recuperacao_senha(usuario, evento='SUCESSO', ip=request.META.get('REMOTE_ADDR'), token=token)

    # Mensagem de sucesso e redireciona para a página de login
    messages.success(request, 'Senha redefinida com sucesso. Faça login com a nova senha.')
    return redirect('login')

  return render(request, 'html/senha/redefinir_senha.html')

@login_required(login_url='login')
def logout_view(request):
  # Desloga o usuário e redireciona para a página de login
  logout(request)
  return redirect('login')
