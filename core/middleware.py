from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone


# Impede que sessões antigas pulem o 2FA ou continuem ativas durante bloqueio.
class Exigir2FAMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    usuario = request.user

    # Encerra imediatamente sessões de contas inativas ou com bloqueio temporário vigente.
    if usuario.is_authenticated:
      bloqueado_ate = getattr(usuario, 'bloqueado_ate', None)
      if not usuario.is_active or (bloqueado_ate and bloqueado_ate > timezone.now()):
        logout(request)
        return redirect('login')

    # O segundo fator precisa ter sido confirmado nesta mesma sessão.
    if usuario.is_authenticated and usuario.otp_ativado:
      if request.session.get('2fa_verificado') != usuario.pk:
        logout(request)
        return redirect('login')

    return self.get_response(request)
