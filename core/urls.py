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
    # tela onde o usuário liga e desliga o 2FA na própria conta
    path('2fa/configurar/', usuarios_views.dois_fatores_configurar_view, name='2fa_configurar'),
    # rota para a página de solicitação de recuperação de senha, que envia o email com o token
    path('senha/recuperar/', usuarios_views.solicitacao_recuperacao_senha_view, name='solicitacao_recuperacao_senha_view'),
    # rota para a página de redefinição de senha, que recebe o token como parâmetro
    path('senha/redefinir/<token>/', usuarios_views.redefinir_senha_view, name='redefinir_senha_view'),
    # rota para a página de dados do usuário, onde ele pode ver e editar seus dados pessoais
    path('meus-dados/', usuarios_views.meus_dados_view, name='meus_dados_view'),
    # rota para a página de atualização de telefone do usuário, onde ele pode alterar seu número de telefone
    path('meus-dados/atualizar/', usuarios_views.atualizar_telefone_view, name='atualizar_telefone_view'),
    # rota para a página de termos de uso, onde o usuário pode ler e aceitar os termos de uso da aplicação
    path('meus-dados/termos/', usuarios_views.termos_view, name='termos_view'),
    # rota para a página de exportação de dados do usuário, onde ele pode baixar um arquivo com seus dados pessoais
    path('meus-dados/exportar/', usuarios_views.exportar_dados_view, name='exportar_dados_view'),
    # rota para a página de exclusão de dados do usuário, onde ele pode excluir sua conta e todos os seus dados pessoais
    path('meus-dados/excluir/', usuarios_views.excluir_dados_view, name='excluir_dados_view'),
]
