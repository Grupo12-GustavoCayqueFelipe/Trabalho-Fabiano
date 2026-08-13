# EduControll
 
Sistema web para escolas e cursos acompanharem frequência, desempenho, atividades e comunicação com alunos e responsáveis.

Arquitetura

MTV(Model–Template–View)
 
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
 
Clone o repositório:
 
```bash
git clone https://github.com/gustavoeguchi28-gif/Trabalho-Fabiano.git
cd Trabalho-Fabiano
```
 
Crie e ative o ambiente virtual:
 
```bash
python -m venv .venv
source .venv/bin/activate
```
 
No Windows, use `.venv\Scripts\activate`.
 
Instale as dependências:
 
```bash
pip install -r requirements.txt
```
 
Configure o arquivo `.env`:
 
```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
DATABASE_URL=postgresql://usuario:senha@host:5432/educontroll
```
 
Aplique as migrações e crie o superusuário:
 
```bash
python manage.py migrate
python manage.py createsuperuser
```
 
Inicie o servidor:
 
```bash
python manage.py runserver
```
 
O sistema ficará disponível em http://127.0.0.1:8000 e o painel administrativo em http://127.0.0.1:8000/admin.
 
## Estrutura
 
```
EduControll/
├── config/          Configurações do Django
├── apps/            Módulos do sistema
├── static/          CSS, JavaScript e imagens
├── templates/       Arquivos HTML
├── media/           Uploads
├── requirements.txt
└── manage.py
```
 
## Licença
 
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
GitHub - gustavoeguchi28-gif/Trabalho-Fabiano
Contribute to gustavoeguchi28-gif/Trabalho-Fabiano development by creating an account on GitHub.
 
