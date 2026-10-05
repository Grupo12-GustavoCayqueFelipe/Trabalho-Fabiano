# EduControll

Sistema web de gestão escolar desenvolvido em Django, com foco em autenticação segura, conformidade com a LGPD e arquitetura modular.

## 🔗 Acesse sem instalar nada

O projeto está publicado em produção, com HTTPS automático:

**https://educontroll.onrender.com**

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

## Estrutura

educontroll/
├── core/ # Configurações globais do Django (settings, urls, wsgi)
├── apps/
│ ├── usuarios/ # Autenticação, 2FA, recuperação de senha, LGPD, logs, perfis
│ └── academico/ # Turmas, Disciplinas, Matriculas e Aulas
├── static/ # Arquivos estáticos (CSS, JS)
├── Templates/ # Templates HTML
├── Docs/ # Documentação técnica, escopo, evidências, guias
├── .github/workflows/ # Pipeline de CI (testes automatizados)
├── .env.example # Exemplo de variáveis de ambiente
├── requirements.txt
├── Checklist.md # Status detalhado por item de requisito
└── manage.py

## Documentação

- [Documentação Técnica completa](<Docs/Documentacoes_Tecnicas/Documentação Técnica — Autenticação e Gestão de Credenciais.md>)  arquitetura, segurança, LGPD, criptografia, testes e referências
- [Checklist do projeto](Docs/Checklist.md)
- [Evidências de Funcionamento](Docs/Evidencias_de_Funcionamento/)

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
