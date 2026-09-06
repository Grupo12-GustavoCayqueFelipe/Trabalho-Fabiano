# Documentação Técnica — Autenticação e Gestão de Credenciais

## 1. Modelagem de identidade e controle de acesso
### 1.1 Usuário customizado
O sistema ao invés de usar o username ele usa o email para login. Para isso o model Usuario usa o AbstractUser do Django e removemos o campo username nativo, deixando o email como campo único e definido no USERNAME-FIELD.
A criação de usuários passa pelo UsuarioManager, que normaliza o email e aplica set_password() em todo create_user e create_superuser, para garantir que nenhum usuário e superusuário seja salvo com senha em texto puro.

### 1.2 Perfis
O Campo perfil define o papel do usuário no sistema, com as opções fixas: ADMIN, PROF, ALUNO, RESP. Esse campo que decide qual template é renderizado no dashboard após o login e no futuro define todas as permissões e areas extras de cada perfil.

### 1.3 Dados por perfil em tabelas separadas
Ao invés de colocar todos os campos específicos de aluno, professor e responsável dentro da tabela de usuários cada perfil tem sua própria tabela ligada por OneToOneField a Usuario:
- Aluno: matrícula, data de nascimento, telefone e endereço.
- Professor: formação, telefone, especialidade.
- Responsável: telefone, parentesco principal

O vínculo dentre aluno e responsável usa tabela associativa própria, AlunoResponsavel que é ManyToManyField com through, que permite um aluno ter mais de um responsável e um responsável com mais de um aluno cadastrado.

## 2. Segurança
### 2.1 Senhas
O Hash da senha é feito pelo próprio Django, o PBKDF2 por padrão, via set_password().
Além disso, o AUTH_PASSWORD_VALIDATORS está configurado no settings.py com os quatro validadores nativos do Django.

### 2.2 CSRF e acesso autenticado
CrsfViewMiddleware está ativo em MIDDLEWARE, e os formulários de login usam {% csrf_token %}. As views que dependem de sessão ativa verificam request.user.is_authenticated, ou usam o decorador @login_required, e redirecionam para login caso contrário.

## 3. Banco de dados e armazenamento
### 3.1 PostgresSQL via Supabase
A conexão com o banco é lida da variável DATABASE_URL, com ssl_require=True, ou seja a conexão é recusada se não for criptografada. Permitindo trocar entre Postgres local e Supabase sem mudar código, só mudando a variável de ambiente.

## 4. Fluxo de autentificação
1. Usuário acessa a pagina principal e envia email e senha pelo formulário de Templates/usuarios/index.html.
2. login_view chama authenticate (request, email=email, password=senha).
3. Se for válido, login (request, usuario) cria a sessão e redireciona para /dashboard/
4. Se for inválido, exibe mensagem genérica de erro, "Email ou senha inválidos.", sem indicar se o email existe.
5. dashboard_view bloqueia acesso de quem não está autentificado e escolhe o template conforme o "perfil" do usuário logado.
6. logout_view que é protegida por @login_required, encerra a sessão e volta para o login.

## 5. Organização no repositório
- apps/usuarios/: models, Usuario, Aluno, Professor, Responsavel e AlunoResponsavel, UsuarioManager e as views de login, dashboard e logout.
- core/settings.py: carrega .env, define AUTH_USER_MODEL, AUTH_PASSWORD_VALIDATORS, configuração de banco e storage.
- Templates/usuarios/: telas de login e dashboard.
- .env e .env.example: variáveis de ambiente fora do versionamento.

## 6. Autenticação de dois fatores (2FA)
### 6.1 Implementação e campos do usuário
Implementado com o padrão TOTP utilizando a biblioteca pyotp, sendo compatível com aplicativos como Microsoft Authenticator e Google Authenticator. Para isso, o model Usuario recebeu dois novos campos: otp_secret, que armazena a chave secreta de validação, e otp_ativado, um boolean que indica se a proteção extra está ligada.

### 6.2 Configuração segura
Na rota /2fa/configurar/, o sistema gera a chave secreta e exibe um QR Code gerado por meio da biblioteca qrcode. O sistema só altera o otp_ativado para True no banco de dados após o usuário confirmar a ativação digitando um código válido gerado pelo seu aplicativo. Isso evita que o 2FA fique ativado acidentalmente sem que o usuário tenha configurado o app com sucesso.

