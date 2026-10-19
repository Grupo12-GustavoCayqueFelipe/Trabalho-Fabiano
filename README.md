# EduControll

Sistema web de gestão escolar desenvolvido em Django, com foco em autenticação segura, conformidade com a LGPD e arquitetura modular.

## 🔗 Acesse sem instalar nada

O projeto está publicado em produção, com HTTPS automático:

**https://educontroll.onrender.com**

### Entrar nos portais

- [Escolha do portal](https://educontroll.onrender.com/) — a página inicial não é um formulário de login.
- [Aluno e responsável](https://educontroll.onrender.com/login/) — formulário acadêmico.
- [Professor e administrador](https://educontroll.onrender.com/funcionarios/login/) — formulário institucional.

Uma página protegida aberta sem sessão envia para a escolha de portal com
`?next=...`. Após entrar pelo portal correspondente (e concluir o 2FA, quando
ativado), o sistema retorna ao **caminho interno solicitado**. A autorização
pela view continua obrigatória; o retorno não libera páginas de outro perfil.

**Atenção ao testar:** não realizar cinco tentativas erradas nem confirmar
exclusão de conta usando os quatro acessos compartilhados para avaliação.
Esses testes devem utilizar contas descartáveis ou o banco SQLite de testes,
pois o bloqueio pode interromper a avaliação e a exclusão desidentifica a conta.
O comando `seed_demonstracao` **não restaura** credenciais de contas excluídas.
Veja o [roteiro de testes seguros](Docs/Roteiro_Testes_Seguros.md).

> ⚠ O plano gratuito do Render "dorme" após 15 minutos sem acesso  o primeiro carregamento após um tempo parado pode levar de 30 a 60 segundos. Dê um refresh e aguarde.

## Funcionalidades

- Autenticação segura com hash PBKDF2, salt automático, 2FA (TOTP) e bloqueio de conta por tentativas
- Política de sessão com expiração automática
- Recuperação de senha por token temporário, com expiração, uso único e log de auditoria
- Auditoria de login, 2FA e tentativas de acesso, com logs protegidos contra alteração
- Conformidade com a LGPD: consulta, exportação e exclusão dos próprios dados; consentimento granular e revogável, com histórico de data e versão
- Criptografia de campos sensíveis (telefone, endereço, data de nascimento) em repouso, via Fernet/AES
- Comunicação em HTTPS obrigatório, com redirecionamento automático
- Módulo acadêmico: cadastro de Turmas, Disciplinas, Matrícula de alunos e Registro de Aulas
- Perfis de acesso: Administrador, Professor, Aluno e Responsável

## Tecnologias

- Python 3.14+
- Django 6.0+
- PostgreSQL 18 (Supabase)
- HTML5, CSS moderno e JavaScript
- django-encrypted-model-fields (Fernet/AES)
- Docker e Docker Compose
- Render.com (deploy e HTTPS)

## Instalação local (alternativa ao site publicado)

Use isso se quiser rodar o projeto na sua própria máquina em vez de acessar o site em produção  por exemplo, para ver o código rodando passo a passo, ou testar o fluxo completo de recuperação de senha por e-mail (que localmente imprime o link no terminal).

### Clone o repositório

```bash
git clone https://github.com/Grupo12-GustavoCayqueFelipe/Trabalho-Fabiano.git
cd Trabalho-Fabiano
```

### Crie e ative o ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS
```

### Instale as dependências

```bash
pip install -r requirements.txt
```

### Configure o arquivo `.env`

Use o `.env.example` como base. Peça as credenciais reais (Supabase, chaves) a um integrante do grupo por um canal privado  **nunca** compartilhe o `.env` em grupos ou lugares públicos.

Gere uma `SECRET_KEY` nova:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

A `FIELD_ENCRYPTION_KEY` (usada para criptografar dados sensíveis) **precisa ser a mesma** usada em produção  não gere uma nova, ou os dados já criptografados no banco ficam inacessíveis.

### Rode as migrations e o servidor

```bash
python manage.py migrate
python manage.py runserver
```

O sistema fica disponível em `http://127.0.0.1:8000`, e o Django Admin em `http://127.0.0.1:8000/admin`.

### Alternativa: rodar via Docker

```bash
docker-compose up --build
```

## Estrutura do Projeto

```text
educontroll/
│
├── core/                          # Configurações centrais do Django
│   ├── settings.py                # Configurações de produção e desenvolvimento
│   ├── settings_test.py           # Configurações isoladas para testes
│   ├── urls.py                    # Rotas principais
│   ├── middleware.py              # Middlewares de segurança e autenticação
│   ├── admin_site.py              # Controle de acesso ao Django Admin
│   ├── admin_auditoria.py         # Auditoria das operações administrativas
│   ├── apps.py                    # Configuração do Django Admin
│   ├── asgi.py                    # Interface ASGI
│   └── wsgi.py                    # Interface WSGI
│
├── apps/                          # Módulos do sistema
│   ├── usuarios/                  # Autenticação, 2FA, LGPD, perfis e auditoria
│   ├── academico/                 # Turmas, disciplinas, matrículas e aulas
│   ├── atividades/                # Atividades, entregas e correções
│   ├── avaliacoes/                # Avaliações, notas e históricos
│   ├── frequencia/                # Presenças, faltas e justificativas
│   └── comunicacao/               # Avisos e mensagens institucionais
│
├── Templates/                     # Interfaces HTML organizadas por módulo
│   ├── html/
│   │   ├── academico/             # Gestão acadêmica
│   │   ├── alunos/                # Portal do aluno
│   │   ├── atividades/            # Telas de atividades
│   │   ├── avaliacoes/            # Boletim e notas
│   │   ├── componentes/           # Componentes HTML compartilhados
│   │   ├── comunicacao/           # Avisos e mensagens
│   │   ├── frequencia/            # Controle de frequência
│   │   ├── login/                 # Formulários de autenticação
│   │   ├── meus_dados/            # Dados pessoais e direitos LGPD
│   │   ├── painel/                # Dashboards administrativos e docentes
│   │   ├── responsaveis/          # Portal do responsável
│   │   ├── senha/                 # Recuperação e alteração de senha
│   │   └── usuarios/              # Gestão e consulta de usuários
│   └── usuarios/                  # Página inicial e entrada dos portais
│
├── static/                        # Arquivos estáticos
│   ├── css/                       # Estilos dos portais e módulos
│   └── js/                        # Scripts JavaScript
│
├── scripts/                       # Diagnósticos e verificações técnicas
│   ├── diagnosticar_totp_legado.py
│   ├── testar_migracoes_dados.py
│   ├── verificar_criptografia_legada.py
│   └── verificar_integracao_estatica.py
│
├── Docs/                          # Documentação do projeto
│   ├── Documentacoes_Tecnicas/    # Documentação técnica detalhada
│   ├── Evidencias_de_Funcionamento/
│   ├── Checklist.md               # Checklist dos requisitos
│   ├── Escopo.md                   # Escopo do sistema
│   ├── Mapa_Dados_LGPD.md          # Mapeamento e proteção de dados
│   └── Requisito.md                # Requisitos do projeto
│
├── supabase/                      # Diretório reservado à integração Supabase
├── .vscode/                       # Configurações do VS Code
├── .dockerignore                  # Exclusões do contexto Docker
├── .env.example                   # Exemplo das variáveis de ambiente
├── .gitignore                     # Arquivos ignorados pelo Git
├── Dockerfile                     # Imagem Docker da aplicação
├── docker-compose.yml             # Orquestração dos serviços locais
├── requirements.txt               # Dependências Python
├── README.md                      # Documentação principal
└── manage.py                      # Gerenciamento do Django
```

### Organização dos módulos

Cada aplicação em `apps/` possui seus próprios arquivos de modelos, views, administração e testes, além das migrations necessárias ao banco de dados.

O sistema utiliza **Django 6.0**, **PostgreSQL via Supabase** e **Render.com** para hospedagem, com autenticação por sessão, 2FA (TOTP), controle de acesso por perfil, criptografia de dados pessoais e registros de auditoria.

Os quatro perfis disponíveis são: **Administrador, Professor, Aluno e Responsável**.

## Documentação

- [Documentação Técnica completa](<Docs/Documentacoes_Tecnicas/Documentação Técnica — Autenticação e Gestão de Credenciais.md>)  arquitetura, segurança, LGPD, criptografia, testes e referências
- [Checklist do projeto](Docs/Checklist.md)
- [Evidências de Funcionamento](Docs/Evidencias_de_Funcionamento/)

### Publicações Científicas — UMC Summit 2026

O EduControll foi desenvolvido como Projeto Integrador do curso de Engenharia de Software da Universidade de Mogi das Cruzes (UMC).

Os materiais científicos apresentam o sistema, sua arquitetura, funcionalidades, integração dos módulos e os mecanismos de proteção de dados adotados.

- [Pôster Científico — EduControll](Docs/Poster_e_Resumo/Poster_EduControll_UMC_Summit.pdf)
- [Resumo Simples — EduControll](Docs/Poster_e_Resumo/Resumo_Simples_EduControll_UMC_Summit.pdf)

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.


## Validação da entrega (outubro de 2026)

As páginas de aluno e responsável usam dados de matrículas e vínculos autorizados;
quando não houver dados, exibem estados vazios em vez de indicadores fictícios.
O acesso inicial separa os portais acadêmico e institucional, mantendo POST legado.
Erros HTTP 500 são registrados em `django.request` no console do Render.

Antes de publicar, execute em ambiente local com banco SQLite de testes:

```powershell
python manage.py check --settings=core.settings_test
python manage.py test --settings=core.settings_test --noinput
python manage.py makemigrations --check --dry-run --settings=core.settings_test
```

**Importante:** passar nos testes SQLite não comprova que a base PostgreSQL do
Render tem todas as migrações aplicadas. Em caso de HTTP 500, consultar os logs
do Render e validar o esquema com segurança, sem apagar nem recriar tabelas.
