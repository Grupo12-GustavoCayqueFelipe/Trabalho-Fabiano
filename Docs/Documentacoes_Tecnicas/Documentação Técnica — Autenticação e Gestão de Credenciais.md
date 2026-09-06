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
4. Se for inváçido, exibe mensagem genérica de erro, "Email ou senha inválidos.", sem indicar se o email existe.
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