from django.contrib.admin import AdminSite
from django.shortcuts import redirect

# O Django Admin usa o mesmo login e exige que o código TOTP tenha sido conferido.
class EduAdminSite(AdminSite):
    def has_permission(self, request):
        # Mesmo um funcionário com senha válida não entra sem o segundo fator.
        return (
            super().has_permission(request)
            and request.user.perfil == 'ADMIN'
            and request.user.otp_ativado
            and request.session.get('2fa_verificado') == request.user.pk
        )

    def login(self, request, extra_context=None):
        # Evita que o admin ofereça um login paralelo sem TOTP.
        return redirect('login_funcionarios')
