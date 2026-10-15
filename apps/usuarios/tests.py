import datetime
import hashlib
import re

import pyotp
from django.core import mail
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Usuario,
    LogAcesso,
    LogRecuperacaoSenha,
    TokenRecuperacaoSenha,
    ConsentimentoUsuario,
)

SENHA = "Senha@12345"


class BaseUsuarioTest(TestCase):
    def setUp(self):
        # O rate limit guarda contadores no cache, então limpa antes de cada teste
        cache.clear()
        self.usuario = Usuario.objects.create_user(
            email="user@t.com", password=SENHA, nome="Usuario Teste"
        )

    def eventos(self, usuario=None):
        logs = LogAcesso.objects.filter(usuario=usuario or self.usuario).order_by("pk")
        return [log.evento for log in logs]

    def logado(self):
        return "_auth_user_id" in self.client.session


class LoginTest(BaseUsuarioTest):
    # Login certo entra e registra LOGIN_SUCESSO uma única vez
    def test_login_correto(self):
        resposta = self.client.post(
            reverse("login"), {"email": "user@t.com", "senha": SENHA}
        )
        self.assertRedirects(
            resposta, reverse("dashboard"), fetch_redirect_response=False
        )
        self.assertTrue(self.logado())
        self.assertEqual(self.eventos(), ["LOGIN_SUCESSO"])

    def test_senha_errada_registra_falha(self):
        self.client.post(reverse("login"), {"email": "user@t.com", "senha": "errada"})
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.tentativas_login, 1)
        self.assertEqual(self.eventos(), ["LOGIN_FALHA"])
        self.assertFalse(self.logado())

    # Na quinta tentativa errada a conta bloqueia, e a senha certa deixa de funcionar
    def test_bloqueio_apos_cinco_tentativas(self):
        for _ in range(5):
            self.client.post(
                reverse("login"), {"email": "user@t.com", "senha": "errada"}
            )
        self.usuario.refresh_from_db()
        self.assertIsNotNone(self.usuario.bloqueado_ate)
        self.assertEqual(self.eventos()[-1], "CONTA_BLOQUEADA")

        cache.clear()
        self.client.post(reverse("login"), {"email": "user@t.com", "senha": SENHA})
        self.assertFalse(self.logado())

    # Só POST conta no limite por IP, então abrir a página várias vezes não trava o login
    def test_get_nao_consome_o_limite_do_login(self):
        for _ in range(8):
            self.client.get(reverse("login"))
        resposta = self.client.post(
            reverse("login"), {"email": "user@t.com", "senha": SENHA}
        )
        self.assertRedirects(
            resposta, reverse("dashboard"), fetch_redirect_response=False
        )


class DoisFatoresLoginTest(BaseUsuarioTest):
    def setUp(self):
        super().setUp()
        self.usuario.otp_secret = pyotp.random_base32()
        self.usuario.otp_ativado = True
        self.usuario.save()

    def senha_correta(self):
        return self.client.post(
            reverse("login"), {"email": "user@t.com", "senha": SENHA}
        )

    # Só a senha não autentica, e ainda não pode existir log de login com sucesso
    def test_senha_sozinha_nao_autentica(self):
        resposta = self.senha_correta()
        self.assertRedirects(
            resposta, reverse("2fa_verificar"), fetch_redirect_response=False
        )
        self.assertFalse(self.logado())
        self.assertEqual(self.eventos(), [])

    def test_codigo_correto_conclui_o_login(self):
        self.senha_correta()
        self.client.post(
            reverse("2fa_verificar"),
            {"codigo": pyotp.TOTP(self.usuario.otp_secret).now()},
        )
        self.assertTrue(self.logado())
        self.assertEqual(self.eventos(), ["2FA_SUCESSO", "LOGIN_SUCESSO"])

    def test_codigo_errado_nao_autentica(self):
        self.senha_correta()
        self.client.post(reverse("2fa_verificar"), {"codigo": "000000"})
        self.assertFalse(self.logado())
        self.assertEqual(self.eventos(), ["2FA_FALHA"])

    # Depois de 5 códigos errados, nem o código certo passa (força bruta contida)
    def test_rate_limit_do_2fa(self):
        self.senha_correta()
        for _ in range(5):
            self.client.post(reverse("2fa_verificar"), {"codigo": "000000"})
        self.client.post(
            reverse("2fa_verificar"),
            {"codigo": pyotp.TOTP(self.usuario.otp_secret).now()},
        )
        self.assertFalse(self.logado())


