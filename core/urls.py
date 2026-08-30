"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

# Após erro apelidei de 'usuarios_views' para não dar conflito com o nome do app
from apps.usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Rota raiz para a aplicação de login
    path('', usuarios_views.login_view, name='login'),
    # Rota para a página principal
    path('dashboard/', usuarios_views.dashboard_view, name='dashboard'),
    #rota para a página de logout
    path('logout/', usuarios_views.logout_view, name='logout'),
    # segundo passo do login, pede o código de 6 dígitos de quem tem 2FA ligado
    path('2fa/verificar/', usuarios_views.dois_fatores_verificar_view, name='2fa_verificar'),
    # tela onde o usuário liga/desliga o 2FA na própria conta
    path('2fa/configurar/', usuarios_views.dois_fatores_configurar_view, name='2fa_configurar'),
]
