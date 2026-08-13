# EduControll
 
Sistema web para escolas e cursos acompanharem frequência, desempenho, atividades e comunicação com alunos e responsáveis.

## Arquitetura

- **Padrão:** Monólito Modular sobre arquitetura MTV (Model–Template–View) do Django.
- **Isolamento de Módulos:** Aplicações separadas dentro da pasta `apps/` (`usuarios`, `academico`, `frequencia`, `avaliacoes`, `atividades`, `comunicacao`), garantindo baixo acoplamento e facilidade de manutenção.

## Funcionalidades
 
- Registro de frequência por aula e cálculo automático de presença
- Lançamento de notas, médias e boletim digital
- Criação de atividades, entregas e correções
- Mural de avisos e mensagens para alunos e responsáveis
- Perfis de acesso: administrador, professor, aluno e responsável
 
## Tecnologias
 
- Python 3.14.6
- Django 6.0.x
- PostgreSQL 18.4 / Supabase PostgreSQL 18
- HTML5, CSS moderno e JavaScript ES2025+
 
## Instalação
 
### Clone o repositório:
 
```bash
git clone [https://github.com/gustavoeguchi28-gif/Trabalho-Fabiano.git](https://github.com/gustavoeguchi28-gif/Trabalho-Fabiano.git)
cd Trabalho-Fabiano
 ```
### Crie e ative o ambiente virtual:
python -m venv .venv

#### Linux/macOS
source .venv/bin/activate

#### Windows
.venv\Scripts\activate

### Instale as dependências:
 
pip install -r requirements.txt

### Configure o arquivo .env (utilize o .env.example como base):

SECRET_KEY=sua-chave-secreta
DEBUG=True
DATABASE_URL=postgresql://usuario:senha@host:5432/educontroll
 
### Aplique as migrações e crie o superusuário:
 
python manage.py migrate
python manage.py createsuperuser
 
### Inicie o servidor:
 
python manage.py runserver
 
O sistema ficará disponível em http://127.0.0.1:8000 e o painel administrativo em http://127.0.0.1:8000/admin.
 
## Estrutura
 
```
educontroll/
├── core/                      # Configurações globais do Django (settings, urls, wsgi)
├── apps/                      # Monólito Modular (Módulos isolados de domínio)
│   ├── usuarios/              # Autenticação, Perfis (RBAC) e Vínculos
│   ├── academico/             # Turmas, Disciplinas, Matriculas e Aulas
│   ├── frequencia/            # Chamada diária e regras de % de presença
│   ├── avaliacoes/            # Avaliações, Notas, Cálculo de Média e Boletim
│   ├── atividades/            # Exercícios, Submissões e Correções
│   └── comunicacao/           # Mural de Avisos e Mensagens Diretas
├── static/                    # Arquivos estáticos globais (CSS, JS, Imagens)
├── templates/                 # Templates base e componentes globais
├── media/                     # Uploads de arquivos e anexos de atividades
├── .env.example               # Exemplo de configuração de variáveis de ambiente
├── requirements.txt           # Dependências do projeto com versões travadas
├── README.md                  # Documentação do projeto
└── manage.py
```
 
## Licença
 
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
GitHub - gustavoeguchi28-gif/Trabalho-Fabiano
Contribute to gustavoeguchi28-gif/Trabalho-Fabiano development by creating an account on GitHub.
 