class DoisFatoresConfigurarTest(BaseUsuarioTest):
    def setUp(self):
        super().setUp()
        self.usuario.otp_secret = pyotp.random_base32()
        self.usuario.otp_ativado = True
        self.usuario.save()
        self.client.force_login(self.usuario)

    def desativar(self, **dados):
        return self.client.post(
            reverse("2fa_configurar"), {"acao": "desativar", **dados}
        )

    def test_desativar_sem_senha_nao_funciona(self):
        self.desativar()
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.otp_ativado)

    def test_desativar_so_com_senha_nao_funciona(self):
        self.desativar(senha=SENHA, codigo="000000")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.otp_ativado)

    def test_desativar_com_senha_e_codigo_corretos(self):
        self.desativar(senha=SENHA, codigo=pyotp.TOTP(self.usuario.otp_secret).now())
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.otp_ativado)
        self.assertIsNone(self.usuario.otp_secret)

    # O segredo TOTP precisa estar criptografado na coluna do banco
    def test_otp_secret_criptografado_no_banco(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT otp_secret FROM usuarios WHERE id = %s", [self.usuario.pk]
            )
            valor_no_banco = cursor.fetchone()[0]
        self.assertNotEqual(valor_no_banco, self.usuario.otp_secret)
        self.assertTrue(valor_no_banco.startswith("gAAAA"))


class RecuperacaoSenhaTest(BaseUsuarioTest):
    def pedir(self, email="user@t.com"):
        return self.client.post(
            reverse("solicitacao_recuperacao_senha_view"), {"email": email}
        )

    def token_do_email(self, indice=-1):
        return re.search(
            r"/senha/redefinir/([^/\s]+)/", mail.outbox[indice].body
        ).group(1)

    def redefinir(self, token, senha):
        return self.client.post(
            reverse("redefinir_senha_view", args=[token]), {"nova_senha": senha}
        )

    # O token vale 1 hora (3600 segundos), e não 3600 horas
    def test_token_expira_em_uma_hora(self):
        self.pedir()
        restante = TokenRecuperacaoSenha.objects.get().expira_em - timezone.now()
        self.assertGreater(restante, datetime.timedelta(minutes=58))
        self.assertLessEqual(restante, datetime.timedelta(hours=1))

    # Email que não existe recebe a mesma resposta, sem token e sem email
    def test_email_inexistente_resposta_generica(self):
        resposta = self.pedir("ninguem@t.com")
        self.assertRedirects(resposta, reverse("login"), fetch_redirect_response=False)
        self.assertEqual(TokenRecuperacaoSenha.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    # Mais de 3 pedidos por hora para o mesmo email não geram novos tokens
    def test_rate_limit_por_email(self):
        for _ in range(5):
            resposta = self.pedir()
            self.assertRedirects(
                resposta, reverse("login"), fetch_redirect_response=False
            )
        self.assertEqual(TokenRecuperacaoSenha.objects.count(), 5)
        # Uma sexta requisição não pode gerar outro token.
        self.pedir()
        self.assertEqual(TokenRecuperacaoSenha.objects.count(), 5)

    def test_senha_fraca_e_recusada(self):
        self.pedir()
        token = self.token_do_email()
        self.redefinir(token, "123")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(SENHA))
        self.assertIsNone(TokenRecuperacaoSenha.objects.get().usado_em)

    def test_senha_forte_e_aceita_e_log_de_sucesso(self):
        self.pedir()
        self.redefinir(self.token_do_email(), "NovaSenha@98765")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("NovaSenha@98765"))
        self.assertTrue(LogRecuperacaoSenha.objects.filter(evento="SUCESSO").exists())

    def test_link_nao_pode_ser_reutilizado(self):
        self.pedir()
        token = self.token_do_email()
        self.redefinir(token, "NovaSenha@98765")
        self.redefinir(token, "OutraSenha@11111")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("NovaSenha@98765"))

    # Ao trocar a senha, os outros links pedidos antes deixam de valer
    def test_outros_tokens_pendentes_sao_invalidados(self):
        self.pedir()
        self.pedir()
        self.redefinir(self.token_do_email(-1), "NovaSenha@98765")
        self.assertEqual(
            TokenRecuperacaoSenha.objects.filter(usado_em__isnull=True).count(), 0
        )
        self.redefinir(self.token_do_email(0), "Invasor@99999")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("NovaSenha@98765"))

    def test_token_expirado_e_recusado_e_registrado(self):
        token = "token-de-teste"
        TokenRecuperacaoSenha.objects.create(
            usuario=self.usuario,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expira_em=timezone.now() - datetime.timedelta(minutes=1),
        )
        self.redefinir(token, "NovaSenha@98765")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(SENHA))
        self.assertTrue(
            LogRecuperacaoSenha.objects.filter(evento="FALHA_TOKEN_EXPIRADO").exists()
        )


class LogoutTest(BaseUsuarioTest):
    def test_logout_por_get_nao_e_permitido(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse("logout"))
        self.assertEqual(resposta.status_code, 405)
        self.assertTrue(self.logado())

    def test_logout_por_post_encerra_a_sessao(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse("logout"))
        self.assertFalse(self.logado())


