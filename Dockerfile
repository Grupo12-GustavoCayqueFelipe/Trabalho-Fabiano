# Versão do python do projeto.
FROM python:3.14.6-slim

# Evita a gravação de arquivos .pyc e força o log direto no terminal.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cria e define a pasta de trabalho dentro do container.
WORKDIR /app

# Cria usuário sem privilégios de root para execução segura do container.
RUN groupadd --system appgroup && useradd --system --gid appgroup --create-home appuser

# Copia as dependências e instala.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do código ajustando a propriedade para o usuário não-root.
COPY --chown=appuser:appgroup . /app/

# Executa a aplicação como usuário sem privilégios administrativos.
USER appuser

EXPOSE 8000

# Comando padrão de produção (sobrescrito pelo command do docker-compose em desenvolvimento).
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