### 6.3 Interceptação no fluxo de login
O fluxo tradicional de entrada foi adaptado. Após o authenticate() confirmar que o email e a senha estão corretos, o sistema verifica o status do 2FA do usuário:

- Se otp_ativado for False: O sistema chama o login(request, usuario) normalmente e redireciona para o dashboard.

- Se otp_ativado for True: O login() não é chamado. O sistema salva apenas o ID do usuário em uma variável de sessão temporária (pre_2fa_user_id) e redireciona para /2fa/verificar/.

Na etapa de verificação, somente após o código de 6 dígitos ser validado por meio de pyotp.TOTP(secret).verify(codigo) é que o login() é executado de fato e a sessão autenticada é criada. Isso garante que o conhecimento isolado da senha seja insuficiente para acessar contas com a restrição ativada.

## 7. Política de sessão e bloqueio de conta
### 7.1 Tentativas e bloqueio por conta
Além do rate limiting por IP, o model Usuario recebeu três campos novos: tentativas_login, que conta quantas vezes seguidas a senha foi digitada errada, ultima_tentativa_falha, que guarda quando foi a última tentativa errada, e bloqueado_ate, que guarda até quando a conta fica bloqueada.
Na login_view, antes de chamar authenticate(), o sistema busca o usuário pelo email e confere se bloqueado_ate ainda está no futuro. Se estiver, a tentativa é barrada e uma mensagem de bloqueio é exibida sem nem chegar a validar a senha.
Quando a senha está errada, tentativas_login é incrementado. Ao atingir o limite de 5 tentativas, bloqueado_ate recebe a data e hora atual mais 15 minutos, bloqueando a conta independente do IP de onde vem a tentativa.
Quando o login é bem sucedido, tentativas_login e bloqueado_ate são zerados, liberando o histórico de tentativas erradas anteriores.

### 7.2 Política de sessão
O settings.py define SESSION_COOKIE_AGE = 1800, ou seja a sessão expira depois de 30 minutos. Com SESSION_SAVE_EVERY_REQUEST = True, esse tempo é renovado a cada requisição, então os 30 minutos contam a partir da última ação do usuário, não do login.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True também encerra a sessão quando o navegador é fechado, e SESSION_COOKIE_HTTPONLY = True impede que o cookie de sessão seja acessado via JavaScript, reduzindo o risco de roubo de sessão por ataques XSS.

## 8. Recuperação de Senha
### 8.1 Geração e validação do token
Quando o usuário solicita a recuperação de senha em /senha/recuperar/, o sistema verifica se o email existe na base. Em caso positivo, gera um token aleatório de 32 bytes usando secrets.token_urlsafe(), a mesma biblioteca recomendada pela documentação oficial do Python para geração de valores criptograficamente seguros. Apenas o hash SHA-256 do token é salvo no banco, no model TokenRecuperacaoSenha, nunca o valor original sendo o token em texto puro existe só no momento da geração, dentro do link enviado por email.
O token expira 1 hora após a criação (campo expira_em), e é marcado como usado (campo usado_em) assim que a senha é redefinida com sucesso, impedindo reuso do mesmo link.
A resposta ao usuário é sempre a mesma mensagem genérica, independente do email existir ou não na base, evitando que a funcionalidade seja usada para descobrir quais emails estão cadastrados no sistema.

### 8.2 Envio do email
O envio usa a função send_mail nativa do Django. Em ambiente de desenvolvimento, o EMAIL_BACKEND está configurado como console, que imprime o conteúdo do email no terminal em vez de enviar de verdade, facilitando os testes sem depender de um servidor SMTP real.

### 8.3 Registro e auditoria (2.6 e 2.7)
Cada etapa do processo é registrada na tabela LogRecuperacaoSenha através da função registrar_log_recuperacao_senha: a solicitação inicial (SOLICITACAO), o sucesso da troca de senha (SUCESSO), e as duas formas de falha (FALHA_TOKEN_EXPIRADO e FALHA_TOKEN_INVALIDO), cada uma com o IP de origem, hash do token envolvido e data/hora. Os logs ficam marcados como somente leitura no Django Admin, impedindo alteração posterior do histórico.