class LogsSomenteLeituraTest(BaseUsuarioTest):
    # Nem o superusuário consegue apagar, editar ou criar logs pelo admin
    def test_admin_nao_altera_logs(self):
        admin = Usuario.objects.create_superuser(
            email="root@t.com", password=SENHA, nome="Root"
        )
        log = LogAcesso.objects.create(usuario=self.usuario, evento="LOGIN_FALHA")
        self.client.force_login(admin)
        for caminho in [
            f"/admin/usuarios/logacesso/{log.pk}/delete/",
            f"/admin/usuarios/logacesso/{log.pk}/change/",
            "/admin/usuarios/logacesso/add/",
        ]:
            resposta = self.client.post(
                caminho, {"evento": "LOGIN_SUCESSO", "post": "yes"}
            )
            # O acesso sem TOTP é barrado antes de chegar à alteração do log.
            self.assertEqual(resposta.status_code, 302, caminho)
        self.assertEqual(LogAcesso.objects.get().evento, "LOGIN_FALHA")


class TermosTest(BaseUsuarioTest):
    def test_pagina_tem_formulario_com_csrf(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse("termos_view"))
        self.assertContains(resposta, '<form method="POST"')
        self.assertContains(resposta, "csrfmiddlewaretoken")

    # Aceitar e depois revogar gera duas linhas, sem apagar o histórico
    def test_aceite_e_revogacao_mantem_historico(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse("termos_view"), {"USO_IMAGEM": "on"})
        self.client.post(reverse("termos_view"), {})
        historico = list(
            ConsentimentoUsuario.objects.filter(tipo="USO_IMAGEM")
            .order_by("pk")
            .values_list("aceito", flat=True)
        )
        self.assertEqual(historico, [True, False])


class SegurancaComplementarTest(BaseUsuarioTest):
    # Testa a ativação que antes ficava em um bloco inalcançável.
    def test_ativacao_do_2fa_funciona(self):
        self.client.force_login(self.usuario)
        self.client.get(reverse('2fa_configurar'))
        self.usuario.refresh_from_db()
        codigo = pyotp.TOTP(self.usuario.otp_secret).now()
        self.client.post(reverse('2fa_configurar'), {'acao': 'ativar', 'codigo': codigo})
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.otp_ativado)
        self.assertTrue(LogAcesso.objects.filter(evento='2FA_ATIVADO').exists())

    # Staff autenticado somente com senha não pode visualizar o admin.
    def test_admin_exige_2fa_confirmado(self):
        staff = Usuario.objects.create_superuser(email='staff@t.com', password=SENHA, nome='Staff')
        self.client.force_login(staff)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.post('/admin/login/', {'username': staff.email, 'password': SENHA}).status_code, 302)
        staff.otp_ativado = True
        staff.otp_secret = pyotp.random_base32()
        staff.save()
        sessao = self.client.session
        sessao['2fa_verificado'] = staff.pk
        sessao.save()
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    # Uma pessoa que não conhece a turma não pode consultar atividades de terceiros.
    def test_login_excluido_impede_autenticacao(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse('excluir_dados_view'), {'senha': SENHA, 'confirmar': 'on'})
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)
        self.assertEqual(self.usuario.nome, 'Conta desidentificada')
        self.assertFalse(self.usuario.has_usable_password())


class ConsentimentoCriancaTest(BaseUsuarioTest):
    def test_crianca_nao_aceita_sem_responsavel(self):
        import datetime as dt
        from .models import Aluno, Responsavel, AlunoResponsavel
        from django.utils import timezone as tz
        crianca = Aluno.objects.create(
            usuario=self.usuario, matricula='CRI-01',
            data_nascimento=tz.localdate() - dt.timedelta(days=365 * 8)
        )
        self.client.force_login(self.usuario)
        self.client.post(reverse('termos_view'), {'USO_IMAGEM': 'on'})
        self.assertFalse(ConsentimentoUsuario.objects.filter(usuario=self.usuario, aceito=True).exists())

        responsavel_usuario = Usuario.objects.create_user(
            email='responsavel-test@teste.local', password=SENHA,
            nome='Responsável Teste', perfil='RESP'
        )
        responsavel = Responsavel.objects.create(usuario=responsavel_usuario)
        AlunoResponsavel.objects.create(aluno=crianca, responsavel=responsavel)
        self.client.force_login(responsavel_usuario)
        self.client.post(reverse('termos_view'), {'aluno_representado': crianca.pk, 'USO_IMAGEM': 'on'})
        self.assertTrue(ConsentimentoUsuario.objects.filter(
            usuario=responsavel_usuario, aluno_representado=crianca,
            tipo='USO_IMAGEM', aceito=True
        ).exists())

    def test_responsavel_nao_concede_consentimento_para_aluno_alheio(self):
        import datetime as dt
        from .models import Aluno, Responsavel
        from django.utils import timezone as tz
        aluno = Aluno.objects.create(
            usuario=self.usuario, matricula='CRI-02',
            data_nascimento=tz.localdate() - dt.timedelta(days=365 * 8)
        )
        outro = Usuario.objects.create_user(email='resp2@teste.local', password=SENHA, nome='Responsável', perfil='RESP')
        Responsavel.objects.create(usuario=outro)
        self.client.force_login(outro)
        self.client.post(reverse('termos_view'), {'aluno_representado': aluno.pk, 'USO_IMAGEM': 'on'})
        self.assertFalse(ConsentimentoUsuario.objects.filter(aluno_representado=aluno).exists())
