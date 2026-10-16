from django.contrib.auth import logout
from django.shortcuts import redirect


# Impede que sessões antigas pulem o 2FA depois da ativação em outra sessão.
class Exigir2FAMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    usuario = request.user

    # O segundo fator precisa ter sido confirmado nesta mesma sessão.
    if usuario.is_authenticated and usuario.otp_ativado:
      if request.session.get('2fa_verificado') != usuario.pk:
        logout(request)
        return redirect('login')

    return self.get_response(request)
